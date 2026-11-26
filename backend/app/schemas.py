"""Response models. Field names are camelCase on the wire to match frontend/src/types.ts."""
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

AnswerValue = Literal["yes", "no", "unsure", "skip"]
ContentType = Literal["clinical_features", "confirmatory_tests", "treatment"]
StopReason = Literal["shortlist", "question_limit", "no_discriminating_question"]


class Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ---- requests (plain snake_case, exactly what the frontend sends) ----
class AnswerPayload(BaseModel):
    feature: str
    value: AnswerValue


class ChatRequest(BaseModel):
    message: str = ""
    conversation_id: Optional[str] = None
    answer: Optional[AnswerPayload] = None


class SearchRequest(BaseModel):
    query: str
    disease: Optional[str] = None
    content_type: Optional[str] = None


# ---- responses ----
class Candidate(Camel):
    id: str
    name: str
    probability: float
    previous: Optional[float] = None
    shortlisted: bool = False


class AnswerOption(Camel):
    label: str
    value: AnswerValue


class FollowUpQuestion(Camel):
    feature: str
    text: str
    options: Optional[list[AnswerOption]] = None
    information_gain: Optional[float] = None
    candidates_separated: Optional[int] = None


class CaseProgress(Camel):
    questions_asked: int
    max_questions: int
    candidates_remaining: int
    stop_reason: Optional[StopReason] = None


class Source(Camel):
    id: int
    title: str
    location: str
    body: Optional[str] = None
    disease: Optional[str] = None
    content_type: Optional[ContentType] = None
    relevance: Optional[float] = None
    file: Optional[str] = None
    url: Optional[str] = None
    snippet: Optional[str] = None


class EvidenceFilter(Camel):
    disease: str
    content_type: ContentType


class EvidenceData(Camel):
    source_count: int
    chunk_count: int
    retrieval_ms: int
    documents_in_index: int
    sources: list[Source]
    dropped_below_threshold: Optional[int] = None
    filters: Optional[list[EvidenceFilter]] = None


class ExplanationSection(Camel):
    content_type: ContentType
    text: str
    citations: list[int]


class DiseaseInfo(Camel):
    """The fixed, hand-written summary of a condition (data/disease_summaries.json)."""
    causative_agent: str
    transmission: str
    summary: str
    preventive_methods: list[str]


class DiseaseExplanation(Camel):
    disease_id: str
    disease: str
    info: Optional[DiseaseInfo] = None
    sections: list[ExplanationSection] = []


class ChatResponse(Camel):
    reply: str
    steps: list[str] = []
    candidates: Optional[list[Candidate]] = None
    question: Optional[FollowUpQuestion] = None
    progress: Optional[CaseProgress] = None
    explanation: Optional[list[DiseaseExplanation]] = None
    evidence: Optional[EvidenceData] = None

    def wire(self) -> dict:
        return self.model_dump(by_alias=True, mode="json")
