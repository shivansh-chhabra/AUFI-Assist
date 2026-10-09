import type {
  AnswerPayload,
  Candidate,
  ChatMessage,
  ChatResponse,
  Conversation,
  DiseaseExplanation,
  EvidenceData,
  KnowledgeBaseStatus,
  SearchFilters,
  SearchResult,
} from '../types';
import { conditionName } from '../conditions';

/*
 * DEMO DATA ONLY (used when VITE_USE_MOCK_DATA=true).
 *
 * The probabilities, questions and guideline excerpts below are scripted so the
 * interface can be shown without a backend. They are NOT output of the scoring
 * component and the excerpts are NOT verbatim guideline text. Don't present
 * them as clinical content.
 */

export const mockConversations: Conversation[] = [
  { id: 'c1', title: 'Fever, body ache, 3 days', active: true },
];

export const mockKnowledgeBaseStatus: KnowledgeBaseStatus = {
  documentCount: 14,
  lastIndexed: 'Today, 14:32',
};

// ---- scripted narrowing: 11 candidates -> dengue + chikungunya ----------

type Dist = Record<string, number>;
const DISTRIBUTIONS: Dist[] = [
  // after the first description
  { dengue: 22, viral_ili: 18, malaria: 14, typhoid: 11, chikungunya: 9, scrub_typhus: 7, leptospirosis: 5, hepatitis_a_e: 4, occult_bacteraemia: 4, tb: 3, rheumatic_fever: 3 },
  // chills in a repeating pattern: no
  { dengue: 27, viral_ili: 21, chikungunya: 12, typhoid: 12, scrub_typhus: 8, leptospirosis: 5, hepatitis_a_e: 4, malaria: 4, occult_bacteraemia: 3, tb: 2, rheumatic_fever: 2 },
  // rash or bleeding: yes
  { dengue: 44, chikungunya: 20, scrub_typhus: 10, typhoid: 8, viral_ili: 6, leptospirosis: 4, malaria: 2, occult_bacteraemia: 2, rheumatic_fever: 2, hepatitis_a_e: 1, tb: 1 },
  // severe joint pain: yes
  { dengue: 47, chikungunya: 43, scrub_typhus: 3, typhoid: 2, viral_ili: 1, malaria: 1, leptospirosis: 1, occult_bacteraemia: 1, rheumatic_fever: 1, hepatitis_a_e: 0, tb: 0 },
];

function candidatesAt(stage: number, shortlist: string[] = []): Candidate[] {
  const now = DISTRIBUTIONS[stage];
  const before = stage > 0 ? DISTRIBUTIONS[stage - 1] : undefined;
  return Object.entries(now)
    .map(([id, p]) => ({
      id,
      name: conditionName(id),
      probability: p / 100,
      previous: before ? before[id] / 100 : undefined,
      shortlisted: shortlist.includes(id),
    }))
    .sort((a, b) => b.probability - a.probability);
}

const QUESTIONS = [
  {
    feature: 'chills_rigors_periodic',
    text: 'Did the fever come with chills and shaking (rigors) in a repeating pattern, for example every other day?',
    informationGain: 0.91,
    candidatesSeparated: 6,
  },
  {
    feature: 'rash_or_bleeding',
    text: 'Have you noticed a rash, or any bleeding such as from the gums or nose?',
    informationGain: 0.84,
    candidatesSeparated: 5,
  },
  {
    feature: 'severe_joint_pain',
    text: 'Is there joint pain severe enough that moving the hands, wrists or ankles is difficult?',
    informationGain: 0.62,
    candidatesSeparated: 2,
  },
];

const FIRST_REPLY =
  'Thanks. A new fever with body ache fits many of the 11 conditions I cover, so I need to narrow it down.\n\n' +
  'First question:';

