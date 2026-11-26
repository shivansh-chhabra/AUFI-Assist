"""STAGE 2b: writes the cited per-condition summary and recommended tests.

For each shortlisted condition a local LLM (Ollama, llama3.2:3b by default) condenses ONLY the
retrieved guideline passages into short sections. The output is checked before it is used:

  * every citation must be a passage id belonging to that condition;
  * every number in a section (days, doses, thresholds) must appear in the passages it cites;
  * most of the section's content words must appear in those passages.

A section that fails a check, or is missing, is replaced by an extractive one: the opening
sentences of the best matching passage, quoted as written, cited to that passage. If Ollama is
not running, every section is extractive, so the app still works offline with no LLM.
Nothing is ever written without a citation.

The ReAct "lock-in" loop in your friend's agent.py picks one diagnosis for the vignette evaluation.
It is not part of this stage: the app shows the ranked shortlist and a summary for each condition.
"""
import logging
import re
from typing import Optional

from .. import config
from ..conditions import CONDITIONS, CONTENT_TYPES
from .llm import Ollama, parse_json

log = logging.getLogger("aufi.explainer")

STUB = False

_llm: Optional[Ollama] = None

SYSTEM = """You write a short guideline summary for ONE condition in a clinical decision-support demo for undifferentiated fever. You are given numbered excerpts from clinical guidelines.

Reply with exactly one JSON object and nothing else:
{"sections": [{"content_type": "clinical_features" | "confirmatory_tests" | "treatment", "text": "<1 to 3 sentences>", "citations": [<excerpt numbers>]}]}

Rules:
- Use ONLY what the excerpts say. Do not add facts, numbers, drug names or doses that are not in them.
- Every section must cite the excerpt numbers it is based on. Cite only numbers you were given.
- clinical_features: how the condition presents. confirmatory_tests: the tests the guidelines recommend to confirm it, and when they are valid. treatment: management steps.
- Write a section only if the excerpts support it. Leave it out otherwise. Do not guess.
- A symptom missing from an excerpt is not evidence against the condition.
- Do not say the patient has the condition. Do not mention probabilities."""

_STOP = set("""the and for with that this from have has are was were not but can may will should also into than then
their there these those when which while where what who whom been being its such only other more most some any each
both per via use used using patients patient cases case people person may might must within without about over under
between during after before above below upon often usually generally including include includes""".split())
_WORD = re.compile(r"[a-z][a-z\-]{3,}")
_NUM = re.compile(r"\d+(?:[.,]\d+)?")
_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(])")


def _llm_client() -> Ollama:
    global _llm
    if _llm is None:
        _llm = Ollama()
    return _llm


# ---------------------------------------------------------------- checks
def _content_words(text: str) -> set:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP}


def _numbers(text: str) -> set:
    return {n.replace(",", ".") for n in _NUM.findall(text)}


def grounded(text: str, cited_texts: list[str], min_overlap: float = 0.6) -> bool:
    """Numbers must all appear in the cited passages; content words mostly so."""
    source = " ".join(cited_texts)
    if not _numbers(text) <= _numbers(source):
        return False
    words = _content_words(text)
    if not words:
        return False
    return len(words & _content_words(source)) / len(words) >= min_overlap


def _clean(text: str) -> str:
    return " ".join(str(text or "").split())


def extractive(passage_text: str, max_chars: int = 450) -> str:
    """The opening sentences of a passage, verbatim, up to max_chars (never cut mid-word)."""
    t = _clean(passage_text)
    out = ""
    for s in _SENT.split(t):
        if out and len(out) + len(s) + 1 > max_chars:
            break
        out = (out + " " + s).strip()
    if len(out) > max_chars:
        out = out[:max_chars].rsplit(" ", 1)[0] + "…"
    return out


# ---------------------------------------------------------------- prompt + LLM call
def _prompt(name: str, findings: list[dict], initial_text: str, plist: list[dict]) -> str:
    yes = [f["question"] for f in findings if f.get("answer") == "yes"]
    no = [f["question"] for f in findings if f.get("answer") == "no"]
    lines = [f"CONDITION: {name}", ""]
    ctx = []
    if initial_text:
        ctx.append("Patient description: " + _clean(initial_text)[:400])
    if yes:
        ctx.append("Answered yes: " + "; ".join(yes))
    if no:
        ctx.append("Answered no: " + "; ".join(no))
    if ctx:
        lines += ["CASE (context only, do not copy it into the summary):"] + ctx + [""]
    lines.append("EXCERPTS:")
    for p in plist:
        lines.append(f"[{p['id']}] ({p.get('title') or 'guideline'}, {p.get('location') or ''}) "
                     + _clean(p["text"])[: config.LLM_CHUNK_CHARS])
    return "\n".join(lines)


