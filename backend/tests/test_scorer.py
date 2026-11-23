"""Scorer wrapper + the condition-name mapping (uses the real manifest.py, a small fake table)."""
import pytest

from app import config
from app.conditions import CONDITIONS, MANIFEST_NAMES
from app.rag import manifest
from app.scoring import scorer

FEATS = ["fever", "fever_cyclical", "rash_maculopapular", "eschar", "jaundice", "cough", "self_limited"]


def write_table(path, names=None):
    names = names or [MANIFEST_NAMES[c] for c in CONDITIONS]
    rows = ["condition," + ",".join(FEATS) + ",prior"]
    for i, n in enumerate(names):
        vals = [0.95] + [round(0.05 + 0.08 * ((i * (k + 3)) % 11), 2) for k in range(len(FEATS) - 1)]
        rows.append(f'"{n}",' + ",".join(map(str, vals)) + ",0.09")
    path.write_text("\n".join(rows), encoding="utf-8")


@pytest.fixture
def table(monkeypatch, tmp_path):
    f = tmp_path / "t.csv"
    write_table(f)
    monkeypatch.setattr(config, "SCORING_TABLE", f)
    monkeypatch.setattr(scorer, "_table", None)
    return f


def test_manifest_names_match_manifest_conditions():
    assert set(MANIFEST_NAMES) == set(CONDITIONS)
    assert set(MANIFEST_NAMES.values()) == set(manifest.CONDITIONS) - {"general"}


def test_stub_flag_follows_table(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "SCORING_TABLE", tmp_path / "nope.csv")
    assert scorer.STUB is True
    (tmp_path / "yes.csv").write_text("x")
    monkeypatch.setattr(config, "SCORING_TABLE", tmp_path / "yes.csv")
    assert scorer.STUB is False


def test_text_extraction_handles_negation(table):
    st = scorer.start_case("Fever with a rash and no cough, comes and goes.")
    assert st.from_text == {"rash_maculopapular": True, "cough": False, "fever_cyclical": True}


def test_posterior_uses_app_ids_and_sums_to_one(table):
    st = scorer.start_case("fever")
    post = scorer.get_posterior(st)
    assert set(post) == set(CONDITIONS) and sum(post.values()) == pytest.approx(1)


def test_question_loop_and_answers(table):
    st = scorer.start_case("fever")
    before = scorer.get_posterior(st)
    q = scorer.choose_next_question(st)
    assert q["feature"] not in ("fever", "self_limited") and q["text"] and q["information_gain"] > 0
    scorer.apply_answer(st, q["feature"], "unsure")
    assert scorer.get_posterior(st) == before                 # unsure changes nothing
    q2 = scorer.choose_next_question(st)
    assert q2["feature"] != q["feature"]
    scorer.apply_answer(st, q2["feature"], "yes")
    assert scorer.get_posterior(st) != before
    seen = {q["feature"], q2["feature"]}
    while (nq := scorer.choose_next_question(st)):            # exhausts, then returns None
        assert nq["feature"] not in seen
        seen.add(nq["feature"]); scorer.apply_answer(st, nq["feature"], "skip")


def test_mismatched_table_is_reported(monkeypatch, tmp_path):
    f = tmp_path / "bad.csv"
    write_table(f, names=[MANIFEST_NAMES[c] for c in list(CONDITIONS)[:-1]] + ["Mystery disease"])
    monkeypatch.setattr(config, "SCORING_TABLE", f)
    monkeypatch.setattr(scorer, "_table", None)
    with pytest.raises(ValueError, match="Mystery disease"):
        scorer.start_case("fever")
