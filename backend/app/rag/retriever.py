"""STAGE 2: retrieval over the ChromaDB guideline store.

Adapter between the app contract (retrieve / search / document_count / last_indexed) and your
friend's retrieval code in retrieve.py (embeddings + condition-filtered Chroma query) and
ingest.py (builds the index: `python -m app.rag.ingest`).

The index chunks carry condition and provenance metadata but no "kind of content" tag, so the
content type of a passage here is the intent of the query that found it (one query each for
clinical features, confirmatory tests and treatment, per shortlisted condition). Text and page
numbers are always the real guideline chunk; nothing is generated here.

STUB is computed: it reads True until the Chroma index exists, so /health shows the truth.
"""
import hashlib
import logging
import os
import re
import threading
import time
from typing import Optional

from .. import config
from ..conditions import CONDITIONS as APP_CONDITIONS
from ..conditions import CONTENT_TYPES, MANIFEST_NAMES, condition_name

log = logging.getLogger("aufi.rag")

# App condition id -> condition name used in manifest.py (defined in app/conditions.py).
COND_MAP: dict[str, str] = MANIFEST_NAMES
_FROM_MANIFEST = {v: k for k, v in COND_MAP.items()}

# What each content type looks up. Patient text is added to clinical_features only.
_INTENT = {
    "clinical_features": "{name}: clinical features, symptoms, signs and diagnosis.",
    "confirmatory_tests": "{name}: confirmatory laboratory tests and diagnostic criteria.",
    "treatment": "{name}: treatment and management.",
}
_BODIES = {"ICMR", "MOHFW"}
_CASE_CHARS = 300  # the embedding model reads ~256 tokens; keep the intent words in front

_lock = threading.Lock()
_retriever = None


def __getattr__(name):  # module-level, so getattr(retriever, "STUB") in /health is live
    if name == "STUB":
        return not os.path.isdir(config.CHROMA_DIR)
    raise AttributeError(name)


def _get():
    """Load the embedding model and Chroma collection once, on first use."""
    global _retriever
    with _lock:
        if _retriever is None:
            from .retrieve import Retriever  # heavy imports (chromadb, sentence-transformers)

            t0 = time.perf_counter()
            _retriever = Retriever(chroma_dir=str(config.CHROMA_DIR))
            log.info("guideline index loaded in %.1fs (%d chunks)", time.perf_counter() - t0, _retriever.total)
        return _retriever


def _manifest_id(cid: str) -> Optional[str]:
    from .manifest import CONDITIONS

    mid = COND_MAP.get(cid, cid)
    return mid if mid in CONDITIONS else None


def _as_condition_id(value: Optional[str]) -> Optional[str]:
    """Accept an app id or its display name (the UI tags passages with the name)."""
    if not value:
        return None
    if value in APP_CONDITIONS:
        return value
    low = value.strip().lower()
    for cid, name in APP_CONDITIONS.items():
        if name.lower() == low:
            return cid
    return None


def _location(meta: dict) -> str:
    a, b = meta.get("page_start") or 0, meta.get("page_end") or 0
    if not a:
        return ""
    return f"p. {a}" if not b or a == b else f"pp. {a}-{b}"


def _title(meta: dict) -> str:
    stem = os.path.splitext(meta.get("source_file") or "")[0]
    return re.sub(r"[_\-]+", " ", stem).strip() or "Guideline document"


def _body(meta: dict) -> Optional[str]:
    issuer = str(meta.get("issuer") or "").strip()
    return {"ICMR": "ICMR", "MOHFW": "MoHFW"}.get(issuer.upper()) if issuer.upper() in _BODIES else None


def _key(hit: dict) -> str:
    m = hit["meta"]
    raw = f"{m.get('source_file')}|{m.get('page_start')}|{' '.join(hit['text'].split())[:200]}"
    return hashlib.sha1(raw.encode()).hexdigest()