def _llm_sections(name: str, findings, initial_text, plist) -> list[dict]:
    """Sections the LLM wrote that pass every check; [] if the LLM is unavailable or useless."""
    llm = _llm_client()
    if not llm.available():
        return []
    try:
        raw = llm.chat([{"role": "system", "content": SYSTEM},
                        {"role": "user", "content": _prompt(name, findings, initial_text, plist)}])
    except (OSError, ValueError) as e:
        log.warning("LLM call failed for %s: %s", name, e)
        llm._ok = False
        return []
    obj = parse_json(raw)
    if not obj:
        log.warning("LLM returned no valid JSON for %s", name)
        return []

    by_id = {int(p["id"]): p for p in plist}
    out, used = [], set()
    for sec in obj.get("sections") or []:
        if not isinstance(sec, dict):
            continue
        ct = sec.get("content_type")
        text = _clean(sec.get("text"))
        try:
            cites = sorted({int(c) for c in sec.get("citations") or [] if int(c) in by_id})
        except (TypeError, ValueError):
            continue
        if ct not in CONTENT_TYPES or ct in used or not text or not cites:
            continue
        if len(text) > 700 or not grounded(text, [by_id[c]["text"] for c in cites]):
            log.info("dropped ungrounded LLM section (%s, %s)", name, ct)
            continue
        used.add(ct)
        out.append({"content_type": ct, "text": text, "citations": cites})
    return out


# ---------------------------------------------------------------- patient questions
ANSWER_SYSTEM = """You answer a patient's question about one condition using numbered excerpts from Indian clinical guidelines.

Reply with exactly one JSON object and nothing else:
{"answer": "<2 to 5 short sentences in plain language>", "citations": [<excerpt numbers>]}

Rules:
- Use ONLY what the excerpts say. Do not add facts, numbers, drug names or doses that are not in them.
- If the excerpts do not answer the question, reply {"answer": "", "citations": []}.
- Cite the excerpt numbers the answer is based on. Cite only numbers you were given.
- Do not tell the person they have the condition."""


def answer_question(question: str, name: str, plist: list[dict]) -> list[dict]:
    """Blocks [{"text", "citations": [passage ids]}] that answer the question from the passages only.
    [] means the passages do not answer it. Falls back to quoted guideline text if the LLM is off."""
    if not plist:
        return []
    by_id = {int(p["id"]): p for p in plist}
    llm = _llm_client()
    if llm.available():
        try:
            lines = [f"CONDITION: {name}", f"QUESTION: {_clean(question)[:400]}", "", "EXCERPTS:"]
            lines += [f"[{p['id']}] ({p.get('title') or 'guideline'}, {p.get('location') or ''}) "
                      + _clean(p["text"])[: config.LLM_CHUNK_CHARS] for p in plist]
            obj = parse_json(llm.chat([{"role": "system", "content": ANSWER_SYSTEM},
                                       {"role": "user", "content": "\n".join(lines)}]))
            if obj is not None:
                text = _clean(obj.get("answer"))
                if not text:
                    return []             # the model says the excerpts do not cover it
                cites = sorted({int(c) for c in obj.get("citations") or [] if int(c) in by_id})
                if cites and len(text) <= 900 and grounded(text, [by_id[c]["text"] for c in cites], 0.5):
                    return [{"text": text, "citations": cites}]
                log.info("dropped ungrounded answer for %s", name)
        except (OSError, ValueError, TypeError) as e:
            log.warning("answer LLM failed: %s", e)
            llm._ok = False
    return [{"text": extractive(p["text"], 380), "citations": [int(p["id"])]} for p in plist[:2]]


# ---------------------------------------------------------------- main entry
def _match(passage_disease, cid: str) -> bool:
    """Pipeline passes the display name; accept the id too."""
    return passage_disease in (cid, CONDITIONS.get(cid))


def explain(
    shortlist: list[dict],
    findings: list[dict],
    initial_text: str,
    passages: list[dict],
) -> list[dict]:
    result = []
    for cand in shortlist:
        cid, name = cand["id"], cand["name"]
        plist = [p for p in passages if _match(p.get("disease"), cid) and p.get("text")]
        if not plist:
            continue                      # nothing retrieved for it: make no claim

        sections = {s["content_type"]: s for s in _llm_sections(name, findings, initial_text, plist)}
        for ct in CONTENT_TYPES:          # fill gaps with quoted guideline text
            if ct in sections:
                continue
            best = next((p for p in plist if p.get("content_type") == ct), None)
            if best:
                sections[ct] = {"content_type": ct, "text": extractive(best["text"]),
                                "citations": [int(best["id"])]}
        ordered = [sections[ct] for ct in CONTENT_TYPES if ct in sections]
        if ordered:
            result.append({"disease_id": cid, "sections": ordered})
    return result
