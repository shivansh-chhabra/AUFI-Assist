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
