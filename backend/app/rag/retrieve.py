"""
retrieve.py -- retrieval over the collection built by ingest.py (backend/app/rag/).

It reuses CHROMA_DIR / COLLECTION_NAME / EMBEDDING_MODEL / condition_filter() from
ingest.py, so the filter keys (c_<id> flags) can never drift from ingestion.

USAGE (CLI)
-----------
python -m app.rag.retrieve "fever with retro-orbital pain and rash" --cond dengue chikungunya -n 4
python -m app.rag.retrieve --check          # smoke test: every condition has chunks + a sane top hit

USAGE (from agent.py / pipeline.py)
-----------------------------------
    from app.rag.retrieve import make_retriever
    retriever = make_retriever(args)            # args needs: model, prefix, chroma_dir, collection, general (all optional)
    hits = retriever("dengue: warning signs", "dengue")          # one condition id
    hits = retriever("fever with rash", ["dengue", "chikungunya"])  # shortlist (OR filter)
    # hits = [{"text", "meta", "distance", "score"}, ...] best first; "meta" has source_file, page_start, ...

The retriever callable has the signature agent.py expects: (query, conditions) -> list of dicts
with "text" and "meta".

NOTES
-----
* Query and passage embeddings must use the same model (and the same prefix convention).
  ingest.py adds NO prefix to passages, so keep --prefix empty unless you add the
  matching passage prefix at ingest time (e5/bge-style models need one on both sides).
* Adjacent chunks overlap (CHUNK_OVERLAP_TOKENS), so we over-fetch and drop near-duplicates
  before returning the top n.
"""

import argparse
import os
import re
import sys

from .ingest import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL, condition_filter
from .manifest import CONDITIONS

__all__ = ["CHROMA_DIR", "COLLECTION_NAME", "EMBEDDING_MODEL", "Retriever", "make_retriever"]

_WORD = re.compile(r"\w+")
_MODEL_CACHE = {}


def _words(text: str) -> set:
    return set(_WORD.findall(text.lower()))


def _jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def _as_ids(conditions) -> list:
    """Accepts 'dengue', ['dengue', 'malaria'], a set, etc. Returns a de-duplicated list."""
    if conditions is None:
        raise ValueError("no condition given (None); pass a condition id or a list of ids")
    if isinstance(conditions, str):
        conditions = [conditions]
    ids = list(dict.fromkeys(conditions))
    if not ids:
        raise ValueError("empty condition list")
    return ids


class Retriever:
    def __init__(self, chroma_dir=CHROMA_DIR, collection=COLLECTION_NAME,
                 model=EMBEDDING_MODEL, prefix="", include_general=False, device=None):
        import chromadb
        from sentence_transformers import SentenceTransformer

        if not os.path.isdir(chroma_dir):
            raise FileNotFoundError(f"Chroma directory not found: {chroma_dir} "
                                    f"(run `python -m app.rag.ingest` first, or pass chroma_dir)")
        client = chromadb.PersistentClient(path=chroma_dir)
        try:
            self.col = client.get_collection(collection)
        except Exception as e:
            raise RuntimeError(f"collection '{collection}' not found in {chroma_dir}: {e}") from e

        built_with = (self.col.metadata or {}).get("embedding_model")
        if built_with and built_with != model:
            raise ValueError(f"collection was built with '{built_with}' but retrieval asked for '{model}'")

        self.total = self.col.count()
        if self.total == 0:
            raise RuntimeError(f"collection '{collection}' in {chroma_dir} is empty")

        key = (model, device)
        if key not in _MODEL_CACHE:
            _MODEL_CACHE[key] = SentenceTransformer(model, device=device)
        self.model = _MODEL_CACHE[key]
        self.prefix = prefix
        self.include_general = include_general

    def search(self, query, conditions, n=3, include_general=None, overfetch=4, dedupe=0.8):
        """Top-n chunks for `query`, restricted to chunks tagged with ANY of `conditions`."""
        query = (query or "").strip()
        if not query:
            return []
        ids = _as_ids(conditions)
        if include_general is None:
            include_general = self.include_general
        where = condition_filter(ids, include_general=include_general and "general" in CONDITIONS)

        emb = self.model.encode([self.prefix + query]).tolist()
        k = max(1, min(n * overfetch, self.total))
        res = self.col.query(query_embeddings=emb, n_results=k, where=where,
                             include=["documents", "metadatas", "distances"])
        docs, metas, dists = res["documents"][0], res["metadatas"][0], res["distances"][0]

        hits, kept_words = [], []
        for text, meta, dist in zip(docs, metas, dists):      # already best-first
            w = _words(text)
            if any(_jaccard(w, kw) >= dedupe for kw in kept_words):
                continue
            kept_words.append(w)
            hits.append({"text": text, "meta": meta, "distance": float(dist), "score": 1.0 - float(dist)})
            if len(hits) >= n:
                break
        return hits


