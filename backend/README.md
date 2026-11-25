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

## Fixed test protocol (recommended tests)

Recommended tests no longer come from retrieval. They are read from `app/protocols/test_protocols.json`
(ICMR and MoHFW guidelines only) by `app/protocols/prescriber.py`, so the same shortlist and day of
fever always give the same tests, and they appear even when the guideline index or Ollama is down.
- If the top conditions are within `AUFI_CLOSE_MARGIN` (default 0.10) of each other, the tests that tell them apart are added.
- The day of fever is read from the patient's first message ("fever for 4 days"); if absent, windows are shown as text.
- Set `AUFI_TESTS_FROM_PROTOCOL=0` to go back to retrieval for tests.
- After editing the JSON run `python scripts/render_protocols_md.py` to refresh `docs/TEST_PROTOCOLS.md`, then `pytest -q`.
