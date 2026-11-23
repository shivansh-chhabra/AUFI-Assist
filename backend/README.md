# Backend: what is integrated and what is still missing

| File | Status |
|---|---|
| `app/rag/retriever.py` | done: adapter that fits the app contract; uses friend's `rag/retrieve.py` |
| `app/rag/ingest.py`, `app/rag/retrieve.py` | friend's code, imports and paths adjusted |
| `app/rag/manifest.py` | **TEMPLATE**: replace with friend's real manifest (not sent yet) |
| `app/agent/explainer.py`, `app/agent/llm.py` | done: Ollama summary writer with citation, number and wording checks |
| `app/scoring/scorer.py` | **still a stub**: `start_case`, `apply_answer`, `get_posterior`, `choose_next_question` |

Rules the backend enforces so the UI never shows something unsafe:
- condition ids must be those in `app/conditions.py`;
- every summary section needs at least one citation that is a real passage id, otherwise it is dropped;
- if retrieval or the agent fails, the patient still gets the ranking.

Stop rule lives in `app/pipeline.py`: 12 questions, or top probability >= 0.80 after at least 3.

Check: `pytest -q`, then open `/health` (rag shows `ready` once the index exists).
