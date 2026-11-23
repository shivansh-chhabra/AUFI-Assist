"""
manifest.py -- the single place that decides which pages of which file get
ingested, and which condition(s) they are tagged with.

RULES
-----
* "conditions" must use the SAME ids as the condition column of your scoring
  CSV, so the scoring layer's shortlist can be used directly as a retrieval
  filter. CONDITIONS below is a PLACEHOLDER set -- edit it to match the CSV.
* "pages" are 1-indexed PDF page numbers (NOT the printed page numbers).
  Inclusive ranges. None = whole file. Check the offset per file; they differ.
* "cut" removes text from the first match of start_regex up to (not
  including) the first match of end_regex, within the selected pages. Use it
  to drop in-page sections you don't want (e.g. "Implementation
  considerations"). The ingest script warns if a cut doesn't match.
* "enabled": False keeps an entry on file without ingesting it. Anything not
  listed here is NOT ingested (no silent os.listdir() pickup, so duplicates
  and out-of-scope files can't sneak in).
* Multi-disease files: list only the in-scope page ranges. Excluding a page
  is safer than tagging it "other" -- an untagged chunk silently never
  appears under a condition filter.
* issuer/year/region are provenance metadata. "unknown" / 0 = not filled in
  yet. Fill them in -- the explanation layer needs them to cite sources and
  to notice when two sources disagree.
"""

CONDITIONS = {
    "Malaria (P. vivax/falciparum)",
    "Dengue (incl. hemorrhagic)",
    "Typhoid fever",
    "Scrub/murine typhus",
    "Leptospirosis",
    "Chikungunya",
    "Viral ILI",
    "Hepatitis A/E",
    "Occult bacteremia (pneumonia/UTI-pyelo/intra-abdominal)",
    "Rheumatic Fever",
    "TB (prolonged fever)",
    "general",          # cross-condition material (e.g. the 2019 treatment guidelines)
}

MANIFEST = [
    # ---- single-disease files: whole file, one tag ------------------------
    {"file": "malaria.pdf", "conditions": ["Malaria (P. vivax/falciparum)"],
     "issuer": "MoHFW", "year": 2013, "region": "unknown"},
    {"file": "dengue.pdf", "conditions": ["Dengue (incl. hemorrhagic)"],
     "issuer": "MoHFW", "year": 2023, "region": "unknown"},
    {"file": "chikungunya.pdf", "conditions": ["Chikungunya"],
     "issuer": "MoHFW", "year": 2023, "region": "unknown"},
    {"file": "Enteric Fever(Typhoid).pdf", "conditions": ["Typhoid fever"],
     "issuer": "IAP", "year": 2022, "region": "unknown"},
    {"file": "leptosiprosis.pdf", "conditions": ["Leptospirosis"],
     "issuer": "NCDC", "year": 2015, "region": "unknown"},
    {"file": "Influenza.pdf", "conditions": ["Viral ILI"],
     "issuer": "unknown", "year": 2019, "region": "unknown"},
    {"file": "TB.pdf", "conditions": ["TB (prolonged fever)"],
     "issuer": "WHO", "year": 2016, "region": "unknown"},
    {"file": "Tuberculosis_treatment.pdf", "conditions": ["TB (prolonged fever)"],
     "issuer": "unknown", "year": 2015, "region": "unknown"},

    # Check this against the DHR-ICMR rickettsial file before enabling both:
    # if they overlap heavily, ingest only one (near-duplicate chunks crowd
    # out top-k). Exact-duplicate chunks are dropped automatically.
    {"file": "ricketsial disease.pdf", "conditions": ["Scrub/murine typhus"],
     "issuer": "ICMR", "year": 2015, "region": "unknown"},
    {"file": "icrm_ricketssial.pdf", "conditions": ["Scrub/murine typhus"],
     "issuer": "ICMR", "year": 2015, "region": "unknown"},
    # ---- standalone general-queries source --------------------------------

    {"file": "Treatment_Guidelines_2019_Final.pdf",
    "conditions": ["general", "Occult bacteremia (pneumonia/UTI-pyelo/intra-abdominal)"],
    "pages": [(35 + 5, 54 + 5), (86 + 5, 92 + 5)],
    "issuer": "ICMR", "year": 2019, "region": "unknown"},

    {"file": "Treatment_Guidelines_2019_Final.pdf",
    "conditions": ["general"],
    "pages": [(1 + 5, 34 + 5)],
    "issuer": "ICMR", "year": 2019, "region": "unknown"},

    # ---- multi-disease: needs in-scope page ranges first ------------------
    {"file": "diagnosis-management-viral-hepatitis.pdf",
     "conditions": ["Hepatitis A/E"],
     "pages": ((16, 18), (44, 47)),          # TODO: set to the hepatitis A/E ranges from the TOC
     "enabled": True,       # flip to True once pages is set
     "issuer": "unknown", "year": 0, "region": "unknown"},

    # ---- rheumatic fever --------------------------------------------------
    # WHO 2024 (PDF page = printed page + 20). 21-23 = introduction;
    # 38-55 = sections 4.5 (diagnosis) to 4.8 (anti-inflammatory agents).
    # The cuts drop the "Implementation considerations" and "research gaps"
    # subsections (health-system content, out of scope).
    {"file": "rheumatic_fever.pdf", "conditions": ["Rheumatic Fever"],
     "issuer": "WHO", "year": 2024, "region": "global",
     "pages": [(21, 23), (38, 55)],
     "cut": [
         (r"4\.5\.2\s+Implementation considerations", r"4\.5\.3\s+Summary of the evidence"),
         (r"4\.5\.4\s+Guideline-related research gaps", r"4\.6\s+Echocardiography"),
         (r"4\.6\.2\s+Implementation considerations", r"4\.6\.3\s+Summary of the evidence"),
         (r"4\.6\.4\s+Guideline-related research gaps", r"4\.7\s+Antibiotic prophylaxis"),
         (r"4\.7\.3\s+Implementation considerations", r"4\.7\.5\s+Summary of the evidence"),
         (r"4\.8\.3\s+Implementation considerations", r"4\.8\.5\s+Summary of the evidence"),
     ]},

    # IAP 2008 consensus guideline (Indian Pediatrics 45:565-573); PDF page =
    # printed page - 564. Save the download under this file name.
    # Sections 3-4 (heart failure, AF, valve surgery, Tables IV-VI) are out of
    # scope; add "cut" entries for them after checking the --dump output.
    {"file": "acute_rheumatic_fever.pdf",
     "conditions": ["Rheumatic Fever"],
     "issuer": "IAP", "year": 2008, "region": "India",
     "pages": [(1, 7)]},

    # NZ Heart Foundation 2014: OPT-IN ONLY. Uses NZ-specific criteria and
    # cutoffs (e.g. ASO >=480) that conflict with WHO/MoHFW/IAP. Pages below
    # are descriptive clinical features (Table 5) and the investigations
    # table (Table 11); check --dump for NZ thresholds before enabling.
    {"file": "diagnosis-management-rheumatic-fever-guideline.pdf",
     "conditions": ["Rheumatic Fever"],
     "issuer": "NZ Heart Foundation", "year": 2014, "region": "NZ",
     "pages": [(20, 21), (27, 28)],
     "enabled": False},
]