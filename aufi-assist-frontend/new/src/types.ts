export type ContentType = 'clinical_features' | 'confirmatory_tests' | 'treatment';
export type GuidelineBody = 'ICMR' | 'MoHFW';
export type AnswerValue = 'yes' | 'no' | 'unsure' | 'skip';

export interface Conversation {
  id: string;
  title: string;
  active?: boolean;
}

/** One disease in the ranked differential. `probability` is 0..1. */
export interface Candidate {
  id: string;
  name: string;
  probability: number;
  /** Probability before the latest answer, used to show the shift. */
  previous?: number;
  /** True once the loop has narrowed to this disease (one or two remain). */
  shortlisted?: boolean;
}

export interface AnswerOption {
  label: string;
  value: AnswerValue;
}

/** The single follow-up question the scoring component chose. */
export interface FollowUpQuestion {
  /** Feature key from the condition-feature table, echoed back with the answer. */
  feature: string;
  text: string;
  options?: AnswerOption[];
  /** Expected information gain in bits, shown as the reason this question was chosen. */
  informationGain?: number;
  /** How many candidates this question is meant to separate. */
  candidatesSeparated?: number;
}

export type StopReason = 'shortlist' | 'question_limit' | 'no_discriminating_question';

export interface CaseProgress {
  questionsAsked: number;
  maxQuestions: number;
  candidatesRemaining: number;
  /** Set once the question loop has stopped. */
  stopReason?: StopReason;
}

/** A retrieved guideline passage. Only real guideline text ever appears here. */
export interface Source {
  /** 1-based number used by [n] citation markers in the explanation. */
  id: number;
  title: string;
  location: string;
  body?: GuidelineBody;
  disease?: string;
  contentType?: ContentType;
  /** 0..1 similarity after reranking. */
  relevance?: number;
  /** Filename in the guideline corpus, if different from `title`. */
  file?: string;
  /** Opens the real source document. */
  url?: string;
  /** The retrieved chunk text, used to highlight it in the preview. */
  snippet?: string;
}

export interface EvidenceData {
  sourceCount: number;
  chunkCount: number;
  retrievalMs: number;
  documentsInIndex: number;
  sources: Source[];
  /** Chunks discarded for being below the relevance threshold. */
  droppedBelowThreshold?: number;
  /** The metadata filter retrieval was narrowed to. */
  filters?: { disease: string; contentType: ContentType }[];
}

export interface ExplanationSection {
  contentType: ContentType;
  text: string;
  /** Source ids this section's claims come from. */
  citations: number[];
}

export interface DiseaseExplanation {
  diseaseId: string;
  disease: string;
  sections: ExplanationSection[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'ai';
  text: string;
  steps?: string[];
  candidates?: Candidate[];
  question?: FollowUpQuestion | null;
  progress?: CaseProgress;
  explanation?: DiseaseExplanation[] | null;
  evidence?: EvidenceData | null;
}

/** What the frontend sends back when the user taps a quick-reply button. */
export interface AnswerPayload {
  feature: string;
  value: AnswerValue;
}

// Shape returned by POST /chat and streamed (as the "final" event) by POST /chat/stream.
export interface ChatResponse {
  reply: string;
  answer?: string; // sendMessage() normalizes reply/answer into one field
  steps: string[];
  candidates?: Candidate[];
  question?: FollowUpQuestion | null;
  progress?: CaseProgress;
  explanation?: DiseaseExplanation[] | null;
  evidence?: EvidenceData | null;
}

/** One event from the POST /chat/stream Server-Sent Events stream. */
export type ChatStreamEvent =
  | { type: 'step'; text: string }
  | ({ type: 'final' } & ChatResponse);

export interface KnowledgeBaseStatus {
  documentCount: number;
  lastIndexed: string;
}

// Shape returned by POST /search, adapted client-side.
export interface SearchResult {
  id: string;
  snippet: string;
  documentTitle: string;
  location: string;
  distance?: number;
  url?: string;
  body?: GuidelineBody;
  disease?: string;
  contentType?: ContentType;
}

export interface SearchFilters {
  disease?: string;
  contentType?: ContentType;
}

export interface ReasoningStep {
  id: string;
  label: string;
}
