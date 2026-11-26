"""The case loop: questionnaire -> stop rule -> fixed summaries + fixed test protocol.

`run_turn()` is a generator of ("step", text) events followed by one ("final", ChatResponse).
The /chat/stream route forwards the events as SSE; /chat just drains it.

This module has no web-framework imports so it can be tested on its own.
"""
import logging
import re
from typing import Any, Iterator, Optional

from . import config, summaries
from .agent import explainer
from .conditions import CONDITIONS, CONTENT_TYPES, condition_name
from .protocols import prescriber
from .rag import retriever
from .schemas import (
    AnswerPayload,
    Candidate,
    CaseProgress,
    ChatResponse,
    DiseaseExplanation,
    DiseaseInfo,
    EvidenceData,
    ExplanationSection,
    FollowUpQuestion,
    Source,
)
from .scoring import scorer
from .session import Session

log = logging.getLogger("aufi.pipeline")

Event = tuple[str, Any]
VALID_VALUES = {"yes", "no", "unsure", "skip"}
ANSWER_LABEL = {"yes": "Yes", "no": "No", "unsure": "Not sure", "skip": "Skipped"}

STOP_TEXT = {
    "shortlist": "The questions have narrowed this down with enough confidence.",
    "question_limit": f"The {config.MAX_QUESTIONS}-question limit was reached.",
    "no_discriminating_question": "No remaining question would help separate the candidates.",
}

# --- typed answers (the UI uses buttons, but the text box stays available) -----------------
_UNSURE = re.compile(r"not\s+sure|unsure|don'?t\s+know|do\s+not\s+know|maybe|can'?t\s+say|idk", re.I)
_SKIP = re.compile(r"^\s*(skip|prefer\s+not|pass)\b", re.I)
_NO = re.compile(r"^\s*(no|n|nope|nah|none|never|absent|not\s+really)\b", re.I)
_YES = re.compile(r"^\s*(yes|y|yeah|yep|yup|sure|true|present|i\s+do|there\s+is)\b", re.I)


def parse_answer_text(text: str) -> Optional[str]:
    for value, rx in (("unsure", _UNSURE), ("skip", _SKIP), ("no", _NO), ("yes", _YES)):
        if rx.search(text):
            return value
    return None


# --- helpers ------------------------------------------------------------------------------
def _normalise(raw: dict[str, float]) -> dict[str, float]:
    p = {k: max(0.0, float(v)) for k, v in raw.items() if k in CONDITIONS}
    total = sum(p.values())
    if total <= 0:
        raise ValueError("scorer returned no usable probabilities")
    return {k: v / total for k, v in p.items()}


def _candidates(s: Session, shortlist: list[str]) -> list[Candidate]:
    rows = sorted(s.posterior.items(), key=lambda kv: kv[1], reverse=True)
    return [
        Candidate(
            id=cid,
            name=condition_name(cid),
            probability=round(p, 4),
            previous=round(s.previous[cid], 4) if cid in s.previous else None,
            shortlisted=cid in shortlist,
        )
        for cid, p in rows
    ]


def _remaining(s: Session) -> int:
    return max(1, sum(1 for p in s.posterior.values() if p >= config.REMAINING_FLOOR))


def _progress(s: Session, remaining: Optional[int] = None) -> CaseProgress:
    return CaseProgress(
        questions_asked=len(s.asked),
        max_questions=config.MAX_QUESTIONS,
        candidates_remaining=remaining if remaining is not None else _remaining(s),
        stop_reason=s.stop_reason,
    )


def _question_model(q: dict) -> FollowUpQuestion:
    if not q.get("feature") or not q.get("text"):
        raise ValueError("scorer question needs 'feature' and 'text'")
    opts = q.get("options")
    if opts:
        bad = [o for o in opts if o.get("value") not in VALID_VALUES]
        if bad:
            raise ValueError(f"scorer option values must be one of {sorted(VALID_VALUES)}")
    return FollowUpQuestion(
        feature=q["feature"],
        text=q["text"],
        options=opts or None,
        information_gain=q.get("information_gain"),
        candidates_separated=q.get("candidates_separated"),
    )


def _fmt_pct(p: float) -> str:
    return "<1%" if 0 < p < 0.01 else f"{round(p * 100)}%"


def _case_query(s: Session) -> str:
    """A compact description of the case for retrieval, built from the answers."""
    yes = [a["text"] for a in s.asked if a["answer"] == "yes"]
    no = [a["text"] for a in s.asked if a["answer"] == "no"]
    parts = [s.initial_text.strip()]
    if yes:
        parts.append("Present: " + "; ".join(yes))
    if no:
        parts.append("Absent: " + "; ".join(no))
    return " ".join(parts)[:1500]


def _response(s: Session, reply: str, steps: list[str], **kw: Any) -> ChatResponse:
    return ChatResponse(reply=reply, steps=steps, **kw)


