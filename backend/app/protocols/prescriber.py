"""Fixed test recommendations from app/protocols/test_protocols.json.

The JSON is written from ICMR and MoHFW guidelines only and never changes at run time, so the same
shortlist and day of fever always give the same tests. No retrieval and no LLM is involved.

prescribe() returns, for each shortlisted condition, a short text and a list of (source id, locator)
citations. When the leading conditions are close, it adds the tests that separate them.
"""
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from .. import config
from ..conditions import condition_name

_PATH = Path(__file__).with_name("test_protocols.json")
_DAY = [
    re.compile(r"\bday\s*(\d{1,2})\b(?:\s*of\s*(?:the\s*)?(?:fever|illness|symptoms?))?", re.I),
    re.compile(r"\b(?:fever|febrile|ill|symptoms?)\s*(?:for|since|x)\s*(\d{1,2})\s*days?\b", re.I),
    re.compile(r"\b(\d{1,2})\s*days?\s*(?:of\s*)?(?:fever|illness|symptoms?|history)\b", re.I),
    re.compile(r"\b(\d{1,2})\s*days?\s*ago\b", re.I),
]


@lru_cache(maxsize=1)
def load() -> dict:
    with open(_PATH, encoding="utf-8") as f:
        return json.load(f)


def parse_day_of_fever(text: str) -> Optional[int]:
    """'fever for 4 days', 'day 3 of fever', '5 days of fever' -> the number; otherwise None."""
    for rx in _DAY:
        m = rx.search(text or "")
        if m and 1 <= int(m.group(1)) <= 60:
            return int(m.group(1))
    return None


def _status(when: dict, day: Optional[int]) -> str:
    if day is None:
        return "ok"
    if when.get("from") is not None and day < when["from"]:
        return "early"
    if when.get("to") is not None and day > when["to"]:
        return "late"
    return "ok"


def _cite(s: str) -> tuple[str, str]:
    sid, _, loc = s.partition(":")
    return sid, loc


def _name(tid: str) -> str:
    return load()["tests"][tid]["name"]


def _window(tid: str, cids, day) -> dict:
    d = load()["conditions"]
    for cid in cids:
        for k in ("first_line", "also", "conditional"):
            for e in d.get(cid, {}).get(k, []):
                if e["test"] == tid:
                    return e.get("when", {})
    return {}


def _bullet(e: dict, day) -> Optional[str]:
    st = _status(e["when"], day)
    if st == "late":
        return None
    w = e["when"].get("text") or ""
    extra = f" (not valid yet; use {w})" if st == "early" else (f" ({w})" if w and w != "any day of illness" else "")
    return f"- **{_name(e['test'])}**{extra}"


def baseline_text(day: Optional[int]) -> tuple[str, list]:
    stages = load()["common_workup"]
    if day is None:
        s = next(x for x in stages if x["id"] == "day_3_4")
        text = (s["text"] + " After day 5 add blood cultures and a chest X-ray; after day 7 add an abdominal ultrasound.")
        return text, [_cite(c) for c in s["src"]]
    s = [x for x in stages if x["from_day"] <= day][-1]
    return s["text"], [_cite(c) for c in s["src"]]


def condition_text(cid: str, day: Optional[int]) -> tuple[str, list]:
    c = load()["conditions"][cid]
    cites, blocks = [], []
    first = [(e, _bullet(e, day)) for e in c.get("first_line", [])]
    first = [(e, t) for e, t in first if t]
    if first:
        blocks.append("**Recommended tests**\n" + "\n".join(t for _, t in first))
        for e, _ in first:
            cites += [_cite(x) for x in e["src"]]
    for e in c.get("conditional", []):
        blocks.append(f"**If {e['if_']}**\n- **{_name(e['test'])}**: {e['why']}")
        cites += [_cite(x) for x in e["src"]]
    also = [e for e in c.get("also", []) if _status(e["when"], day) != "late"]
    if also:
        blocks.append("**Also useful**\n" + "\n".join(f"- **{_name(e['test'])}**" for e in also))
        for e in also:
            cites += [_cite(x) for x in e["src"]]
    nr = c.get("not_recommended", [])
    if nr:
        blocks.append("**Not recommended**\n" + "\n".join(f"- **{_name(e['test'])}**: {e['why']}" for e in nr))
        for e in nr:
            cites += [_cite(x) for x in e["src"]]
    for n in c.get("notes", []):
        blocks.append("**Note:** " + n["text"])
        cites += [_cite(x) for x in n["src"]]
    return "\n\n".join(blocks), cites


def pair_info(a: str, b: str, day: Optional[int]) -> dict:
    d = load()
    for p in d["pair_differentiators"]:
        if set(p["pair"]) == {a, b}:
            tests = [t for t in p["tests"] if _status(_window(t, (a, b), day), day) == "ok"]
            return {"tests": tests, "contrast": p["contrast"], "src": [_cite(x) for x in p["src"]], "explicit": True}
    # default rule: diagnostic tests that the other condition does not share, routine before specialised
    def diag(cid):
        c = d["conditions"][cid]
        return [e["test"] for e in c.get("first_line", []) + c.get("conditional", [])
                if d["tests"][e["test"]]["role"] == "diagnostic" and _status(e.get("when", {}), day) == "ok"]
    da, db = diag(a), diag(b)
    uniq = [t for t in da if t not in db] + [t for t in db if t not in da]
    if not uniq:
        uniq = list(dict.fromkeys(da + db))
    uniq.sort(key=lambda t: d["tests"][t]["tier"] != "routine")
    cites = []
    for cid in (a, b):
        for e in d["conditions"][cid].get("first_line", []):
            if e["test"] in uniq:
                cites += [_cite(x) for x in e["src"]]
    return {"tests": uniq, "contrast": None, "src": cites, "explicit": False}


def prescribe(posterior: dict, shortlist: list, day: Optional[int] = None, margin: Optional[float] = None) -> dict:
    """posterior: {condition id: probability}; shortlist: condition ids, best first."""
    margin = config.CLOSE_MARGIN if margin is None else margin
    d = load()
    ids = [c for c in shortlist if c in d["conditions"]]
    if not ids:
        return {"by_condition": {}, "close": [], "day": day, "version": d["meta"]["version"]}
    lead = posterior.get(ids[0], 0.0)
    close = [c for c in ids if lead - posterior.get(c, 0.0) <= margin][:3]
    if len(close) < 2:
        close = []
    out = {}
    for i, cid in enumerate(ids):
        text, cites = condition_text(cid, day)
        pre = []
        if i == 0:
            t, c = baseline_text(day)
            pre.append("**Baseline for any fever:** " + t)
            cites = c + cites
        if cid in close:
            for other in close:
                if other == cid:
                    continue
                info = pair_info(cid, other, day)
                if info["tests"]:
                    bullets = "\n".join(f"- **{_name(t)}**" for t in info["tests"])
                    sent = (f"**Close call: {condition_name(cid)} or {condition_name(other)}.** "
                            f"The probabilities are close. To tell them apart, send:\n{bullets}")
                    if info["contrast"]:
                        sent += "\n\n" + info["contrast"]
                    pre.append(sent)
                    cites = cites + info["src"]
        seen, uniq = set(), []
        for c in cites:
            if c not in seen:
                seen.add(c)
                uniq.append(c)
        out[cid] = {"text": "\n\n".join(pre + [text]).strip(), "citations": uniq}
    return {"by_condition": out, "close": close, "day": day, "version": d["meta"]["version"]}
