"""
ingest.py -- AUFI guideline corpus ingestion (adapted from the SIH26117 ingest script).
Lives in backend/app/rag/. Run it from backend/ with `python -m app.rag.ingest`.

SETUP
-----
pip install chromadb sentence-transformers pymupdf langchain-text-splitters

USAGE
-----
python -m app.rag.ingest --dump      # write cleaned text per manifest entry to ./dump/ (no embedding) -- eyeball it
python -m app.rag.ingest --dry-run   # chunk + print the report, no embedding, nothing stored
python -m app.rag.ingest             # full ingest into a NEW collection/dir (does not touch the SIH Chroma DB)

WHAT CHANGED vs THE SIH SCRIPT, AND WHY
---------------------------------------
1. Manifest-driven (manifest.py) instead of os.listdir(): only listed files and
   page ranges are ingested, so duplicates and out-of-scope pages can't sneak in.
2. Every chunk carries condition metadata (c_<id>=True flags + a primary
   "condition") and provenance (file, issuer, year, region, page_start/end).
3. Header/footer stripping is now PAGE-EDGE based. The old version dropped any
   line repeating 4+ times after replacing digits with '#', which would also
   delete table/dosing lines ("250 mg", "10 mg/kg/day" -> "# mg ...") in
   medical tables. This one only removes repeated lines at the top/bottom of
   pages.
4. PyMuPDF text extraction instead of pypdf (cleaner on the tables in the WHO
   and NZ files in my tests; I did not test pypdf on them).
5. Exact-duplicate chunks are dropped; a token-length check warns if chunks are
   longer than the embedding model's max sequence length (silent truncation).
6. New collection name + directory, because the old script deletes its
   collection on every run.
(The old docstring described numbered-rule chunking, but the code actually used
RecursiveCharacterTextSplitter -- still does, which is fine for these docs.)
"""

import argparse
import hashlib
import os
import re
import sys
from collections import Counter

from .. import config
from .manifest import CONDITIONS, MANIFEST

BASE = os.path.dirname(os.path.abspath(__file__))
# Guideline PDFs: the same folder the source-preview modal serves (AUFI_KB_DOCS_DIR).
DOCS_DIR = str(config.KB_DOCS_DIR)
CHROMA_DIR = str(config.CHROMA_DIR)                 # AUFI_CHROMA_DIR
DUMP_DIR = os.path.join(BASE, "dump")
COLLECTION_NAME = "aufi_guidelines"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

CHUNK_TOKENS = 220
CHUNK_OVERLAP_TOKENS = 30
MIN_CHUNK_CHARS = 60

PAGE_MARK = "@@PAGE{}@@"
PAGE_RE = re.compile(r"@@PAGE(\d+)@@")


# ---------------------------------------------------------------- extraction
def extract_pages(path: str) -> list:
    """Returns a list of page texts (index 0 = page 1). .txt/.md = one page."""
    ext = os.path.splitext(path)[1].lower()
    if ext != ".pdf":
        with open(path, "r", encoding="utf-8") as f:
            return [f.read()]
    try:
        import pymupdf
    except ImportError:          # older PyMuPDF releases
        import fitz as pymupdf
    pages = []
    with pymupdf.open(path) as doc:
        for page in doc:
            pages.append(page.get_text("text", sort=True))
    return pages
 
 
def strip_page_furniture(pages: list, edge_lines: int = 2,
                         min_pages: int = 4, min_frac: float = 0.1,
                         removed: Counter = None) -> list:
    """
    Removes running headers/footers/page numbers: lines in the first or last
    `edge_lines` non-blank lines of a page whose digit-normalised form shows up
    at the page edge on at least max(min_pages, min_frac * n_pages) pages.
    Lines in the body of a page are never touched. min_frac is low (0.1)
    because running footers often change per chapter, so each variant only
    appears on a fraction of a long document's pages. Pass a Counter as
    `removed` to collect what was stripped.
    """
    def norm(line):
        return re.sub(r"\s+", " ", re.sub(r"\d+", "#", line.strip()))
 
    edge_info = []          # per page: (lines, set of edge line indexes)
    counts = Counter()
    for text in pages:
        lines = text.split("\n")
        nonblank = [i for i, ln in enumerate(lines) if ln.strip()]
        edge = set(nonblank[:edge_lines] + nonblank[-edge_lines:])
        edge_info.append((lines, edge))
        for n in {norm(lines[i]) for i in edge}:
            counts[n] += 1
 
    threshold = max(min_pages, int(min_frac * len(pages)))
    cleaned = []
    for lines, edge in edge_info:
        kept = []
        for i, ln in enumerate(lines):
            if i in edge and counts[norm(ln)] >= threshold:
                if removed is not None:
                    removed[norm(ln)] += 1
                continue
            kept.append(ln)
        cleaned.append("\n".join(kept))
    return cleaned
 
 