def _passage(hit: dict, cid: str, content_type: str) -> dict:
    m = hit["meta"]
    return {
        "text": hit["text"],
        "file": m.get("source_file"),
        "location": _location(m),
        "title": _title(m),
        "body": _body(m),
        "disease": cid,
        "content_type": content_type,
        "relevance": round(max(0.0, min(1.0, hit["score"])), 3),
    }


def retrieve(shortlist: list[str], query: str) -> dict:
    """Passages for each shortlisted condition and content type (see module docstring)."""
    r = _get()
    case = " ".join((query or "").split())[:_CASE_CHARS]
    passages: list[dict] = []
    filters: list[dict] = []
    seen: set[str] = set()
    dropped = 0
    skipped: list[str] = []

    for cid in shortlist:
        mid = _manifest_id(cid)
        if mid is None:
            skipped.append(cid)
            continue
        for ct in CONTENT_TYPES:
            if ct == "confirmatory_tests" and config.TESTS_FROM_PROTOCOL:
                continue  # tests come from the fixed protocol document
            q = _INTENT[ct].format(name=condition_name(cid))
            if ct == "clinical_features" and case:
                q += " " + case
            filters.append({"disease": cid, "content_type": ct})
            for hit in r.search(q, [mid], n=config.CHUNKS_PER_SECTION):
                if hit["score"] < config.RELEVANCE_FLOOR:
                    dropped += 1
                    continue
                k = _key(hit)
                if k in seen:  # the same chunk can answer two intents; keep the first
                    continue
                seen.add(k)
                passages.append(_passage(hit, cid, ct))

    if skipped:
        log.warning("no index tag for condition id(s) %s; fix MANIFEST_NAMES in app/conditions.py", skipped)
    return {
        "passages": passages,
        "chunk_count": len(passages) + dropped,
        "dropped_below_threshold": dropped,
        "documents_in_index": document_count(),
        "filters": filters,
    }


def search(query: str, disease: Optional[str] = None, content_type: Optional[str] = None) -> list[dict]:
    """Free search box (POST /search). `disease` narrows to one condition; `content_type` steers
    the query toward that kind of passage (it is not a stored tag)."""
    from .manifest import CONDITIONS

    r = _get()
    cid = _as_condition_id(disease)
    if disease and cid is None:
        return []
    if cid:
        mid = _manifest_id(cid)
        if mid is None:
            return []
        scope = [mid]
    else:
        scope = [c for c in CONDITIONS if c != "general"] or list(CONDITIONS)

    q = (query or "").strip()
    if content_type in _INTENT and cid:
        q = f"{_INTENT[content_type].format(name=condition_name(cid))} {q}"
    out = []
    for h in r.search(q, scope, n=8):
        m = h["meta"]
        primary = _FROM_MANIFEST.get(m.get("condition")) or _as_condition_id(m.get("condition"))
        out.append({
            "text": h["text"],
            "source": m.get("source_file") or "",
            "distance": h["distance"],
            "disease": condition_name(cid or primary) if (cid or primary) else None,
            "content_type": content_type if content_type in CONTENT_TYPES else None,
            "body": _body(m),
            "location": _location(m),
        })
    return out


def document_count() -> int:
    """Distinct guideline files in the index (sidebar counter)."""
    r = _get()
    if not hasattr(r, "_doc_count"):
        metas = r.col.get(include=["metadatas"])["metadatas"]
        r._doc_count = len({m.get("source_file") for m in metas if m.get("source_file")})
    return r._doc_count


def last_indexed() -> str:
    """When the index was last rebuilt, e.g. 'Today, 14:32'."""
    db = os.path.join(config.CHROMA_DIR, "chroma.sqlite3")
    try:
        ts = os.stat(db).st_mtime
    except OSError:
        return "Not indexed"
    t = time.localtime(ts)
    day = "Today" if time.strftime("%Y%m%d", t) == time.strftime("%Y%m%d") else time.strftime("%d %b %Y", t)
    return f"{day}, {time.strftime('%H:%M', t)}"
