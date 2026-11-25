"""All tunable settings in one place. Override any of them with environment variables."""
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent

# --- questionnaire loop -------------------------------------------------------
MAX_QUESTIONS = int(os.getenv("AUFI_MAX_QUESTIONS", "12"))
# Stop asking once the leading condition reaches this probability ...
CONFIDENCE_THRESHOLD = float(os.getenv("AUFI_CONFIDENCE_THRESHOLD", "0.80"))
# ... but never before this many questions, so a single sentence can't end the case.
MIN_QUESTIONS = int(os.getenv("AUFI_MIN_QUESTIONS", "3"))
# How many top conditions go on to the RAG stage (report says 3 to 5).
SHORTLIST_SIZE = int(os.getenv("AUFI_SHORTLIST_SIZE", "3"))
# Conditions below this probability no longer count as "remaining" in the progress strip.
REMAINING_FLOOR = float(os.getenv("AUFI_REMAINING_FLOOR", "0.05"))

# --- storage: nothing is persisted, sessions live in memory only --------------
SESSION_TTL_HOURS = float(os.getenv("AUFI_SESSION_TTL_HOURS", "12"))

# --- files --------------------------------------------------------------------
KB_DOCS_DIR = Path(os.getenv("AUFI_KB_DOCS_DIR", BACKEND_DIR / "data" / "guidelines"))
FRONTEND_DIST = Path(os.getenv("AUFI_FRONTEND_DIST", BACKEND_DIR.parent / "frontend" / "dist"))

# --- guideline index (ChromaDB, built by `python -m app.rag.ingest`) ------------
CHROMA_DIR = Path(os.getenv("AUFI_CHROMA_DIR", BACKEND_DIR / "data" / "chroma_db_aufi_mini"))
# Passages with cosine similarity below this are dropped (the UI then says no claim is made).
# Starting value for all-MiniLM-L6-v2; tune it with `python -m app.rag.retrieve --check`.
RELEVANCE_FLOOR = float(os.getenv("AUFI_RELEVANCE_FLOOR", "0.25"))
# Passages kept per (condition, content type) pair: 3 conditions x 3 types x 2 = at most 18.
CHUNKS_PER_SECTION = int(os.getenv("AUFI_CHUNKS_PER_SECTION", "2"))

# --- local LLM for the summary writer (Ollama, no internet needed) --------------
LLM_URL = os.getenv("AUFI_LLM_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("AUFI_LLM_MODEL", "llama3.2:3b")
LLM_NUM_CTX = int(os.getenv("AUFI_LLM_NUM_CTX", "8192"))
LLM_TIMEOUT = int(os.getenv("AUFI_LLM_TIMEOUT", "180"))
# Characters of each passage shown to the LLM (a 220-token chunk is roughly 900-1000 characters).
LLM_CHUNK_CHARS = int(os.getenv("AUFI_LLM_CHUNK_CHARS", "1000"))

# --- scoring table (P(feature | condition) CSV read by scoring/diagnose.py) ------
SCORING_TABLE = Path(os.getenv("AUFI_SCORING_TABLE", BACKEND_DIR / "data" / "scoring_table.csv"))

# --- fixed test protocol (app/protocols) -----------------------------------------
# When on, recommended tests come from the fixed ICMR/MoHFW document, not from retrieval.
TESTS_FROM_PROTOCOL = os.getenv("AUFI_TESTS_FROM_PROTOCOL", "1") not in ("0", "false", "False")
# Two conditions whose probabilities differ by no more than this are a "close call": the document's
# differentiating tests are shown. Absolute probability, e.g. 0.10 = 10 percentage points.
CLOSE_MARGIN = float(os.getenv("AUFI_CLOSE_MARGIN", "0.10"))
