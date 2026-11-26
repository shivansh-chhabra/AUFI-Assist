"""Tests for the real rag/retriever.py adapter and agent/explainer.py (fake index and fake LLM)."""
import json

import pytest

from app import config
from app.agent import explainer
from app.rag import retriever

PASSAGES = [
    {"id": 1, "text": "Dengue presents with high fever for 2 to 7 days, headache, retro-orbital pain and rash.",
     "title": "ICMR dengue", "location": "pp. 3-4", "disease": "Dengue", "content_type": "clinical_features"},
    {"id": 2, "text": "NS1 antigen testing is recommended within the first 5 days of illness. IgM ELISA after day 5.",
     "title": "ICMR dengue", "location": "p. 9", "disease": "Dengue", "content_type": "confirmatory_tests"},
    {"id": 3, "text": "Chikungunya causes severe joint pain.", "title": "x", "location": "p. 1",
     "disease": "Chikungunya", "content_type": "clinical_features"},
]
SHORTLIST = [{"id": "dengue", "name": "Dengue", "probability": 0.6}]


class FakeLLM:
    def __init__(self, reply=None, up=True):
        self.reply, self.up, self._ok = reply, up, up

    def available(self):
        return self.up

    def chat(self, messages):
        if isinstance(self.reply, Exception):
            raise self.reply
        return json.dumps(self.reply) if not isinstance(self.reply, str) else self.reply


@pytest.fixture
def llm(monkeypatch):
    def install(**kw):
        fake = FakeLLM(**kw)
        monkeypatch.setattr(explainer, "_llm", fake)
        return fake
    return install


def secs(result):
    return {s["content_type"]: s for s in result[0]["sections"]}


def test_llm_sections_kept_when_grounded(llm):
    llm(reply={"sections": [
        {"content_type": "clinical_features", "text": "Fever lasts 2 to 7 days with headache and rash.", "citations": [1]},
        {"content_type": "confirmatory_tests", "text": "NS1 antigen in the first 5 days; IgM ELISA after day 5.", "citations": [2]},
    ]})
    s = secs(explainer.explain(SHORTLIST, [], "fever", PASSAGES))
    assert s["clinical_features"]["text"].startswith("Fever lasts")
    assert s["confirmatory_tests"]["citations"] == [2]
    assert "treatment" not in s            # no passage, no claim


def test_invented_number_and_bad_citation_fall_back_to_quoted_text(llm):
    llm(reply={"sections": [
        {"content_type": "clinical_features", "text": "Fever lasts 14 days with headache.", "citations": [1]},
        {"content_type": "confirmatory_tests", "text": "NS1 antigen in the first 5 days.", "citations": [3]},  # other condition
    ]})
    s = secs(explainer.explain(SHORTLIST, [], "fever", PASSAGES))
    assert s["clinical_features"]["text"].startswith("Dengue presents")   # extractive
    assert s["clinical_features"]["citations"] == [1]
    assert s["confirmatory_tests"]["text"].startswith("NS1 antigen testing")
    assert s["confirmatory_tests"]["citations"] == [2]


@pytest.mark.parametrize("kw", [dict(up=False), dict(reply="not json"), dict(reply=OSError("down"))])
def test_works_without_llm(llm, kw):
    llm(**kw)
    r = explainer.explain(SHORTLIST, [], "fever", PASSAGES)
    assert r[0]["disease_id"] == "dengue"
    assert all(sec["citations"] for sec in r[0]["sections"])


def test_condition_without_passages_is_skipped(llm):
    llm(up=False)
    sl = SHORTLIST + [{"id": "malaria", "name": "Malaria", "probability": 0.2}]
    assert [e["disease_id"] for e in explainer.explain(sl, [], "", PASSAGES)] == ["dengue"]


