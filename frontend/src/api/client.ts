import { API_URL, USE_MOCK_DATA } from '../config';
import { mockChatReply, mockConversations, mockKnowledgeBaseStatus, mockMessageHistory, mockSearch } from '../data/mockData';
import type {
  AnswerPayload,
  ChatMessage,
  ChatResponse,
  ChatStreamEvent,
  Conversation,
  KnowledgeBaseStatus,
  SearchFilters,
  SearchResult,
} from '../types';

// Design note: unlike a generic chat demo, this app shows clinical content.
// When the backend is unreachable we surface an error. We never silently
// substitute demo data. Demo data is only used when VITE_USE_MOCK_DATA=true,
// and the UI labels it as such.

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`Request to ${path} failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

/**
 * POST /chat. Returns the full response in one shot (no live step updates).
 * Fallback for when streaming isn't available; prefer sendMessageStream().
 *
 * Request body: { message, conversation_id, answer? }
 *   `answer` is set when the user tapped a quick-reply button, so the
 *   backend can update the scoring component without parsing free text.
 */
export async function sendMessage(
  message: string,
  conversationId?: string,
  answer?: AnswerPayload
): Promise<ChatResponse> {
  if (USE_MOCK_DATA) {
    await new Promise((r) => setTimeout(r, 400));
    return mockChatReply(message, conversationId, answer);
  }
  const raw = await request<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify({ message, conversation_id: conversationId, answer }),
  });
  return { ...raw, answer: raw.reply };
}

/**
 * POST /chat/stream (Server-Sent Events). Calls `onStep` with each
 * reasoning-trace line as the backend produces it, then resolves with the
 * final response. Falls back to the non-streaming sendMessage() if the
 * stream can't be opened.
 */
export async function sendMessageStream(
  message: string,
  onStep: (text: string) => void,
  conversationId?: string,
  answer?: AnswerPayload
): Promise<ChatResponse> {
  if (USE_MOCK_DATA) {
    const response = mockChatReply(message, conversationId, answer);
    for (const step of response.steps) {
      await new Promise((r) => setTimeout(r, 320));
      onStep(step);
    }
    await new Promise((r) => setTimeout(r, 200));
    return response;
  }

  let res: Response;
  try {
    res = await fetch(`${API_URL}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, conversation_id: conversationId, answer }),
    });
  } catch (err) {
    console.warn('Streaming chat unreachable, falling back to sendMessage():', err);
    return sendMessage(message, conversationId, answer);
  }

  if (!res.ok || !res.body) {
    console.warn(`Streaming chat failed (${res.status}), falling back to sendMessage()`);
    return sendMessage(message, conversationId, answer);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let final: ChatResponse | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE frames are separated by a blank line; the payload line starts with "data:".
    const frames = buffer.split('\n\n');
    buffer = frames.pop() ?? '';

    for (const frame of frames) {
      const line = frame.split('\n').find((l) => l.startsWith('data:'));
      if (!line) continue;
      const jsonText = line.slice(5).trim();
      if (!jsonText) continue;

      try {
        const event = JSON.parse(jsonText) as ChatStreamEvent;
        if (event.type === 'step') {
          onStep(event.text);
        } else if (event.type === 'final') {
          final = { ...event, answer: event.reply };
        }
      } catch (err) {
        console.warn('Malformed stream event, skipping:', jsonText, err);
      }
    }
  }

  if (!final) {
    console.warn('Stream ended without a final event, falling back to sendMessage()');
    return sendMessage(message, conversationId, answer);
  }
  return final;
}

/** GET /conversations */
export async function fetchConversations(): Promise<Conversation[]> {
  if (USE_MOCK_DATA) return mockConversations;
  try {
    return await request<Conversation[]>('/conversations');
  } catch {
    return [];
  }
}

/** GET /conversations/{id}/messages */
export async function fetchConversationHistory(conversationId: string): Promise<ChatMessage[]> {
  if (USE_MOCK_DATA) return mockMessageHistory[conversationId] ?? [];
  try {
    return await request<ChatMessage[]>(`/conversations/${conversationId}/messages`);
  } catch {
    return [];
  }
}

/** GET /knowledge-base/status: how many guideline documents are indexed. */
export async function fetchKnowledgeBaseStatus(): Promise<KnowledgeBaseStatus> {
  if (USE_MOCK_DATA) return mockKnowledgeBaseStatus;
  try {
    return await request<KnowledgeBaseStatus>('/knowledge-base/status');
  } catch {
    return { documentCount: 0, lastIndexed: 'Unavailable' };
  }
}

/**
 * POST /search over the guideline corpus. `disease` and `content_type` are
 * the same metadata tags the agent uses to narrow retrieval.
 */
export async function searchDocuments(query: string, filters: SearchFilters = {}): Promise<SearchResult[]> {
  if (USE_MOCK_DATA) {
    await new Promise((r) => setTimeout(r, 300));
    return mockSearch(query, filters);
  }

  const data = await request<{
    results: Array<{
      text: string;
      source: string;
      distance: number;
      disease?: string;
      content_type?: SearchResult['contentType'];
      body?: SearchResult['body'];
      location?: string;
    }>;
  }>('/search', {
    method: 'POST',
    body: JSON.stringify({ query, disease: filters.disease, content_type: filters.contentType }),
  });

  return (data.results || []).map((item, idx) => ({
    id: `sr-${idx}-${Date.now()}`,
    snippet: item.text,
    documentTitle: item.source || 'Guideline document',
    location: item.location ?? `Relevance ${Math.max(0, Math.min(100, Math.round((1 - item.distance) * 100)))}%`,
    distance: item.distance,
    url: item.source ? `/kb-docs/${encodeURIComponent(item.source)}` : undefined,
    body: item.body,
    disease: item.disease,
    contentType: item.content_type,
  }));
}
