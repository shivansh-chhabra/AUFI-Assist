"""STAGE 1: probabilistic scoring + adaptive question selection.

Wraps diagnose.py (your friend's Bernoulli naive Bayes over the P(feature | condition) table, with
the next question chosen by expected information gain). The pipeline owns the stop rules; this file
only holds the case state and answers the four calls it makes.

Needs the table CSV at AUFI_SCORING_TABLE (default backend/data/scoring_table.csv). STUB reads True
until that file exists, so /health shows the truth.

The patient's opening text is turned into features by the keyword rules in _RULES below (a feature is
only used if the table has that column). They are deliberately conservative: a missed symptom costs
one extra question, a wrong match would skew the ranking.
"""
import os
import re
import threading
from dataclasses import dataclass, field
from difflib import get_close_matches
from typing import Optional

from .. import config
from ..conditions import CONDITIONS, MANIFEST_NAMES
from . import diagnose as dx

_lock = threading.Lock()
_table = None  # (conds, feats, P, prior, cond_ids)


def __getattr__(name):  # module-level, so getattr(scorer, "STUB") in /health is live
    if name == "STUB":
        return not os.path.isfile(config.SCORING_TABLE)
    raise AttributeError(name)


# feature column -> phrases in the patient's own words
_RULES = {
    "rash_maculopapular": r"\brash\b",
    "eschar": r"\beschar\b|black (scab|spot|lesion)",
    "jaundice": r"jaundice|yellow(ing)? (of )?(the )?(eyes|skin)|yellow eyes",
    "cough": r"\bcough",
    "weight_loss": r"weight loss|losing weight|lost weight",
    "night_sweats": r"night sweats?",
    "hemorrhagic_signs": r"bleeding|bruis|petechiae|blood in (the )?(stool|urine)",
    "conjunctival_suffusion": r"red eyes?|conjunctival",
    "myalgia_severe": r"severe (muscle|body) (pain|ache)s?|severe myalgia",
    "arthralgia_poly": r"(several|multiple|many) joints|polyarthralgia",
    "gi_symptoms": r"vomit|nausea|diarrh|abdominal pain|stomach pain",
    "lymphadenopathy_reg": r"swollen (lymph )?(nodes|glands)",
    "fever_cyclical": r"on and off|comes and goes|every (other|second|third) day",
    "fever_continuous": r"continuous fever|constant fever|persistent fever|fever (that )?(never|doesn'?t) (goes? away|stops?)",
    "fever_prolonged": r"prolonged fever|fever (for|since|lasting)[^.]{0,20}weeks?|(\d+|two|three|four|five|six) weeks? (of )?fever",
    "travel_endemic_hx": r"\btravel|returned from",
    "water_exposure_hx": r"flood|contaminated water|wading|stagnant water",
}
_NEG = re.compile(r"\b(no|not|without|denies|denied|never)\b[^.;,]*$", re.I)


@dataclass
class CaseState:
    post: list
    asked: set = field(default_factory=set)
    from_text: dict = field(default_factory=dict)  # feature -> present? (for debugging/tests)


def _load():
    """Read the CSV once and map each of its conditions to an app condition id."""
    global _table
    with _lock:
        if _table is None:
            if not os.path.isfile(config.SCORING_TABLE):
                # NotImplementedError makes the pipeline say "module not installed" instead of "went wrong"
                raise NotImplementedError(
                    f"scoring table not found at {config.SCORING_TABLE} (set AUFI_SCORING_TABLE)")
            conds, feats, P, prior = dx.load_table(str(config.SCORING_TABLE))
            by_name = {n.lower(): cid for cid, n in MANIFEST_NAMES.items()}
            ids = []
            for c in conds:
                cid = by_name.get(c.lower())
                if cid is None:  # tolerate small spelling differences
                    m = get_close_matches(c.lower(), list(by_name), n=1, cutoff=0.8)
                    cid = by_name[m[0]] if m else None
                ids.append(cid)
            bad = [c for c, i in zip(conds, ids) if i is None]
            missing = [c for c in CONDITIONS if c not in ids]
            if bad or missing or len(set(ids)) != len(ids):
                raise ValueError(
                    f"scoring table conditions do not match the app's 11 (unknown: {bad}, "
                    f"missing: {missing}). Fix the CSV or MANIFEST_NAMES in app/conditions.py.")
            _table = (conds, feats, P, prior, ids)
        return _table


def _extract(text: str, feats: list) -> dict:
    found = {}
    low = (text or "").lower()
    for feat, rx in _RULES.items():
        if feat not in feats:
            continue
        m = re.search(rx, low)
        if not m:
            continue
        found[feat] = not _NEG.search(low[max(0, m.start() - 40): m.start()])
    return found


def start_case(initial_text: str) -> CaseState:
    _, feats, P, prior, _ = _load()
    state = CaseState(post=list(prior))
    # never ask outcome-type features or 'fever' itself (every patient has it)
    state.asked = {feats.index(f) for f in (*dx.EXCLUDE, "fever") if f in feats}
    state.from_text = _extract(initial_text, feats)
    for feat, present in state.from_text.items():
        j = feats.index(feat)
        state.post = dx.update(state.post, P, j, present)
        state.asked.add(j)
    return state


def apply_answer(state: CaseState, feature: str, value: str) -> None:
    _, feats, P, _, _ = _load()
    if feature not in feats:
        raise ValueError(f"unknown feature {feature!r}")
    j = feats.index(feature)
    state.asked.add(j)
    if value in ("yes", "no"):  # 'unsure' and 'skip' are NOT treated as 'no'
        state.post = dx.update(state.post, P, j, value == "yes")


def get_posterior(state: CaseState) -> dict[str, float]:
    ids = _load()[4]
    return {cid: float(p) for cid, p in zip(ids, state.post)}


def choose_next_question(state: CaseState) -> Optional[dict]:
    _, feats, P, _, _ = _load()
    gain, j = dx.next_question(state.post, P, state.asked)
    if j is None or gain < dx.MIN_GAIN:
        return None
    feat = feats[j]
    return {
        "feature": feat,
        "text": dx.QUESTIONS.get(feat, dx.norm(feat) + "?"),
        "information_gain": round(gain, 3),
    }