const FINAL_EVIDENCE: EvidenceData = {
  sourceCount: 6,
  chunkCount: 6,
  retrievalMs: 58,
  documentsInIndex: 14,
  droppedBelowThreshold: 2,
  filters: [
    { disease: 'Dengue', contentType: 'clinical_features' },
    { disease: 'Dengue', contentType: 'confirmatory_tests' },
    { disease: 'Dengue', contentType: 'treatment' },
    { disease: 'Chikungunya', contentType: 'clinical_features' },
    { disease: 'Chikungunya', contentType: 'confirmatory_tests' },
    { disease: 'Chikungunya', contentType: 'treatment' },
  ],
  sources: [
    { id: 1, title: 'Dengue clinical management (demo excerpt)', body: 'MoHFW', location: 'Clinical features', disease: 'Dengue', contentType: 'clinical_features', relevance: 0.86, snippet: 'Demo excerpt: sudden fever with severe headache, pain behind the eyes, muscle and joint pain, and sometimes a rash.' },
    { id: 2, title: 'Dengue clinical management (demo excerpt)', body: 'MoHFW', location: 'Laboratory diagnosis', disease: 'Dengue', contentType: 'confirmatory_tests', relevance: 0.83, snippet: 'Demo excerpt: NS1 antigen detection in the early days of illness, IgM antibody testing from about day 5.' },
    { id: 3, title: 'Dengue clinical management (demo excerpt)', body: 'MoHFW', location: 'Management', disease: 'Dengue', contentType: 'treatment', relevance: 0.81, snippet: 'Demo excerpt: supportive care with oral fluids and paracetamol; avoid NSAIDs; watch for warning signs.' },
    { id: 4, title: 'Chikungunya clinical management (demo excerpt)', body: 'ICMR', location: 'Clinical features', disease: 'Chikungunya', contentType: 'clinical_features', relevance: 0.84, snippet: 'Demo excerpt: abrupt fever with severe, often symmetrical joint pain that can limit movement.' },
    { id: 5, title: 'Chikungunya clinical management (demo excerpt)', body: 'ICMR', location: 'Laboratory diagnosis', disease: 'Chikungunya', contentType: 'confirmatory_tests', relevance: 0.79, snippet: 'Demo excerpt: RT-PCR in the first week of illness, IgM antibody testing after about day 5.' },
    { id: 6, title: 'Chikungunya clinical management (demo excerpt)', body: 'ICMR', location: 'Management', disease: 'Chikungunya', contentType: 'treatment', relevance: 0.77, snippet: 'Demo excerpt: symptomatic treatment with rest, fluids and paracetamol; joint pain can persist for weeks.' },
  ],
};

const FINAL_EXPLANATION: DiseaseExplanation[] = [
  {
    diseaseId: 'dengue',
    disease: 'Dengue',
    sections: [
      { contentType: 'clinical_features', text: 'Sudden fever with severe headache, pain behind the eyes, and muscle and joint pain. A rash can appear, and bleeding signs such as gum or nose bleeding point towards dengue.', citations: [1] },
      { contentType: 'confirmatory_tests', text: 'NS1 antigen testing works in the first days of illness. IgM antibody testing becomes useful from about day 5.', citations: [2] },
      { contentType: 'treatment', text: 'Supportive care: oral fluids and paracetamol for fever, avoiding NSAIDs. Watch for warning signs such as persistent vomiting, abdominal pain or bleeding, and refer if they appear.', citations: [3] },
    ],
  },
  {
    diseaseId: 'chikungunya',
    disease: 'Chikungunya',
    sections: [
      { contentType: 'clinical_features', text: 'Abrupt fever with severe joint pain, often in both hands, wrists or ankles, that can make movement difficult.', citations: [4] },
      { contentType: 'confirmatory_tests', text: 'RT-PCR in the first week of illness. IgM antibody testing after about day 5.', citations: [5] },
      { contentType: 'treatment', text: 'Symptomatic treatment with rest, fluids and paracetamol. Joint pain can last for weeks after the fever settles.', citations: [6] },
    ],
  },
];

const FINAL_REPLY =
  '## Shortlist: dengue and chikungunya\n\n' +
  'Your answers (no repeating chills, a rash or bleeding, and severe joint pain) leave two conditions far ahead of the rest. ' +
  'Both can look alike early on. Below is what the guidelines say about each.\n\n' +
  'Only a confirmatory test separates them reliably.';