# ------------------------------------------------------------------ retriever adapter
class FakeIndex:
    total = 10

    class col:
        @staticmethod
        def get(include=None):
            return {"metadatas": [{"source_file": "a.pdf"}, {"source_file": "a.pdf"}, {"source_file": "b.pdf"}]}

    def __init__(self):
        self.calls = []

    def search(self, q, conds, n=3):
        self.calls.append((q, conds))
        meta = {"source_file": "icmr_dengue.pdf", "page_start": 3, "page_end": 4, "issuer": "ICMR", "condition": "dengue"}
        return [{"text": "same chunk everywhere", "meta": meta, "distance": 0.4, "score": 0.6},
                {"text": "weak " + q[:20], "meta": meta, "distance": 0.9, "score": 0.1}]


@pytest.fixture
def index(monkeypatch):
    fake = FakeIndex()
    monkeypatch.setattr(retriever, "_retriever", fake)
    return fake


def test_retrieve_shape_floor_and_dedupe(index):
    raw = retriever.retrieve(["dengue", "malaria"], "fever and rash")
    ps = raw["passages"]
    assert [(p["disease"], p["content_type"]) for p in ps][0] == ("dengue", "clinical_features")
    assert len({p["text"] for p in ps if p["disease"] == "dengue"}) == len([p for p in ps if p["disease"] == "dengue"])
    p = ps[0]
    assert p["file"] == "icmr_dengue.pdf" and p["location"] == "pp. 3-4" and p["body"] == "ICMR" and 0 < p["relevance"] <= 1
    assert raw["dropped_below_threshold"] == 4          # 2 conditions x 2 intents (tests come from the protocol), one weak hit each
    assert raw["documents_in_index"] == 2
    assert len(raw["filters"]) == 4
    assert "fever and rash" in index.calls[0][0] and "fever and rash" not in index.calls[1][0]


def test_search_accepts_name_or_id_and_unknown_returns_empty(index):
    assert retriever.search("rash", "Dengue", "treatment")[0]["disease"] == "Dengue"
    assert retriever.search("rash", "dengue")[0]["source"] == "icmr_dengue.pdf"
    assert retriever.search("rash", "not_a_condition") == []
    assert retriever.search("rash")                      # all conditions


def test_stub_flag_follows_index_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "CHROMA_DIR", tmp_path / "missing")
    assert retriever.STUB is True
    (tmp_path / "there").mkdir()
    monkeypatch.setattr(config, "CHROMA_DIR", tmp_path / "there")
    assert retriever.STUB is False


def test_answer_passages_filters_by_condition_and_floor(index):
    out = retriever.answer_passages("how does it spread", "dengue")
    assert len(out) == 1 and out[0]["disease"] == "dengue" and out[0]["file"] == "icmr_dengue.pdf"   # the 0.1 hit is below the floor
    assert "Dengue:" in index.calls[-1][0] and retriever.answer_passages("", "dengue") == []


def test_answer_question_uses_llm_when_grounded_else_quotes_the_guideline(llm):
    ps = [{"id": 1, "text": "Dengue is spread by Aedes mosquitoes that bite during the day.", "title": "t", "location": "p. 1"},
          {"id": 2, "text": "Rest and plenty of fluids are advised.", "title": "t", "location": "p. 2"}]
    llm(reply={"answer": "It is spread by Aedes mosquitoes that bite in the day.", "citations": [1]})
    assert explainer.answer_question("how", "Dengue", ps) == [
        {"text": "It is spread by Aedes mosquitoes that bite in the day.", "citations": [1]}]
    llm(reply={"answer": "It is spread by 5 kinds of fleas.", "citations": [1]})          # invented number and words
    got = explainer.answer_question("how", "Dengue", ps)
    assert [b["citations"] for b in got] == [[1], [2]] and got[0]["text"].startswith("Dengue is spread")
    llm(reply={"answer": "", "citations": []})                                              # model says not covered
    assert explainer.answer_question("how", "Dengue", ps) == []
    llm(up=False)                                                                           # no LLM: quoted text
    assert len(explainer.answer_question("how", "Dengue", ps)) == 2
