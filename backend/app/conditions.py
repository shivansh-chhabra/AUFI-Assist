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

CONTENT_TYPES: dict[str, str] = {
    "clinical_features": "Clinical features",
    "confirmatory_tests": "Confirmatory tests",
    "treatment": "Treatment and management",
}


def condition_name(cid: str) -> str:
    return CONDITIONS.get(cid, cid)