def assemble(pages: list, ranges, label: str, warnings: list) -> str:
    """Joins the selected pages, each prefixed with a page marker."""
    n = len(pages)
    if ranges is None:
        ranges = [(1, n)]
    parts = []
    for a, b in ranges:
        if a < 1 or b > n or a > b:
            warnings.append(f"{label}: page range ({a},{b}) outside 1..{n}; clipped")
        for p in range(max(a, 1), min(b, n) + 1):
            parts.append(f"{PAGE_MARK.format(p)}\n{pages[p - 1].strip()}")
    return "\n\n".join(parts)
 
 
def apply_cuts(text: str, cuts, label: str, warnings: list) -> str:
    for start_re, end_re in cuts or []:
        m1 = re.search(start_re, text, re.I | re.S)
        if not m1:
            warnings.append(f"{label}: cut start not found: {start_re}")
            continue
        m2 = re.search(end_re, text[m1.end():], re.I | re.S)
        if not m2:
            warnings.append(f"{label}: cut end not found after start: {end_re}")
            continue
        cut_from, cut_to = m1.start(), m1.end() + m2.start()
        # keep any page markers inside the removed span, or the text after the
        # cut would be attributed to the wrong (earlier) page
        kept_marks = "\n".join(m.group(0) for m in PAGE_RE.finditer(text[cut_from:cut_to]))
        text = text[:cut_from] + "\n\n" + kept_marks + "\n\n" + text[cut_to:]
    return text
 
 
# ------------------------------------------------------------------ chunking
_tokenizer = None
 
 
def token_len(text: str) -> int:
    """Token count under the embedding model's tokenizer (loaded once, cached by HF)."""
    global _tokenizer
    if _tokenizer is None:
        from transformers import AutoTokenizer
        name = EMBEDDING_MODEL if "/" in EMBEDDING_MODEL else f"sentence-transformers/{EMBEDDING_MODEL}"
        _tokenizer = AutoTokenizer.from_pretrained(name)
        _tokenizer.model_max_length = 10 ** 6        # silence the long-input warning
    return len(_tokenizer.encode(text, add_special_tokens=False))
 
 
def chunk_entry(entry: dict, text: str) -> list:
    from langchain_text_splitters import RecursiveCharacterTextSplitter   # lazy: only needed when ingesting
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_TOKENS,
        chunk_overlap=CHUNK_OVERLAP_TOKENS,
        length_function=token_len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    docs = splitter.create_documents([text])
    marks = [(m.start(), int(m.group(1))) for m in PAGE_RE.finditer(text)]
 
    def page_at(pos):
        last = None
        for s_, p_ in marks:
            if s_ <= pos:
                last = p_
            else:
                break
        return last
 
    chunks, pos = [], 0
    for d in docs:
        # NOTE: LangChain's add_start_index is NOT used: with a token-based
        # length_function it treats the overlap as characters and returns wrong
        # offsets (36 of 122 chunks in my test), which would corrupt page numbers.
        start = text.find(d.page_content, pos)
        if start == -1:
            start = text.find(d.page_content)
        if start == -1:
            start = pos
        pos = start + 1
        end = start + len(d.page_content)
        ps, pe = page_at(start), page_at(max(start, end - 1))
        clean = PAGE_RE.sub("", d.page_content)
        clean = re.sub(r"[ \t]+\n", "\n", clean)
        clean = re.sub(r"\n{3,}", "\n\n", clean).strip()
        if len(clean) < MIN_CHUNK_CHARS:
            continue
        chunks.append({"text": clean, "page_start": ps, "page_end": pe, "entry": entry})
    return chunks
 
 