# --- the turn -----------------------------------------------------------------------------
def run_turn(s: Session, message: str, answer: Optional[AnswerPayload]) -> Iterator[Event]:
    with s.lock:
        s.add_message("user", message)
        try:
            for ev in _turn(s, message, answer):
                if ev[0] == "final":
                    _remember(s, ev[1])
                yield ev
        except NotImplementedError as e:
            log.warning("module not implemented yet: %s", e)
            resp = _error_response(s, f"A required module is not installed yet ({e}).")
            _remember(s, resp)
            yield ("final", resp)
        except Exception:
            log.exception("turn failed")
            resp = _error_response(
                s, "Something went wrong while processing that. Please send your answer again; "
                   "if it keeps happening, start a new case."
            )
            _remember(s, resp)
            yield ("final", resp)


_MENTIONS = {
    "malaria": r"malaria", "dengue": r"dengue", "typhoid": r"typhoid|enteric", "scrub_typhus": r"scrub|murine|rickett",
    "leptospirosis": r"lepto", "chikungunya": r"chikun", "viral_ili": r"influenza|\bflu\b|swine", "hepatitis_a_e": r"hepatitis",
    "occult_bacteraemia": r"bacter(a)?emia|sepsis", "rheumatic_fever": r"rheumatic", "tb": r"\btb\b|tubercul",
}


def _mentioned_condition(text: str) -> Optional[str]:
    for cid, rx in _MENTIONS.items():
        if re.search(rx, text, re.I):
            return cid
    return None


def _answer_followup(s: Session, message: str, note, steps: list) -> Iterator[Event]:
    """After the result: answer a question about the condition from the guideline index, with citations."""
    def done(reply: str, **kw):
        return ("final", _response(s, reply, steps, progress=_progress(s, len(s.shortlist)), **kw))

    cid = _mentioned_condition(message) or (s.shortlist[0] if s.shortlist else None)
    if cid is None:
        yield done("I'm not sure which condition you mean. Please name it, for example \"What causes dengue?\".")
        return
    name = condition_name(cid)
    yield note(f"Looking for an answer about {name} in the guidelines.")
    try:
        passages = retriever.answer_passages(message, cid, n=4)
    except NotImplementedError:
        raise
    except Exception:
        log.exception("answer retrieval failed")
        yield done("I couldn't search the guidelines just now, so I can't answer that. Please try again, or ask your doctor.")
        return
    for i, p in enumerate(passages, start=1):
        p["id"] = i
    blocks = explainer.answer_question(message, name, passages) if passages else []
    if not blocks:
        yield done(f"I couldn't find an answer to that about {name} in the ICMR and MoHFW guidelines I have, "
                   "so I won't guess. Please ask your doctor.")
        return
    used = sorted({c for b in blocks for c in b["citations"]})
    renum = {old: new for new, old in enumerate(used, start=1)}
    sources = _build_sources([passages[old - 1] for old in used])
    reply = "\n\n".join(b["text"] + " " + "".join(f"[{renum[c]}]" for c in b["citations"]) for b in blocks)
    evidence = EvidenceData(source_count=len(sources), chunk_count=len(passages), retrieval_ms=0,
                            documents_in_index=0, sources=sources)
    yield note(f"Answered from {len(sources)} guideline {'passage' if len(sources) == 1 else 'passages'}.")
    yield done(reply, evidence=evidence)


def undo_last(s: Session) -> ChatResponse:
    """Take back the last answer: rebuild the scoring state from the earlier answers and re-ask that question."""
    with s.lock:
        if s.finished or not s.started or not s.asked:
            return _response(
                s, "There is no earlier answer to change.", [],
                candidates=_candidates(s, []) if s.posterior else None,
                question=_question_model(s.pending) if s.pending else None, progress=_progress(s))
        last = s.asked.pop()
        state = scorer.start_case(s.initial_text)
        for a in s.asked:
            scorer.apply_answer(state, a["feature"], a["answer"])
        s.scorer_state = state
        s.pending = last.get("q") or {"feature": last["feature"], "text": last["text"]}
        s.posterior = _normalise(scorer.get_posterior(state))
        s.previous = {}
        return _response(
            s, "No problem. Here is that question again.", [],
            candidates=_candidates(s, []), question=_question_model(s.pending), progress=_progress(s))


def _remember(s: Session, r: ChatResponse) -> None:
    w = r.wire()
    s.add_message(
        "ai", r.reply, steps=w["steps"], candidates=w["candidates"], question=w["question"],
        progress=w["progress"], explanation=w["explanation"], evidence=w["evidence"],
    )


def _error_response(s: Session, text: str) -> ChatResponse:
    return ChatResponse(
        reply=text,
        steps=[],
        candidates=_candidates(s, s.shortlist) if s.posterior else None,
        question=_question_model(s.pending) if s.pending and not s.finished else None,
        progress=_progress(s) if s.started else None,
    )


