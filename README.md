# AUFI Assist

AUFI Assist is a decision-support tool for acute undifferentiated fever (AUFI): a patient or health worker describes the fever in a few words, answers a handful of yes/no questions, and gets back a ranked shortlist of likely causes, the tests that would confirm them, and a plain-language summary of each condition. The result can be downloaded as a PDF to take to a doctor.

It covers eleven conditions that commonly sit behind an undifferentiated fever in India:

malaria, dengue, typhoid, scrub and murine typhus, leptospirosis, chikungunya, viral influenza-like illness, hepatitis A and E, occult bacteraemia, rheumatic fever, and TB (prolonged fever presentation).

This is a project prototype. It is **not a medical device and does not diagnose anything**. See [Limitations](#limitations-and-things-to-know) before showing it to anyone.

## How it works

A case goes through three stages.

1. **Scoring and questioning.** The opening description is turned into features with a small set of keyword rules. A Bernoulli naive Bayes model over a table of P(feature | condition) (`backend/data/scoring_table.csv`) gives a probability for each of the 11 conditions. The next question is always the one with the highest expected information gain, so the app asks what actually helps separate the leading candidates instead of walking through a fixed script.
2. **Stop rule.** Questioning ends when the top condition reaches 80% probability (never before 3 questions), when 12 questions have been asked, or when no remaining question would tell the candidates apart. The top 3 conditions become the shortlist.
3. **Result.** For the shortlist, recommended tests come from a fixed protocol written from ICMR and MoHFW documents, taking the day of fever into account (a test that is too early is marked as not valid yet, and one past its window, such as dengue NS1 after day 5, is left out). When the top conditions are close, the tests that tell them apart are added. Every one of the 11 conditions also gets a fixed, hand-written summary: what it is, what causes it, how it spreads and how to prevent it.

None of this is generated at run time. The summaries and the test protocol are plain JSON files, so the same case always gives the same result, instantly, and it works with no internet and no LLM.

After the result, the patient can type follow-up questions ("how does dengue spread?"). Those are answered from an index of the guideline PDFs, with citations, and the app says so when the guidelines do not cover the question rather than guessing. This is the only part that uses retrieval and a language model, and it is optional (see [Guideline index and follow-up questions](#guideline-index-and-follow-up-questions)).

## Project layout

```
aufi_assist/
  backend/                  FastAPI app
    app/
      main.py               routes, PDF endpoint, serves the built frontend
      pipeline.py           the case loop: questions, stop rule, result assembly
      session.py            in-memory sessions
      config.py             every tunable setting (all overridable by env var)
      conditions.py         the 11 condition ids and display names
      summaries.py          loads the fixed per-condition summaries
      report.py             PDF export (reportlab)
      schemas.py            response models (camelCase on the wire)
      scoring/              naive Bayes scorer and question selection
      protocols/            fixed test recommendations (prescriber + JSON)
      rag/                  guideline ingest, retrieval, adapter
      agent/                Ollama client and the follow-up answer writer
    data/
      scoring_table.csv     P(feature | condition)
      disease_summaries.json  the fixed summaries shown on the result screen
      guidelines/           put the guideline PDFs here (not in the repo)
    scripts/                render_protocols_md.py
    docs/TEST_PROTOCOLS.md  readable copy of the test protocol
    tests/                  pytest suite
  frontend/                 React + Vite + TypeScript chat UI
```

## Getting started

You need Python 3.11 or newer (developed on 3.13) and Node 20.19 or newer.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000 --reload
```

The API is now on http://localhost:8000 and interactive docs are at `/api/docs`. Open `/health` to see which modules are ready.

`requirements.txt` includes the heavy retrieval packages (chromadb, sentence-transformers, pymupdf). If you only want the questionnaire, the summaries and the tests, the app runs without a guideline index: only the follow-up Q&A is affected.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

The dev server proxies `/api` to `localhost:8000`, so start the backend first. To click through the interface with no backend at all, set `VITE_USE_MOCK_DATA=true` in `.env.local`; the UI then plays a scripted demo and labels it as demo data. The demo content is not clinical output. If the backend is down while mock mode is off, the UI shows an error on purpose and never falls back to demo data.

### One-process build

```bash
cd frontend && npm run build
cd ../backend && uvicorn app.main:app --port 8000
```

When `frontend/dist` exists the backend serves it, so the whole app runs from one command with no Node at run time. This is how it is meant to be deployed on a hospital machine.

## Configuration

Everything lives in `backend/app/config.py` and can be overridden with environment variables.

| Variable | Default | What it does |
|---|---|---|
| `AUFI_MAX_QUESTIONS` | 12 | Hard limit on questions per case |
| `AUFI_MIN_QUESTIONS` | 3 | Never stop on confidence before this many |
| `AUFI_CONFIDENCE_THRESHOLD` | 0.80 | Stop once the leading condition reaches this |
| `AUFI_SHORTLIST_SIZE` | 3 | How many conditions get tests in the result |
| `AUFI_REMAINING_FLOOR` | 0.05 | Below this a condition no longer counts as "remaining" |
| `AUFI_CLOSE_MARGIN` | 0.10 | Conditions this close are a "close call"; differentiating tests are added |
| `AUFI_TESTS_FROM_PROTOCOL` | 1 | Set to 0 to stop using the fixed test protocol |
| `AUFI_SESSION_TTL_HOURS` | 12 | How long an idle session is kept in memory |
| `AUFI_SCORING_TABLE` | `data/scoring_table.csv` | Path to the scoring table |
| `AUFI_DISEASE_SUMMARIES` | `data/disease_summaries.json` | Path to the fixed summaries |
| `AUFI_KB_DOCS_DIR` | `data/guidelines` | Where the guideline PDFs live |
| `AUFI_CHROMA_DIR` | `data/chroma_db_aufi_mini` | Where the guideline index is stored |
| `AUFI_RELEVANCE_FLOOR` | 0.25 | Minimum similarity for a retrieved passage to be used |
| `AUFI_LLM_URL` | `http://localhost:11434` | Ollama address |
| `AUFI_LLM_MODEL` | `llama3.2:3b` | Model used for follow-up answers |
| `AUFI_FRONTEND_DIST` | `frontend/dist` | Built frontend to serve |

## Editing the clinical content

The two files below are the clinical content of the result screen. Treat changes to them like changes to a document that a clinician should review.

**Condition summaries** are in `backend/data/disease_summaries.json`. Each condition has a cause, a transmission route, a summary and a list of preventive methods. The file's own note says the text is a general educational summary and should be cross-checked against the ICMR and MoHFW guidelines before real use. Two ids in the file differ from the app's (`scrub_murine_typhus` and `occult_bacteremia`); `app/summaries.py` maps them. The loader refuses to start a case if a condition is missing or a field is empty, and `pytest` checks this too.

**Recommended tests** are in `backend/app/protocols/test_protocols.json`. After editing it, regenerate the readable copy and run the tests:

```bash
python scripts/render_protocols_md.py
pytest -q
```

**Scoring table.** `backend/data/scoring_table.csv` holds the feature probabilities. Condition names in its first column must match `MANIFEST_NAMES` in `app/conditions.py`; if a name changes, change it there and nowhere else. A test fails if they drift apart.

## Guideline index and follow-up questions

The follow-up Q&A needs two optional pieces that are not in the repository:

1. The guideline PDFs, placed in `backend/data/guidelines/`. Which pages of which file are used, and which condition each is tagged with, is decided in `app/rag/manifest.py`.
2. A local Chroma index built from them:

```bash
cd backend
python -m app.rag.ingest --dump      # write cleaned text per manifest entry so you can read it
python -m app.rag.ingest --dry-run   # chunk and report, nothing stored
python -m app.rag.ingest             # build the index
python -m app.rag.retrieve --check   # smoke test: every condition has chunks and a sane top hit
```

For the written answer, install [Ollama](https://ollama.com) and pull the model (`ollama pull llama3.2:3b`). If Ollama is not running, the app quotes the best matching guideline passage instead. If there is no index, follow-up questions say that guideline search is not connected. In every case the ranking, tests and summaries still work.

Answers are checked before they are shown: every citation must be a real retrieved passage, every number must appear in the passages cited, and most of the wording must come from them. Anything that fails is dropped, and a question the guidelines do not cover gets an honest "I couldn't find this" instead of an answer.

## API

All routes are available both at `/` and under `/api`.

| Route | Purpose |
|---|---|
| `POST /chat` | One turn of the case. Returns the full response |
| `POST /chat/stream` | Same, as server-sent events: step events while it works, then a final event |
| `POST /chat/back` | Undo the last answer and re-ask that question |
| `GET /report/{conversation_id}/pdf` | PDF of a finished case |
| `GET /conversations/{id}/messages` | Message history for a session |
| `DELETE /conversations/{id}` | Discard a session |
| `POST /search` | Search the guideline index directly |
| `GET /knowledge-base/status` | Document count and last indexed time |
| `GET /kb-docs/{file}` | A guideline PDF (and `/content` for its text) |
| `GET /health` | Which modules are ready, and the current settings |

A chat request looks like this. `answer` is set when the user tapped a button, so the scorer gets the structured value instead of parsing text.

```json
{ "message": "Yes", "conversation_id": "c1", "answer": { "feature": "rash_or_bleeding", "value": "yes" } }
```

Values are `yes`, `no`, `unsure` or `skip`. Responses use camelCase field names; the exact shape is in `frontend/src/types.ts`. When the questioning stops, the response has `question: null`, a `progress.stopReason`, and an `explanation` with one entry per condition. Each entry has an `info` object (the fixed summary) and, for shortlisted conditions, a `sections` list with the recommended tests and the ids of the sources they cite.

## Tests

```bash
cd backend
pytest -q
```

The suite uses a fake scorer and fake index where it can, so it runs in under a second and needs no guideline files, no Chroma and no Ollama. It covers the stop rules, typed answers, undo, the result assembly, the PDF, the test protocol, the summaries file and the retrieval adapter.

The frontend has no automated tests yet. `npm run build` runs the TypeScript check.

## Privacy

Nothing is written to disk. Sessions live in memory and disappear when the server restarts or after `AUFI_SESSION_TTL_HOURS`. `GET /conversations` deliberately returns an empty list so that refreshing a shared hospital computer never shows the previous patient. The frontend bundles its fonts and makes no outside requests, and the backend needs no internet.

## Limitations and things to know

- It is a shortlist generator, not a diagnostic. Every screen says so, and so should anyone who demos it.
- The scoring table is the model. Its probabilities decide both the ranking and which questions get asked, so the quality of the output is only as good as that CSV. It has not been validated against real patient data.
- Free-text understanding of the opening message is limited to keyword rules, on purpose. A missed symptom costs one extra question; a wrong match would skew the ranking.
- The condition summaries carry no citations. They are hand-written general information, not quoted from a specific passage. Only the recommended tests and the follow-up answers cite guideline sources.
- The day-of-fever window for tests is read from the first message ("fever for 4 days"). If no day is found, the windows are shown as text and nothing is filtered.
- Follow-up answers come from a 3B-parameter local model checked by simple rules. The checks catch invented numbers and unsupported wording, but not every subtle error.
- Sessions are held in one process's memory, so it is a single-server design.

## Contributing

Keep the invariants that the tests protect: nothing clinical is shown without either a fixed source or a valid citation, and a failure in any stage must never lose the ranking. Run `pytest -q` before you push, and if you touch the summaries, test protocol or scoring table, say in the commit message where the new content came from.