def flag_key(condition: str) -> str:
    """Metadata key for a condition flag, e.g. 'Hepatitis A/E' -> 'c_hepatitis_a_e'.
    Sanitised so odd characters in display names can't cause trouble."""
    return "c_" + re.sub(r"\W+", "_", condition).strip("_").lower()
 
 
_keys = {}
for _c in CONDITIONS:
    _k = flag_key(_c)
    if _k in _keys:
        raise ValueError(f"conditions '{_keys[_k]}' and '{_c}' produce the same flag key '{_k}'")
    _keys[_k] = _c
 
 
def build_metadata(entry: dict, page_start, page_end) -> dict:
    conds = entry["conditions"]
    meta = {
        "condition": conds[0],                       # primary tag
        "source_file": entry["file"],
        "issuer": entry.get("issuer", "unknown"),
        "year": int(entry.get("year", 0)),           # 0 = unknown
        "region": entry.get("region", "unknown"),
        "age_group": entry.get("age_group", "unknown"),   # adult | paediatric | all | unknown
        "page_start": int(page_start or 0),          # PDF page index, 1-based
        "page_end": int(page_end or 0),
    }
    for c in conds:                                  # one boolean flag per condition
        meta[flag_key(c)] = True
    return meta
 
 
def condition_filter(conditions, include_general: bool = False):
    """
    Chroma `where` filter for a shortlist of condition ids, e.g.
        collection.query(query_embeddings=..., n_results=8,
                         where=condition_filter(["dengue", "chikungunya"]))
    Filter on the whole shortlist, not just the top-1 prediction.
    """
    ids = list(conditions) + (["general"] if include_general else [])
    unknown = [c for c in ids if c not in CONDITIONS]
    if unknown:
        raise ValueError(f"unknown condition id(s) {unknown}; a typo here would silently "
                         f"match nothing. Valid ids: {sorted(CONDITIONS)}")
    flags = [{flag_key(c): True} for c in ids]
    return flags[0] if len(flags) == 1 else {"$or": flags}
 
 
# ------------------------------------------------------------------ pipeline
def validate_manifest() -> list:
    problems = []
    for e in MANIFEST:
        for c in e.get("conditions", []):
            if c not in CONDITIONS:
                problems.append(f"{e['file']}: unknown condition id '{c}'")
        if not e.get("conditions"):
            problems.append(f"{e['file']}: no conditions")
        if e.get("issuer", "unknown") == "unknown" or not e.get("year"):
            problems.append(f"{e['file']}: issuer/year not filled in (provenance incomplete)")
    return problems
 
 
