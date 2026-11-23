"""The 11 conditions. Ids MUST match frontend/src/conditions.ts."""

CONDITIONS: dict[str, str] = {
    "malaria": "Malaria",
    "dengue": "Dengue",
    "typhoid": "Typhoid fever",
    "scrub_typhus": "Scrub typhus and murine typhus",
    "leptospirosis": "Leptospirosis",
    "chikungunya": "Chikungunya",
    "viral_ili": "Viral influenza-like illness",
    "hepatitis_a_e": "Hepatitis A and E",
    "occult_bacteraemia": "Occult bacteraemia",
    "rheumatic_fever": "Rheumatic fever",
    "tb": "TB",
}

# Condition names exactly as written in rag/manifest.py CONDITIONS and the condition column of the
# scoring CSV. If your friend renames a condition, change it here and nowhere else.
MANIFEST_NAMES: dict[str, str] = {
    "malaria": "Malaria (P. vivax/falciparum)",
    "dengue": "Dengue (incl. hemorrhagic)",
    "typhoid": "Typhoid fever",
    "scrub_typhus": "Scrub/murine typhus",
    "leptospirosis": "Leptospirosis",
    "chikungunya": "Chikungunya",
    "viral_ili": "Viral ILI",
    "hepatitis_a_e": "Hepatitis A/E",
    "occult_bacteraemia": "Occult bacteremia (pneumonia/UTI-pyelo/intra-abdominal)",
    "rheumatic_fever": "Rheumatic Fever",
    "tb": "TB (prolonged fever)",
}

CONTENT_TYPES: dict[str, str] = {
    "clinical_features": "Clinical features",
    "confirmatory_tests": "Confirmatory tests",
    "treatment": "Treatment and management",
}


def condition_name(cid: str) -> str:
    return CONDITIONS.get(cid, cid)