def _turn(s: Session, message: str, answer: Optional[AnswerPayload]) -> Iterator[Event]:
    steps: list[str] = []

    def note(text: str) -> Event:
        steps.append(text)
        return ("step", text)

    # A finished case is read-only: start a new case for the next patient.
    if s.finished:
        yield from _answer_followup(s, message, note, steps)
        return

    if not s.started:
        # ---- first message: free-text description ----
        text = message.strip()
        if not text:
            yield ("final", _response(s, "Please describe the fever and any other symptoms to begin.", steps))
            return
        yield note("Reading your description.")
        s.initial_text = text
        s.scorer_state = scorer.start_case(text)
        s.started = True
        s.posterior = _normalise(scorer.get_posterior(s.scorer_state))
        yield note("Scored the 11 conditions from your description.")
        lead_in = "Thanks. I'll ask a few short questions to narrow down the likely cause."
    else:
        # ---- a reply to the pending question ----
        pending = s.pending
        if pending is None:
            # An earlier turn failed after recording the answer; just pick the next question again.
            lead_in = "Let's continue. Next question:"
        else:
            if answer and answer.feature == pending["feature"]:
                value = answer.value
            else:
                value = parse_answer_text(message)
            if value is None:
                yield (
                    "final",
                    _response(
                        s, "I didn't catch that. Please choose one of the options for this question.", steps,
                        candidates=_candidates(s, []), question=_question_model(pending), progress=_progress(s),
                    ),
                )
                return
            yield note(f"Recorded your answer: {ANSWER_LABEL[value]}.")
            scorer.apply_answer(s.scorer_state, pending["feature"], value)
            s.asked.append({"feature": pending["feature"], "text": pending["text"], "answer": value, "q": dict(pending)})
            s.pending = None
            s.previous = dict(s.posterior)
            s.posterior = _normalise(scorer.get_posterior(s.scorer_state))
            top_id, top_p = max(s.posterior.items(), key=lambda kv: kv[1])
            yield note(f"Updated probabilities. Leading: {condition_name(top_id)} ({_fmt_pct(top_p)}).")
            lead_in = "Noted. Next question:"

    # ---- stop rule ----
    top_p = max(s.posterior.values())
    asked = len(s.asked)
    stop: Optional[str] = None
    next_q: Optional[dict] = None
    if asked >= config.MAX_QUESTIONS:
        stop = "question_limit"
    elif asked >= config.MIN_QUESTIONS and top_p >= config.CONFIDENCE_THRESHOLD:
        stop = "shortlist"
    else:
        yield note("Choosing the most informative next question.")
        next_q = scorer.choose_next_question(s.scorer_state)
        if next_q is None:
            stop = "no_discriminating_question"

    if stop is None and next_q is not None:
        qm = _question_model(next_q)  # validate before storing
        s.pending = next_q
        yield (
            "final",
            _response(s, lead_in, steps, candidates=_candidates(s, []), question=qm, progress=_progress(s)),
        )
        return

    # ---- questionnaire finished: RAG + summary ----
    s.stop_reason = stop
    ranked = sorted(s.posterior.items(), key=lambda kv: kv[1], reverse=True)
    s.shortlist = [cid for cid, _ in ranked[: config.SHORTLIST_SIZE]]
    yield note(f"Questions finished. Shortlist: {', '.join(condition_name(c) for c in s.shortlist)}.")

    # fixed test protocol (ICMR/MoHFW document; offline, no retrieval, no LLM)
    protocol = None
    if config.TESTS_FROM_PROTOCOL:
        try:
            protocol = prescriber.prescribe(
                s.posterior, s.shortlist, day=prescriber.parse_day_of_fever(s.initial_text))
            if protocol["close"]:
                yield note("The leading conditions are close; adding the tests that tell them apart.")
            else:
                yield note("Added the recommended tests from the ICMR/MoHFW test protocol.")
        except Exception:
            log.exception("test protocol failed")

    # fixed summaries (hand-written, read from disk: instant, no retrieval, no LLM)
    explanation: Optional[list[DiseaseExplanation]] = None
    evidence: Optional[EvidenceData] = None
    try:
        explanation = _summaries(s)
        yield note("Added the summary of each condition.")
    except Exception:
        log.exception("condition summaries failed")
        yield note("Could not load the condition summaries; showing the scoring result only.")

    if protocol and protocol["by_condition"]:
        try:
            explanation, evidence = _merge_protocol(explanation, evidence, protocol, s)
        except Exception:
            log.exception("merging test protocol failed")

    s.explanation = [e.model_dump(by_alias=True, mode="json") for e in explanation] if explanation else None
    s.evidence = evidence.model_dump(by_alias=True, mode="json") if evidence else None
    s.finished = True

    yield (
        "final",
        _response(
            s,
            _final_reply(s, stop, has_summary=bool(explanation and any(e.info for e in explanation)),
                         has_tests=bool(evidence and evidence.sources)),
            steps,
            candidates=_candidates(s, s.shortlist),
            progress=_progress(s, len(s.shortlist)),
            explanation=explanation,
            evidence=evidence,
        ),
    )


