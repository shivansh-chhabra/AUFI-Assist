# Backend: what is integrated and what is still missing

| File | Status |
|---|---|
| `app/scoring/diagnose.py` | friend's code, used as is |
| `app/scoring/scorer.py` | done: wraps diagnose.py; needs `data/scoring_table.csv` (not in the repo yet) |
| `app/rag/manifest.py` | friend's manifest, used as is |
| `app/rag/ingest.py`, `retrieve.py` | friend's code, imports and paths adjusted |
| `app/rag/retriever.py` | done: adapter that fits the app contract |
| `app/agent/explainer.py`, `llm.py` | done: Ollama summary writer with citation, number and wording checks |

Condition names: the app's ids (`app/conditions.py`) map to the names used in `manifest.py` and in the
CSV's condition column through `MANIFEST_NAMES` in that file. If a name changes, edit it there only.
`pytest` fails if it drifts from `manifest.py`.

Rules the backend enforces so the UI never shows something unsafe:
- every summary section needs at least one citation that is a real passage id, otherwise it is dropped;
- if retrieval or the agent fails, the patient still gets the ranking.

Stop rule lives in `app/pipeline.py`: 12 questions, or top probability >= 0.80 after at least 3.

Check: `pytest -q`, then open `/health` (all three say `ready` once the CSV and index exist).
