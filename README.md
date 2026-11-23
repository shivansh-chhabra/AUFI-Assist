# AUFI Assist

Offline decision support for acute undifferentiated fever. Patient answers a questionnaire (max 12
questions, stops early once the leading condition reaches the confidence threshold), then the RAG
layer retrieves guideline passages for the top conditions, and a cited summary with recommended
tests is shown and can be downloaded as a PDF.

```
frontend/   React + Vite UI (already done)
backend/    FastAPI API + case loop + PDF export
  app/scoring/scorer.py      <- FRIEND: probability table, naive Bayes, question selection (still a stub)
  app/rag/retriever.py       <- app adapter over rag/retrieve.py (friend's ChromaDB retrieval)
  app/rag/ingest.py          <- friend's ingest: builds the index from data/guidelines/
  app/rag/manifest.py        <- which guideline files/pages/conditions to index (TEMPLATE: use friend's)
  app/agent/explainer.py     <- cited summary writer (local LLM via Ollama + citation checks)
  data/guidelines/           <- put the guideline PDFs here (served to the source-preview modal)
```

## Run it (development)

```bash
# terminal 1: backend
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000 --reload

# terminal 2: frontend
cd frontend
npm install
cp .env.example .env.local        # VITE_USE_MOCK_DATA=false  -> talks to the backend
npm run dev                       # http://localhost:5173  (proxies /api -> :8000)
```

Open http://localhost:8000/health to see which of your friend's modules are still `stub`.
Until a module is delivered, the UI shows a plain message naming the missing file; scoring still
works without RAG/agent (you get the ranking and a note that the guideline search isn't connected).

## Build the guideline index and start the local LLM

```bash
cd backend
pip install -r requirements.txt
# put the PDFs in data/guidelines/ and your friend's real manifest.py in app/rag/
python -m app.rag.ingest --dry-run      # chunk and report, nothing stored
python -m app.rag.ingest                # builds data/chroma_db_aufi_mini
python -m app.rag.retrieve --check      # every condition has chunks and a sane top hit

ollama pull llama3.2:3b                 # summary writer; if Ollama is off, summaries are quoted guideline text
```

## Run it (demo day, one process, no Node, no internet)

```bash
cd frontend && npm run build          # once, on any machine with internet
cd ../backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
# open http://<this-machine>:8000
```
The backend serves `frontend/dist` itself. Fonts are bundled, so nothing is fetched online.

## Settings (environment variables, all optional)

| Variable | Default | Meaning |
|---|---|---|
| `AUFI_MAX_QUESTIONS` | 12 | hard limit on questions |
| `AUFI_CONFIDENCE_THRESHOLD` | 0.80 | stop when the top condition reaches this probability |
| `AUFI_MIN_QUESTIONS` | 3 | never stop before this many answers |
| `AUFI_SHORTLIST_SIZE` | 3 | conditions passed to RAG (report says 3 to 5) |
| `AUFI_KB_DOCS_DIR` | backend/data/guidelines | guideline files for ingestion and source preview |
| `AUFI_CHROMA_DIR` | backend/data/chroma_db_aufi_mini | the ChromaDB index |
| `AUFI_RELEVANCE_FLOOR` | 0.25 | passages with cosine similarity below this are dropped |
| `AUFI_CHUNKS_PER_SECTION` | 2 | passages per condition per content type |
| `AUFI_LLM_MODEL` / `AUFI_LLM_URL` | llama3.2:3b / http://localhost:11434 | Ollama model and address |

## Data handling

No database. Each case lives in server memory only, is wiped after 12 h or on restart, and
`GET /conversations` always returns an empty list, so a page refresh on a shared machine never
shows a previous patient's case. Patient text is not logged.

## Tests

`cd backend && pytest -q` (uses fake modules, so it runs before the real ones exist).
