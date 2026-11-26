"""Fixed per-condition summaries, read from data/disease_summaries.json.

The text is written by hand and never changes at run time, so a case always shows the same summary
for a condition, instantly, with no retrieval and no LLM. (The post-result Q&A still uses the
guideline index; see pipeline._answer_followup.)

The JSON uses its own ids for two conditions; JSON_IDS maps them to the app's ids.
"""
import json
from functools import lru_cache
from typing import Optional

from . import config
from .conditions import CONDITIONS

# JSON id -> app id (only where they differ)
JSON_IDS = {
    "scrub_murine_typhus": "scrub_typhus",
    "occult_bacteremia": "occult_bacteraemia",
}
_FIELDS = ("causative_agent", "transmission", "summary", "preventive_methods")


@lru_cache(maxsize=1)
def load() -> dict[str, dict]:
    """{app condition id: {causative_agent, transmission, summary, preventive_methods}}.

    Raises ValueError at first use if a condition is missing or a field is empty, so a bad edit to
    the JSON is caught on the first case (and by the tests) rather than showing a blank summary."""
    with open(config.DISEASE_SUMMARIES, encoding="utf-8") as f:
        raw = json.load(f)
    out: dict[str, dict] = {}
    for d in raw.get("diseases", []):
        cid = JSON_IDS.get(d.get("id"), d.get("id"))
        if cid not in CONDITIONS:
            raise ValueError(f"disease_summaries.json: unknown condition id {d.get('id')!r}")
        for k in _FIELDS:
            if not d.get(k):
                raise ValueError(f"disease_summaries.json: {d.get('id')!r} has no {k!r}")
        out[cid] = {k: d[k] for k in _FIELDS}
    missing = sorted(set(CONDITIONS) - set(out))
    if missing:
        raise ValueError(f"disease_summaries.json: no summary for {', '.join(missing)}")
    return out


def get(cid: str) -> Optional[dict]:
    return load().get(cid)
