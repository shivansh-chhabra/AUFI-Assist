"""The case loop: questionnaire -> stop rule -> RAG -> cited summary.

`run_turn()` is a generator of ("step", text) events followed by one ("final", ChatResponse).
The /chat/stream route forwards the events as SSE; /chat just drains it.

This module has no web-framework imports so it can be tested on its own.
"""
import logging
import re
import time
from typing import Any, Iterator, Optional

from . import config
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
    EvidenceData,
    EvidenceFilter,
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
        yield (
            "final",
            _response(
                s, "This case is complete. To assess another patient, start a new case.", steps,
                candidates=_candidates(s, s.shortlist), progress=_progress(s, len(s.shortlist)),
            ),
        )
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

    # retrieval (failure here must not lose the scoring result)
    sources: list[Source] = []
    evidence: Optional[EvidenceData] = None
    retrieval_failed = False
    yield note("Searching the guideline documents for the shortlisted conditions.")
    t0 = time.perf_counter()
    try:
        raw = retriever.retrieve(s.shortlist, _case_query(s))
        sources = _build_sources(raw.get("passages", []))
        evidence = EvidenceData(
            source_count=len(sources),
            chunk_count=int(raw.get("chunk_count", len(sources))),
            retrieval_ms=round((time.perf_counter() - t0) * 1000),
            documents_in_index=int(raw.get("documents_in_index", 0)),
            sources=sources,
            dropped_below_threshold=raw.get("dropped_below_threshold"),
            filters=_build_filters(raw.get("filters")),
        )
        yield note(f"Found {len(sources)} guideline passage{'s' if len(sources) != 1 else ''}.")
    except NotImplementedError:
        retrieval_failed = True
        yield note("Guideline search is not connected yet; showing the scoring result only.")
    except Exception:
        log.exception("retrieval failed")
        retrieval_failed = True
        yield note("Guideline search failed; showing the scoring result only.")

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

    # cited summary (failure here must not lose the scoring result either)
    explanation: Optional[list[DiseaseExplanation]] = None
    if sources:
        yield note("Writing the cited summary and recommended tests.")
        try:
            explanation, dropped = _explain(s, sources)
            if dropped:
                yield note(f"Removed {dropped} statement{'s' if dropped != 1 else ''} without a valid citation.")
        except NotImplementedError:
            yield note("The summary writer is not connected yet; showing the scoring result and sources only.")
        except Exception:
            log.exception("explanation failed")
            yield note("Could not write the summary; showing the scoring result and sources only.")

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
            _final_reply(s, stop, bool(explanation), retrieval_failed, bool(sources)),
            steps,
            candidates=_candidates(s, s.shortlist),
            progress=_progress(s, len(s.shortlist)),
            explanation=explanation,
            evidence=evidence,
        ),
    )


def _merge_protocol(explanation, evidence, protocol, s):
    """Put the fixed protocol's tests into each condition's confirmatory_tests section, with citations."""
    docs = prescriber.load()["sources"]
    sources = list(evidence.sources) if evidence else []
    next_id = max((x.id for x in sources), default=0) + 1
    made: dict = {}
    existing = {e.disease_id: e for e in (explanation or [])}
    merged = []
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
            entry = DiseaseExplanation(disease_id=cid, disease=condition_name(cid), sections=secs)
        if entry:
            merged.append(entry)
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


def _build_filters(raw: Optional[list[dict]]) -> Optional[list[EvidenceFilter]]:
    if not raw:
        return None
    return [
        EvidenceFilter(disease=condition_name(f["disease"]), content_type=f["content_type"])
        for f in raw
        if f.get("content_type") in CONTENT_TYPES and f.get("disease")
    ]


def _explain(s: Session, sources: list[Source]) -> tuple[Optional[list[DiseaseExplanation]], int]:
    shortlist = [{"id": c, "name": condition_name(c), "probability": s.posterior[c]} for c in s.shortlist]
    findings = [
        {"feature": a["feature"], "question": a["text"], "answer": a["answer"]} for a in s.asked
    ]
    passages = [
        {
            "id": src.id, "text": src.snippet, "title": src.title, "location": src.location,
            "body": src.body, "disease": src.disease, "content_type": src.content_type,
        }
        for src in sources
    ]
    raw = explainer.explain(shortlist, findings, s.initial_text, passages)

    valid_ids = {src.id for src in sources}
    dropped = 0
    result: list[DiseaseExplanation] = []
    for entry in raw or []:
        cid = entry.get("disease_id")
        if cid not in CONDITIONS:
            continue
        sections: list[ExplanationSection] = []
        for sec in entry.get("sections", []):
            text = (sec.get("text") or "").strip()
            cites = [int(c) for c in sec.get("citations", []) if int(c) in valid_ids]
            if sec.get("content_type") not in CONTENT_TYPES or not text:
                continue
            if not cites:  # the UI promises "every statement is cited"
                dropped += 1
                continue
            sections.append(ExplanationSection(content_type=sec["content_type"], text=text, citations=cites))
        if sections:
            result.append(DiseaseExplanation(disease_id=cid, disease=condition_name(cid), sections=sections))
    return (result or None), dropped


def _final_reply(s: Session, stop: str, has_expl: bool, retrieval_failed: bool, has_sources: bool) -> str:
    ranked = sorted(s.posterior.items(), key=lambda kv: kv[1], reverse=True)[: config.SHORTLIST_SIZE]
    names = [f"**{condition_name(c)}** ({_fmt_pct(p)})" for c, p in ranked]
    joined = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
    lines = [f"{STOP_TEXT[stop]} The most likely conditions are {joined}."]
    if has_expl and retrieval_failed:
        lines.append(
            "I couldn't search the guidelines this time, so only the recommended tests from the fixed "
            "ICMR/MoHFW test protocol are shown. You can download it as a PDF."
        )
    elif has_expl:
        lines.append(
            "The summary below is taken from the clinical guidelines and includes the tests "
            "recommended to confirm each condition. You can download it as a PDF."
        )
    elif retrieval_failed:
        lines.append("I couldn't search the guidelines this time, so only the ranking is shown.")
    elif not has_sources:
        lines.append("No guideline passage was close enough to this case, so no medical claim is made beyond the ranking.")
    else:
        lines.append("I couldn't write the guideline summary this time; the retrieved sources are listed below.")
    lines.append("This is decision support, not a diagnosis. Please discuss it with a doctor.")
    return "\n\n".join(lines)
