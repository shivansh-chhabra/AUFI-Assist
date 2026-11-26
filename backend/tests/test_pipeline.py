"""Run:  pytest -q      (uses fake scorer/RAG/agent, so it works before your friend's code lands)"""
import pytest

from app import config, pipeline
from app.agent import explainer
from app.rag import retriever
from app.report import build_pdf
from app.schemas import AnswerPayload
from app.scoring import scorer
from app.session import Session


class FakeScorer:
    """Each 'yes' moves dengue up. Probability of dengue = 0.2 + 0.2 * yes_count."""
    def __init__(self, step=0.2, questions=100):
        self.step, self.questions = step, questions

    def install(self, mp):
        mp.setattr(scorer, "start_case", lambda text: {"yes": 0, "asked": 0})
        def apply(state, feature, value):
            state["asked"] += 1
            state["yes"] += value == "yes"
        mp.setattr(scorer, "apply_answer", apply)
        def post(state):
            d = min(0.95, 0.2 + self.step * state["yes"])
            rest = (1 - d) / 10
            return {"dengue": d, "chikungunya": rest * 3, "malaria": rest * 2,
                    **{c: rest for c in ["typhoid", "scrub_typhus", "leptospirosis", "viral_ili",
                                         "hepatitis_a_e", "occult_bacteraemia", "rheumatic_fever", "tb"]}}
        mp.setattr(scorer, "get_posterior", post)
        mp.setattr(scorer, "choose_next_question",
                   lambda st: None if st["asked"] >= self.questions else
                   {"feature": f"f{st['asked']}", "text": f"Question {st['asked']}?", "information_gain": 0.5})


def fake_rag(mp, passages=None):
    passages = passages if passages is not None else [
        {"text": "fever for 2-7 days", "file": "d.pdf", "location": "p. 3", "body": "ICMR",
         "disease": "dengue", "content_type": "clinical_features", "relevance": 0.9},
        {"text": "NS1 antigen in first 5 days", "file": "d.pdf", "location": "p. 9", "body": "ICMR",
         "disease": "dengue", "content_type": "confirmatory_tests"},
    ]
    mp.setattr(retriever, "retrieve", lambda sl, q: {"passages": passages, "documents_in_index": 14})


def fake_agent(mp, sections=None):
    sections = sections or [
        {"content_type": "clinical_features", "text": "Fever with headache.", "citations": [1]},
        {"content_type": "confirmatory_tests", "text": "NS1 or IgM.", "citations": [2]},
        {"content_type": "treatment", "text": "Invented, uncited claim.", "citations": []},
        {"content_type": "treatment", "text": "Bad citation id.", "citations": [99]},
    ]
    mp.setattr(explainer, "explain", lambda sl, f, t, p: [{"disease_id": "dengue", "sections": sections}])


def drive(s, message, answer=None):
    steps, final = [], None
    for kind, payload in pipeline.run_turn(s, message, answer):
        steps.append(payload) if kind == "step" else None
        if kind == "final":
            final = payload
    return final


def answer_yes(s, resp):
    q = resp.question
    return drive(s, "Yes", AnswerPayload(feature=q.feature, value="yes"))


@pytest.fixture
def mp(monkeypatch):
    return monkeypatch


def test_full_flow_stops_on_confidence_then_fixed_summaries(mp):
    FakeScorer().install(mp)
    # the final stage no longer retrieves or calls the LLM: make either one blow up if it is touched
    boom = lambda *a, **k: (_ for _ in ()).throw(AssertionError("RAG/LLM must not run for the summary"))
    mp.setattr(retriever, "retrieve", boom); mp.setattr(explainer, "explain", boom)
    s = Session(id="t")
    r = drive(s, "fever for 3 days")
    assert r.question and r.progress.questions_asked == 0 and r.progress.max_questions == 12
    for _ in range(10):
        r = answer_yes(s, r)
        if r.progress.stop_reason:
            break
    assert r.progress.stop_reason == "shortlist"
    assert r.progress.questions_asked >= config.MIN_QUESTIONS
    assert r.question is None
    assert [c.shortlisted for c in r.candidates[:3]] == [True, True, True]
    assert r.candidates[0].id == "dengue"
    # every condition has its fixed summary, most likely first
    assert len(r.explanation) == 11 and r.explanation[0].disease_id == "dengue"
    assert all(e.info and e.info.summary and e.info.preventive_methods for e in r.explanation)
    assert "Aedes" in r.explanation[0].info.transmission
    # only the shortlisted conditions carry tests, each cited to the protocol's sources
    with_tests = [e for e in r.explanation if e.sections]
    assert [e.disease_id for e in with_tests] == s.shortlist
    ids = {x.id for x in r.evidence.sources}
    for e in with_tests:
        assert [x.content_type for x in e.sections] == ["confirmatory_tests"]
        assert e.sections[0].citations and set(e.sections[0].citations) <= ids
    assert r.evidence.sources[0].disease == "Dengue" and r.evidence.chunk_count == 0
    assert "summary of each condition" in r.reply and "test protocol" in r.reply
    assert s.finished


