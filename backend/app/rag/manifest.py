"""TEMPLATE -- replace this file with your friend's real manifest.py.

ingest.py and retrieve.py import `CONDITIONS` and `MANIFEST` from here, and your friend's copy was
not in the files you sent. This template only lets the app import cleanly; with an empty MANIFEST,
`python -m app.rag.ingest` finds nothing to index.

CONDITIONS: every condition id the index is tagged with (the 11 app ids, plus optionally "general"
            for background chapters). If your friend used different ids, either rename them to match
            app/conditions.py or fill COND_MAP in app/rag/retriever.py.
MANIFEST:   one dict per guideline file (file name must exist in data/guidelines/):
    {
        "file": "icmr_dengue_2023.pdf",
        "conditions": ["dengue"],            # first one is the primary tag
        "issuer": "ICMR",                    # "ICMR" / "MoHFW" show as badges in the UI
        "year": 2023,
        "region": "India",
        "age_group": "all",                  # adult | paediatric | all | unknown
        "pages": [(5, 40)],                  # optional 1-based inclusive page ranges
        "cut": [],                           # optional (start_regex, end_regex) removals
        "enabled": True,
    },
"""
from ..conditions import CONDITIONS as _APP_CONDITIONS

CONDITIONS = {**_APP_CONDITIONS, "general": "General background"}

MANIFEST: list = []
