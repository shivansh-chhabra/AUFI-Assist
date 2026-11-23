"""STAGE 2: retrieval over the ChromaDB guideline store.   >>> YOUR FRIEND FILLS THIS IN <<<

Delete the line `STUB = True` once implemented (/health reads it).
Condition ids must be the ones in app/conditions.py.
"""
from typing import Optional

STUB = True


def retrieve(shortlist: list[str], query: str) -> dict:
    """Retrieve guideline passages restricted to the shortlisted conditions.

    Args:
        shortlist: condition ids from the scoring stage, e.g. ["dengue", "chikungunya", "malaria"]
        query: a short natural-language description of the case (built by the backend from the
               patient's answers).

    Return shape (only real guideline text, nothing generated):
        {
          "passages": [
            {
              "text": "…chunk text…",
              "file": "icmr_dengue_2023.pdf",   # filename inside data/guidelines/
              "location": "pp. 12-13",           # page range shown on the source card
              "title": "ICMR Dengue Guidelines", # optional, defaults to file
              "body": "ICMR",                    # optional: "ICMR" | "MoHFW"
              "disease": "dengue",               # condition id the chunk is tagged with
              "content_type": "clinical_features",  # clinical_features | confirmatory_tests | treatment
              "relevance": 0.83,                 # optional 0..1 after reranking
            },
          ],
          "chunk_count": 6,                      # optional
          "dropped_below_threshold": 4,          # optional
          "documents_in_index": 14,              # optional
          "filters": [{"disease": "dengue", "content_type": "clinical_features"}],  # optional
        }
    Return "passages": [] if nothing clears the relevance threshold; the UI then says no
    medical claim is made.
    """
    raise NotImplementedError("rag.retriever.retrieve")


def search(query: str, disease: Optional[str] = None, content_type: Optional[str] = None) -> list[dict]:
    """Free search box in the UI (POST /search). Return a list of:
        {"text", "source" (filename), "distance" (0 = identical), "disease", "content_type",
         "body", "location"}
    """
    raise NotImplementedError("rag.retriever.search")


def document_count() -> int:
    """How many guideline documents are indexed (sidebar counter)."""
    raise NotImplementedError("rag.retriever.document_count")


def last_indexed() -> str:
    """Human-readable time of the last ingestion, e.g. "Today, 14:32"."""
    raise NotImplementedError("rag.retriever.last_indexed")