def test_question_limit_at_12(mp):
    FakeScorer(step=0.0).install(mp); fake_rag(mp); fake_agent(mp)   # confidence never rises
    s = Session(id="t"); r = drive(s, "fever")
    n = 0
    while r.question:
        r = answer_yes(s, r); n += 1
    assert n == 12 and r.progress.stop_reason == "question_limit" and r.progress.questions_asked == 12


def test_no_discriminating_question(mp):
    FakeScorer(step=0.0, questions=2).install(mp); fake_rag(mp); fake_agent(mp)
    s = Session(id="t"); r = drive(s, "fever")
    while r.question:
        r = answer_yes(s, r)
    assert r.progress.stop_reason == "no_discriminating_question"


def test_typed_answers_and_unparseable(mp):
    FakeScorer().install(mp); fake_rag(mp); fake_agent(mp)
    s = Session(id="t"); r = drive(s, "fever"); first = r.question.feature
    r2 = drive(s, "hmm what")
    assert r2.question.feature == first and len(s.asked) == 0           # re-asked, nothing recorded
    r3 = drive(s, "not sure")
    assert s.asked[0]["answer"] == "unsure" and r3.question.feature != first
    assert pipeline.parse_answer_text("Yes, since Monday") == "yes"
    assert pipeline.parse_answer_text("No") == "no"


def test_stale_button_payload_falls_back_to_the_typed_text(mp):
    FakeScorer().install(mp); fake_rag(mp); fake_agent(mp)
    s = Session(id="t"); r = drive(s, "fever")
    pending = r.question.feature
    r2 = drive(s, "Yes", AnswerPayload(feature="some_old_feature", value="no"))
    # the payload's feature doesn't match the pending question, so it is ignored (not recorded as "no")
    assert {k: v for k, v in s.asked[0].items() if k != "q"} == {"feature": pending, "text": "Question 0?", "answer": "yes"}
    assert r2.question.feature == "f1"


def test_summaries_missing_keeps_scoring_result_and_tests(mp):
    FakeScorer().install(mp)
    mp.setattr(pipeline.summaries, "get", lambda cid: (_ for _ in ()).throw(ValueError("bad json")))
    s = Session(id="t"); r = drive(s, "fever")
    while r.question:
        r = answer_yes(s, r)
    assert s.finished and r.candidates[0].shortlisted
    # the fixed protocol still supplies the tests, each with citations that resolve to listed sources
    assert [e.disease_id for e in r.explanation] == s.shortlist
    assert all(e.info is None for e in r.explanation)
    ids = {x.id for x in r.evidence.sources}
    assert r.explanation[0].sections[0].citations and set(r.explanation[0].sections[0].citations) <= ids
    assert "Only the recommended tests" in r.reply


def test_stubs_not_installed_gives_clear_message_and_is_retryable(mp):
    mp.setattr(config, "SCORING_TABLE", config.BACKEND_DIR / "data" / "no_such_table.csv")
    mp.setattr(scorer, "_table", None)
    s = Session(id="t")
    r = drive(s, "fever")                      # the real scorer has no table, so it raises NotImplementedError
    assert "not installed yet" in r.reply and "scoring table" in r.reply and not s.started
    FakeScorer().install(mp); fake_rag(mp); fake_agent(mp)
    r = drive(s, "fever")                      # same session, module now present
    assert s.started and r.question


def finish_case(mp):
    FakeScorer(step=0.5).install(mp); fake_rag(mp); fake_agent(mp)
    s = Session(id="t"); r = drive(s, "fever")
    while r.question:
        r = answer_yes(s, r)
    return s


