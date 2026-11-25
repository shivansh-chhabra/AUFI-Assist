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


def test_full_flow_stops_on_confidence_then_rag(mp):
    FakeScorer().install(mp); fake_rag(mp); fake_agent(mp)
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
    # uncited and badly-cited sections were removed, cited ones kept
    secs = r.explanation[0].sections
    assert [x.content_type for x in secs] == ["clinical_features", "confirmatory_tests"]
    assert r.evidence.sources[0].id == 1
    # retrieved sources first, then the protocol's; the tests section cites only the protocol's
    n_rag = sum(1 for x in r.evidence.sources if x.id <= 2)
    assert n_rag == 2 and r.evidence.source_count > 2
    tests = secs[-1]
    assert tests.citations and min(tests.citations) > 2
    assert r.evidence.sources[0].disease == "Dengue"
    assert any("without a valid citation" in x for x in r.steps)
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
    assert s.asked[0] == {"feature": pending, "text": "Question 0?", "answer": "yes"}
    assert r2.question.feature == "f1"


def test_rag_down_keeps_scoring_result(mp):
    FakeScorer().install(mp); fake_agent(mp)
    mp.setattr(retriever, "retrieve", lambda sl, q: (_ for _ in ()).throw(RuntimeError("chroma down")))
    s = Session(id="t"); r = drive(s, "fever")
    while r.question:
        r = answer_yes(s, r)
    assert s.finished and r.candidates[0].shortlisted
    # the fixed protocol still supplies the tests, each with citations that resolve to listed sources
    assert [x.content_type for x in r.explanation[0].sections] == ["confirmatory_tests"]
    ids = {x.id for x in r.evidence.sources}
    assert r.explanation[0].sections[0].citations and set(r.explanation[0].sections[0].citations) <= ids
    assert "couldn't search" in r.reply and "test protocol" in r.reply


def test_stubs_not_installed_gives_clear_message_and_is_retryable(mp):
    mp.setattr(config, "SCORING_TABLE", config.BACKEND_DIR / "data" / "no_such_table.csv")
    mp.setattr(scorer, "_table", None)
    s = Session(id="t")
    r = drive(s, "fever")                      # the real scorer has no table, so it raises NotImplementedError
    assert "not installed yet" in r.reply and "scoring table" in r.reply and not s.started
    FakeScorer().install(mp); fake_rag(mp); fake_agent(mp)
    r = drive(s, "fever")                      # same session, module now present
    assert s.started and r.question


def test_finished_case_is_read_only(mp):
    FakeScorer(step=0.5).install(mp); fake_rag(mp); fake_agent(mp)
    s = Session(id="t"); r = drive(s, "fever")
    while r.question:
        r = answer_yes(s, r)
    again = drive(s, "hello?")
    assert "complete" in again.reply and again.question is None


def test_pdf_builds(mp):
    FakeScorer(step=0.5).install(mp); fake_rag(mp); fake_agent(mp)
    s = Session(id="t"); r = drive(s, "fever ≥ 3 days, µ")
    while r.question:
        r = answer_yes(s, r)
    pdf = build_pdf(s)
    assert pdf.startswith(b"%PDF") and len(pdf) > 2000
    open("/tmp/aufi_test_report.pdf", "wb").write(pdf)


def test_wire_format_is_camel_case(mp):
    FakeScorer().install(mp)
    s = Session(id="t"); w = drive(s, "fever").wire()
    assert {"reply", "steps", "candidates", "question", "progress"} <= w.keys()
    assert w["progress"]["maxQuestions"] == 12 and "questionsAsked" in w["progress"]
    assert "informationGain" in w["question"] and w["explanation"] is None