def make_retriever(args):
    """Build a retriever(query, conditions) callable from an argparse namespace (all fields optional)."""
    r = Retriever(chroma_dir=getattr(args, "chroma_dir", None) or CHROMA_DIR,
                  collection=getattr(args, "collection", None) or COLLECTION_NAME,
                  model=getattr(args, "model", None) or EMBEDDING_MODEL,
                  prefix=getattr(args, "prefix", "") or "",
                  include_general=bool(getattr(args, "general", False)))
    n_default = int(getattr(args, "n_chunks", 3) or 3)

    def retrieve(query, conditions, n=None):
        return r.search(query, conditions, n=n or n_default)

    retrieve.retriever = r
    return retrieve


# ---------------------------------------------------------------- CLI
def _show(hits, width=400):
    if not hits:
        print("  (no hits)")
    for i, h in enumerate(hits, 1):
        m = h["meta"]
        src = f"{m.get('source_file', '?')} p{m.get('page_start', '?')}-{m.get('page_end', '?')}"
        print(f"[{i}] sim={h['score']:.3f}  {m.get('condition', '?')}  ({src}, {m.get('issuer', '?')} {m.get('year', '?')})")
        print("    " + " ".join(h["text"].split())[:width])


def _check(r):
    print(f"{r.total} chunks in collection\n")
    empty = []
    for c in sorted(CONDITIONS):
        hits = r.search(c.replace("_", " ") + " clinical features and diagnosis", [c], n=3)
        top = f"{hits[0]['score']:.3f}" if hits else "-"
        print(f"  {c:22s} hits={len(hits)}  top_sim={top}")
        if not hits and c != "general":
            empty.append(c)
    if empty:
        print(f"\nNO CHUNKS for: {', '.join(empty)}  (check manifest page ranges / enabled flags)")
        return 1
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Query the AUFI guideline collection.")
    ap.add_argument("query", nargs="?")
    ap.add_argument("--cond", nargs="+", help="condition id(s) to restrict to (manifest ids)")
    ap.add_argument("-n", type=int, default=3)
    ap.add_argument("--general", action="store_true", help="also include chunks tagged 'general'")
    ap.add_argument("--prefix", default="")
    ap.add_argument("--model", default=EMBEDDING_MODEL)
    ap.add_argument("--chroma-dir", default=CHROMA_DIR)
    ap.add_argument("--collection", default=COLLECTION_NAME)
    ap.add_argument("--check", action="store_true", help="smoke-test every condition and exit")
    a = ap.parse_args(argv)

    r = Retriever(a.chroma_dir, a.collection, a.model, a.prefix, a.general)
    if a.check:
        sys.exit(_check(r))
    if not a.query or not a.cond:
        ap.error("give a query and --cond (or use --check)")
    _show(r.search(a.query, a.cond, n=a.n))


if __name__ == "__main__":
    main()