def fake_qa(mp, passages, blocks, seen=None):
    def ap(question, cid, n=4):
        if seen is not None:
            seen.append((question, cid))
        return [dict(p) for p in passages]
    mp.setattr(pipeline.retriever, "answer_passages", ap)
    mp.setattr(pipeline.explainer, "answer_question", lambda q, name, plist: blocks)


P = [{"text": "Dengue is spread by Aedes mosquitoes.", "file": "dengue.pdf", "location": "p. 2", "title": "Dengue guideline", "body": "MoHFW", "disease": "dengue", "relevance": 0.7},
     {"text": "Rest and plenty of fluids are advised.", "file": "dengue.pdf", "location": "p. 9", "title": "Dengue guideline", "body": "MoHFW", "disease": "dengue", "relevance": 0.6}]


def test_question_after_result_is_answered_from_the_guidelines_with_citations(mp):
    s = finish_case(mp)
    seen = []
    fake_qa(mp, P, [{"text": "It is spread by mosquitoes.", "citations": [2]}], seen)
    r = drive(s, "How does it spread?")
    assert seen and seen[0][1] == s.shortlist[0]                   # defaults to the leading condition
    assert r.question is None and s.finished and r.progress.stop_reason
    assert r.reply.startswith("It is spread by mosquitoes. [1]")   # cited passage 2 is renumbered to 1
    assert [x.id for x in r.evidence.sources] == [1] and r.evidence.sources[0].location == "p. 9"


def test_question_naming_another_condition_uses_that_condition(mp):
    s = finish_case(mp)
    seen = []
    fake_qa(mp, P, [{"text": "x", "citations": [1]}], seen)
    drive(s, "What are the symptoms of malaria?")
    assert seen[0][1] == "malaria"


def test_unanswerable_question_says_so_and_does_not_guess(mp):
    s = finish_case(mp)
    fake_qa(mp, P, [])
    r = drive(s, "Can I drive a car?")
    assert "won't guess" in r.reply and r.evidence is None
    fake_qa(mp, [], [{"text": "x", "citations": [1]}])             # nothing retrieved at all
    assert "won't guess" in drive(s, "Anything?").reply


def test_qa_does_not_disturb_the_stored_result_used_for_the_pdf(mp):
    s = finish_case(mp)
    before = (s.explanation, s.evidence)
    fake_qa(mp, P, [{"text": "x", "citations": [1]}])
    drive(s, "What is it?")
    assert (s.explanation, s.evidence) == before


def test_pdf_builds(mp):
    FakeScorer(step=0.5).install(mp); fake_rag(mp); fake_agent(mp)
    s = Session(id="t"); r = drive(s, "fever ≥ 3 days, µ")
    while r.question:
        r = answer_yes(s, r)
    pdf = build_pdf(s)
    assert pdf.startswith(b"%PDF") and len(pdf) > 2000
    assert any(e["info"] for e in s.explanation)
    open("/tmp/aufi_test_report.pdf", "wb").write(pdf)


def test_wire_format_is_camel_case(mp):
    FakeScorer().install(mp)
    s = Session(id="t"); w = drive(s, "fever").wire()
    assert {"reply", "steps", "candidates", "question", "progress"} <= w.keys()
    assert w["progress"]["maxQuestions"] == 12 and "questionsAsked" in w["progress"]
    assert "informationGain" in w["question"] and w["explanation"] is None


def test_go_back_restores_the_previous_question_and_scores(mp):
    FakeScorer().install(mp); fake_rag(mp); fake_agent(mp)
    s = Session(id="t"); r = drive(s, "fever")
    p0 = {c.id: c.probability for c in r.candidates}
    r = answer_yes(s, r); r = answer_yes(s, r)           # now on f2 after two yes answers
    assert r.question.feature == "f2" and len(s.asked) == 2
    back = pipeline.undo_last(s)
    assert back.question.feature == "f1" and len(s.asked) == 1 and back.progress.questions_asked == 1
    back = pipeline.undo_last(s)
    assert back.question.feature == "f0" and not s.asked
    assert {c.id: round(c.probability, 6) for c in back.candidates} == {k: round(v, 6) for k, v in p0.items()}
    again = pipeline.undo_last(s)                         # nothing left to undo: same question stays
    assert again.question.feature == "f0" and "no earlier answer" in again.reply
    r = drive(s, "No", AnswerPayload(feature="f0", value="no"))   # and the case carries on normally
    assert r.question.feature == "f1"