def prepare_chunks(dump: bool = False):
    warnings = validate_manifest()
    all_chunks, seen, dups = [], {}, 0
 
    if dump:
        os.makedirs(DUMP_DIR, exist_ok=True)
 
    for idx, entry in enumerate(MANIFEST):
        label = entry["file"]
        if not entry.get("enabled", True):
            print(f"  [skip] {label} (enabled=False)")
            continue
        path = os.path.join(DOCS_DIR, entry["file"])
        if not os.path.isfile(path):
            warnings.append(f"{label}: file not found in {DOCS_DIR} -- skipped")
            continue
 
        pages = extract_pages(path)
        if sum(len(p.strip()) for p in pages) < 50:
            warnings.append(f"{label}: almost no text extracted (scanned PDF? needs OCR) -- skipped")
            continue
 
        stripped = Counter()
        pages = strip_page_furniture(pages, removed=stripped)
        if stripped:
            top = ", ".join(f"'{k[:40]}' x{v}" for k, v in stripped.most_common(3))
            print(f"  {label}: stripped page furniture, e.g. {top}")
        sel = entry.get("pages") or [(1, len(pages))]
        blank = [pg for a, b in sel for pg in range(max(a, 1), min(b, len(pages)) + 1)
                 if len(pages[pg - 1].strip()) < 40]
        if blank:
            warnings.append(f"{label}: {len(blank)} selected page(s) with almost no text "
                            f"(scanned/image-only? may need OCR): {blank[:15]}")
        text = assemble(pages, entry.get("pages"), label, warnings)
        text = apply_cuts(text, entry.get("cut"), label, warnings)
 
        if dump:
            out = os.path.join(DUMP_DIR, f"{idx:02d}_{os.path.splitext(label)[0]}.txt")
            with open(out, "w", encoding="utf-8") as f:
                f.write(text)
 
        kept = 0
        for ch in chunk_entry(entry, text):
            key = hashlib.sha1(re.sub(r"\s+", " ", ch["text"].lower()).encode()).hexdigest()
            if key in seen:
                dups += 1
                warnings.append(f"duplicate chunk dropped: {label} p{ch['page_start']} "
                                f"(already from {seen[key]})")
                continue
            seen[key] = label
            ch["entry_idx"] = idx
            all_chunks.append(ch)
            kept += 1
        print(f"  {label}: {kept} chunks")
 
    # files sitting in the docs folder that the manifest doesn't mention
    # (manifest-only ingestion means these would otherwise be ignored silently)
    listed = {e["file"] for e in MANIFEST}
    if os.path.isdir(DOCS_DIR):
        for fn in sorted(os.listdir(DOCS_DIR)):
            if (fn not in listed and not fn.startswith(".")
                    and os.path.splitext(fn)[1].lower() in (".pdf", ".txt", ".md")):
                warnings.append(f"{fn}: in the docs folder but NOT in the manifest -- not ingested "
                                f"(add an entry, or fix a file-name mismatch)")
 
    return all_chunks, warnings
 
 
def report(chunks: list, warnings: list):
    print("\n=== REPORT ===")
    per_cond = Counter()
    for ch in chunks:
        for c in ch["entry"]["conditions"]:
            per_cond[c] += 1
    print("Chunks per condition:")
    for c in sorted(CONDITIONS):
        n = per_cond.get(c, 0)
        flag = "   <-- NONE" if n == 0 and c != "general" else ""
        print(f"  {c:22s} {n}{flag}")
    print("Chunks per source file:")
    for f, n in Counter(ch["entry"]["file"] for ch in chunks).most_common():
        print(f"  {f}: {n}")
    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print("  -", w)
 
 
def ingest(dry_run: bool = False, dump: bool = False):
    print("Preparing chunks...")
    chunks, warnings = prepare_chunks(dump=dump)
    if not chunks:
        report(chunks, warnings)
        print("No usable chunks -- check DOCS_DIR and the manifest.")
        return
    if dump:
        print(f"Cleaned text written to {DUMP_DIR}")
 
    if dry_run or dump:
        report(chunks, warnings)
        return
 
    from sentence_transformers import SentenceTransformer
    import chromadb
 
    print("Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    limit = model.max_seq_length
    token_counts = [len(ids) for ids in
                    model.tokenizer([c["text"] for c in chunks],
                                    add_special_tokens=True)["input_ids"]]
    too_long = sum(1 for n in token_counts if n > limit)
    if too_long:
        warnings.append(f"{too_long}/{len(chunks)} chunks exceed the model's max sequence "
                        f"length ({limit} tokens) and will be silently truncated when embedded "
                        f"-- lower CHUNK_TOKENS")
 
    report(chunks, warnings)
 
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
 
    texts = [c["text"] for c in chunks]
    print(f"\nEmbedding {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True)
 
    ids = [f"e{c['entry_idx']:02d}_{i:05d}" for i, c in enumerate(chunks)]
    metas = [build_metadata(c["entry"], c["page_start"], c["page_end"]) for c in chunks]
    collection.add(ids=ids, embeddings=embeddings.tolist(), documents=texts, metadatas=metas)
    print(f"Done. {len(chunks)} chunks stored in {CHROMA_DIR} (collection '{COLLECTION_NAME}')")
 
 
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", action="store_true", help="write cleaned per-entry text to ./dump/ and stop")
    ap.add_argument("--dry-run", action="store_true", help="chunk and report only")
    args = ap.parse_args()
    ingest(dry_run=args.dry_run, dump=args.dump)
