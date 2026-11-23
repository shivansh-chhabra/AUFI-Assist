"""STAGE 2b: the agent loop that writes the cited per-disease summary.   >>> YOUR FRIEND FILLS THIS IN <<<

Delete the line `STUB = True` once implemented (/health reads it).
"""
STUB = True


def explain(
    shortlist: list[dict],
    findings: list[dict],
    initial_text: str,
    passages: list[dict],
) -> list[dict]:
    """Write a guideline-grounded summary for each shortlisted condition, including the
    confirmatory tests to recommend.

    Args:
        shortlist: [{"id": "dengue", "name": "Dengue", "probability": 0.47}, ...] best first
        findings:  [{"feature": "...", "question": "Do you have a rash?", "answer": "yes"}, ...]
        initial_text: the patient's first free-text description
        passages:  numbered guideline passages from rag.retriever.retrieve():
                   [{"id": 1, "text": "...", "title": "...", "location": "...", "body": "ICMR",
                     "disease": "dengue", "content_type": "confirmatory_tests"}, ...]

    Return one entry per shortlisted condition:
        [
          {
            "disease_id": "dengue",
            "sections": [
              {"content_type": "clinical_features",  "text": "…", "citations": [1, 3]},
              {"content_type": "confirmatory_tests", "text": "…", "citations": [2]},
              {"content_type": "treatment",          "text": "…", "citations": [4]},
            ],
          },
        ]
    RULES the backend enforces: `citations` must be passage ids from `passages`. A section with
    no valid citation is dropped before it reaches the patient, so never put uncited medical
    claims in `text`. Always include a "confirmatory_tests" section where the guidelines
    support one: that is what the final report shows as recommended tests.
    """
    raise NotImplementedError("agent.explainer.explain")
