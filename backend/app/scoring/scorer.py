"""STAGE 1: probabilistic scoring + adaptive question selection.   >>> YOUR FRIEND FILLS THIS IN <<<

The backend (pipeline.py) owns the question loop, the stop rules (confidence reached or 12
questions) and the HTTP layer. This file only has to answer four things. Keep the function
names and return shapes below and everything else works unchanged.

Delete the line `STUB = True` once the functions are implemented (/health reads it).

`state` is an opaque object that you create and mutate; the backend just stores it per case.
Condition ids must be the ones in app/conditions.py.
"""
from typing import Any, Optional

STUB = True


def start_case(initial_text: str) -> Any:
    """Called once with the patient's first free-text description.
    Create and return the case state. You may extract features from the text here
    (keyword rules or an LLM) and apply them to the state before returning."""
    raise NotImplementedError("scoring.scorer.start_case")


def apply_answer(state: Any, feature: str, value: str) -> None:
    """Record one answer. `feature` is the key you returned in choose_next_question();
    `value` is one of "yes" | "no" | "unsure" | "skip". Mutate `state` in place."""
    raise NotImplementedError("scoring.scorer.apply_answer")


def get_posterior(state: Any) -> dict[str, float]:
    """Return {condition_id: probability} for all 11 conditions, summing to ~1."""
    raise NotImplementedError("scoring.scorer.get_posterior")


def choose_next_question(state: Any) -> Optional[dict]:
    """Pick the most informative unasked question, or return None if no remaining question
    would help separate the candidates.

    Return shape:
        {
          "feature": "severe_joint_pain",          # required, echoed back with the answer
          "text": "Do you have severe joint pain?",# required, shown to the patient
          "options": [                              # optional; default is Yes / No / Not sure
              {"label": "Yes", "value": "yes"},
              {"label": "No", "value": "no"},
              {"label": "Not sure", "value": "unsure"},
          ],
          "information_gain": 0.62,                 # optional, bits, shown as "why this question"
          "candidates_separated": 2,                # optional
        }
    Option `value` must be one of yes | no | unsure | skip.
    """
    raise NotImplementedError("scoring.scorer.choose_next_question")