/** How many user turns each conversation has already had in the scripted case. */
const stageByConversation: Record<string, number> = { c1: 1 };

export function mockChatReply(_message: string, conversationId = 'default', answer?: AnswerPayload): ChatResponse {
  const stage = stageByConversation[conversationId] ?? 0;
  stageByConversation[conversationId] = stage + 1;

  // Stages 0..2 each ask a question; stage 3 concludes.
  if (stage <= 2) {
    const q = QUESTIONS[stage];
    return {
      reply: stage === 0 ? FIRST_REPLY : `Noted${answer ? ` (${answer.value})` : ''}. Next question:`,
      steps: stage === 0
        ? [
            'Read symptoms from your description: fever, body ache, duration 3 days.',
            'Scored 11 conditions against the condition-feature table.',
            `Ranked remaining questions by expected information gain. Best: ${q.feature}.`,
          ]
        : [
            'Updated probabilities from your answer.',
            `${11 - stage * 2} conditions still above 1%.`,
            `Ranked remaining questions by expected information gain. Best: ${q.feature}.`,
          ],
      candidates: candidatesAt(stage),
      question: { ...q, text: q.text },
      progress: { questionsAsked: stage, maxQuestions: 8, candidatesRemaining: stage === 0 ? 11 : stage === 1 ? 10 : 8 },
      evidence: null,
      explanation: null,
    };
  }

  if (stage === 3) {
    return {
      reply: FINAL_REPLY,
      steps: [
        'Updated probabilities from your answer.',
        'Two candidates remain: stopping the question loop.',
        'Retrieving guideline passages filtered to each disease and content type.',
        'Kept 6 passages above the relevance threshold, dropped 2.',
        'Writing the explanation from the retrieved text only.',
      ],
      candidates: candidatesAt(3, ['dengue', 'chikungunya']),
      question: null,
      progress: { questionsAsked: 3, maxQuestions: 8, candidatesRemaining: 2, stopReason: 'shortlist' },
      explanation: FINAL_EXPLANATION,
      evidence: FINAL_EVIDENCE,
    };
  }

  return {
    reply: 'This case has reached its shortlist. To assess another patient, start a new case.',
    steps: [],
    candidates: candidatesAt(3, ['dengue', 'chikungunya']),
    question: null,
    progress: { questionsAsked: 3, maxQuestions: 8, candidatesRemaining: 2, stopReason: 'shortlist' },
    evidence: null,
    explanation: null,
  };
}

// Seeded history: a case that is waiting on its first answer, so the quick-reply buttons show on load.
const seed = mockChatReply('Fever for three days with body ache', 'seed');
export const mockMessageHistory: Record<string, ChatMessage[]> = {
  c1: [
    { id: 'seed-1', role: 'user', text: 'Fever for three days with body ache' },
    {
      id: 'seed-2',
      role: 'ai',
      text: seed.reply,
      steps: seed.steps,
      candidates: seed.candidates,
      question: seed.question,
      progress: seed.progress,
    },
  ],
};

// ---- search over the demo corpus -------------------------------------------

const mockSearchCorpus: SearchResult[] = FINAL_EVIDENCE.sources.map((s) => ({
  id: `s${s.id}`,
  snippet: s.snippet ?? '',
  documentTitle: s.title,
  location: s.location,
  body: s.body,
  disease: s.disease,
  contentType: s.contentType,
}));

export function mockSearch(query: string, filters: SearchFilters = {}): SearchResult[] {
  if (!query.trim()) return [];
  const q = query.toLowerCase();
  const pool = mockSearchCorpus.filter(
    (r) =>
      (!filters.disease || r.disease?.toLowerCase() === conditionName(filters.disease).toLowerCase()) &&
      (!filters.contentType || r.contentType === filters.contentType)
  );
  const matches = pool.filter(
    (r) => r.snippet.toLowerCase().includes(q) || r.disease?.toLowerCase().includes(q) || r.documentTitle.toLowerCase().includes(q)
  );
  return matches;
}
