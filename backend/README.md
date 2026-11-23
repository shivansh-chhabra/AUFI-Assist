# Backend: what your friend needs to deliver

Replace the body of the functions in these three files. Keep names, arguments and return shapes
(each file's docstring is the contract), then delete the `STUB = True` line in each.

| File | Functions |
|---|---|
| `app/scoring/scorer.py` | `start_case`, `apply_answer`, `get_posterior`, `choose_next_question` |
| `app/rag/retriever.py` | `retrieve`, `search`, `document_count`, `last_indexed` |
| `app/agent/explainer.py` | `explain` |

Rules the backend enforces so the UI never shows something unsafe:
- condition ids must be those in `app/conditions.py`;
- every summary section needs at least one citation that is a real passage id, otherwise it is dropped;
- if retrieval or the agent fails, the patient still gets the ranking.

Stop rule lives in `app/pipeline.py`: 12 questions, or top probability >= 0.80 after at least 3.

Quick contract check once the modules are in: `pytest -q`, then open `/health`
(all three should say `ready`) and click through a case in the UI.
