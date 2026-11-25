"""The fixed ICMR/MoHFW test protocol (app/protocols): data integrity, day logic, close-call tests."""
import pytest

from app.conditions import CONDITIONS
from app.protocols import prescriber as px

D = px.load()


def test_every_condition_and_reference_is_defined():
    assert set(D["conditions"]) == set(CONDITIONS)
    tests, sources = set(D["tests"]), set(D["sources"])
    cites = []
    for cid, c in D["conditions"].items():
        for k in ("first_line", "also", "if_severe", "not_recommended", "conditional"):
            for e in c.get(k, []):
                assert e["test"] in tests, (cid, e["test"])
                cites += e["src"]
        cites += [x for n in c.get("notes", []) for x in n["src"]]
    for p in D["pair_differentiators"]:
        assert set(p["pair"]) <= set(CONDITIONS) and set(p["tests"]) <= tests
        cites += p["src"]
    for st in D["common_workup"]:
        assert set(st["tests"]) <= tests
        cites += st["src"]
    assert cites and all(c.partition(":")[0] in sources and c.partition(":")[2] for c in cites)


def test_only_icmr_and_mohfw_sources():
    assert {s["issuer"] for s in D["sources"].values()} <= {"ICMR", "MoHFW"}


@pytest.mark.parametrize("text,day", [("fever for 4 days with rash", 4), ("day 3 of fever", 3), ("5 days of fever", 5),
                                      ("fever", None), ("fever for 400 days", None)])
def test_parse_day(text, day):
    assert px.parse_day_of_fever(text) == day


def test_day_of_fever_picks_the_valid_dengue_test():
    early = px.prescribe({"dengue": 0.8}, ["dengue"], day=3)["by_condition"]["dengue"]["text"]
    late = px.prescribe({"dengue": 0.8}, ["dengue"], day=8)["by_condition"]["dengue"]["text"]
    assert "NS1 antigen (ELISA) (day 1-5)" in early and "IgM capture ELISA (MAC-ELISA) (not valid yet" in early
    assert "NS1" not in late.split("Recommended:")[1].split("Also useful")[0] and "after day 5" in late


def test_close_pair_adds_the_explicit_differentiator_and_is_deterministic():
    post = {"dengue": 0.40, "chikungunya": 0.36, "malaria": 0.10}
    a = px.prescribe(post, ["dengue", "chikungunya", "malaria"], day=4)
    assert a == px.prescribe(post, ["dengue", "chikungunya", "malaria"], day=4)
    assert a["close"] == ["dengue", "chikungunya"]
    t = a["by_condition"]["dengue"]["text"]
    assert "close" in t and "tell them apart" in t and "haematocrit" in t
    assert "tell them apart" not in a["by_condition"]["malaria"]["text"]


def test_clear_leader_gets_no_differentiator():
    r = px.prescribe({"dengue": 0.7, "chikungunya": 0.2}, ["dengue", "chikungunya"], day=4)
    assert r["close"] == [] and "tell them apart" not in r["by_condition"]["dengue"]["text"]


def test_default_rule_for_pair_without_explicit_entry():
    info = px.pair_info("typhoid", "leptospirosis", None)
    assert not info["explicit"] and "blood_culture_2" in info["tests"] and "lepto_igm_elisa" in info["tests"]
    assert "widal" not in info["tests"]
    # shared test is dropped from the differentiators
    assert "blood_culture_2" not in px.pair_info("typhoid", "occult_bacteraemia", None)["tests"] or px.pair_info("typhoid", "occult_bacteraemia", None)["explicit"]


def test_every_condition_gets_text_with_citations_and_viral_ili_is_conditional():
    r = px.prescribe({c: 0.1 for c in CONDITIONS}, list(CONDITIONS), day=None, margin=0)["by_condition"]
    assert set(r) == set(CONDITIONS)
    assert all(v["text"] and v["citations"] for v in r.values())
    assert "Category C" in r["viral_ili"]["text"] and "Recommended:" not in r["viral_ili"]["text"]
    assert "Baseline for any fever" in r[list(CONDITIONS)[0]]["text"]