def _merge_protocol(explanation, evidence, protocol, s):
    """Put the fixed protocol's tests into each shortlisted condition's confirmatory_tests section, with citations.
    Conditions that are not shortlisted keep their summary and get no tests."""
    docs = prescriber.load()["sources"]
    sources = list(evidence.sources) if evidence else []
    next_id = max((x.id for x in sources), default=0) + 1
    made: dict = {}
    existing = {e.disease_id: e for e in (explanation or [])}
    replaced: dict = {}
    for cid in s.shortlist:
        item = protocol["by_condition"].get(cid)
        entry = existing.get(cid)
        if item:
            cites = []
            for sid, loc in item["citations"]:
                key = (sid, loc, cid)
                if key not in made:
                    d = docs[sid]
                    f = d.get("kb_file")
                    if f and not (config.KB_DOCS_DIR / f).exists():
                        f = None
                    sources.append(Source(
                        id=next_id, title=f"{d['title']} ({d['issuer']}, {d['year']})", location=loc,
                        body=d["issuer"] if d["issuer"] in ("ICMR", "MoHFW") else None,
                        disease=condition_name(cid), content_type="confirmatory_tests",
                        file=f, url=f"/kb-docs/{f}" if f else d["url"], snippet=None))
                    made[key] = next_id
                    next_id += 1
                cites.append(made[key])
            secs = [x for x in (entry.sections if entry else []) if x.content_type != "confirmatory_tests"]
            secs.append(ExplanationSection(content_type="confirmatory_tests", text=item["text"], citations=cites))
            order = list(CONTENT_TYPES)
            secs.sort(key=lambda x: order.index(x.content_type))
            entry = DiseaseExplanation(disease_id=cid, disease=condition_name(cid),
                                       info=entry.info if entry else None, sections=secs)
            replaced[cid] = entry
    merged = [replaced.pop(e.disease_id, e) for e in (explanation or [])] + list(replaced.values())
    if evidence:
        evidence = evidence.model_copy(update={"sources": sources, "source_count": len(sources)})
    else:
        evidence = EvidenceData(source_count=len(sources), chunk_count=0, retrieval_ms=0,
                                documents_in_index=0, sources=sources)
    return merged, evidence


def _build_sources(passages: list[dict]) -> list[Source]:
    out: list[Source] = []
    for i, p in enumerate(passages, start=1):
        file = p.get("file")
        ct = p.get("content_type")
        out.append(
            Source(
                id=i,
                title=p.get("title") or file or "Guideline document",
                location=p.get("location") or "",
                body=p.get("body"),
                disease=condition_name(p["disease"]) if p.get("disease") else None,
                content_type=ct if ct in CONTENT_TYPES else None,
                relevance=p.get("relevance"),
                file=file,
                url=f"/kb-docs/{file}" if file else None,
                snippet=p.get("text"),
            )
        )
    return out


def _summaries(s: Session) -> list[DiseaseExplanation]:
    """The fixed summary of every condition, most likely first. Tests are added later for the shortlist."""
    ranked = sorted(s.posterior, key=lambda c: s.posterior[c], reverse=True)
    return [
        DiseaseExplanation(disease_id=cid, disease=condition_name(cid), info=DiseaseInfo(**summaries.get(cid)))
        for cid in ranked
    ]


def _final_reply(s: Session, stop: str, has_summary: bool, has_tests: bool) -> str:
    ranked = sorted(s.posterior.items(), key=lambda kv: kv[1], reverse=True)[: config.SHORTLIST_SIZE]
    names = [f"**{condition_name(c)}** ({_fmt_pct(p)})" for c, p in ranked]
    joined = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
    lines = [f"{STOP_TEXT[stop]} The most likely conditions are {joined}."]
    if has_summary and has_tests:
        lines.append(
            "Below is a short summary of each condition and the tests recommended to confirm the likely "
            "ones, from the ICMR/MoHFW test protocol. You can download it as a PDF."
        )
    elif has_summary:
        lines.append("Below is a short summary of each condition. You can download it as a PDF.")
    elif has_tests:
        lines.append("Only the recommended tests from the ICMR/MoHFW test protocol are shown. You can download them as a PDF.")
    else:
        lines.append("I couldn't prepare a summary this time, so only the ranking is shown.")
    lines.append("This is decision support, not a diagnosis. Please discuss it with a doctor.")
    return "\n\n".join(lines)
