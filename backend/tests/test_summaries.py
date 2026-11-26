"""The fixed per-condition summaries (data/disease_summaries.json)."""
import json

import pytest

from app import config, summaries
from app.conditions import CONDITIONS


@pytest.fixture(autouse=True)
def fresh():
    summaries.load.cache_clear()
    yield
    summaries.load.cache_clear()


def test_every_condition_has_a_complete_summary():
    data = summaries.load()
    assert set(data) == set(CONDITIONS)
    for cid, d in data.items():
        assert d["summary"].strip() and d["causative_agent"].strip() and d["transmission"].strip(), cid
        assert d["preventive_methods"] and all(m.strip() for m in d["preventive_methods"]), cid


def test_json_ids_are_mapped_to_app_ids():
    assert "Orientia" in summaries.get("scrub_typhus")["causative_agent"]
    assert "Streptococcus" in summaries.get("occult_bacteraemia")["causative_agent"]
    assert summaries.get("nope") is None


def test_unknown_or_missing_condition_is_rejected(tmp_path, monkeypatch):
    raw = json.load(open(config.DISEASE_SUMMARIES, encoding="utf-8"))
    for bad, msg in ((raw["diseases"][1:], "no summary for malaria"),
                     (raw["diseases"] + [{"id": "zika"}], "unknown condition id")):
        f = tmp_path / "s.json"
        f.write_text(json.dumps({"diseases": bad}))
        monkeypatch.setattr(config, "DISEASE_SUMMARIES", f)
        summaries.load.cache_clear()
        with pytest.raises(ValueError, match=msg):
            summaries.load()
