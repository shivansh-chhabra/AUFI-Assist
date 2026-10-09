import { useEffect, useState } from 'react';
import HeaderControls from './components/HeaderControls';
import Sidebar from './components/Sidebar';
import ChatThread from './components/ChatThread';
import Composer from './components/Composer';
import SearchOverlay from './components/SearchOverlay';
import { useTheme } from './hooks/useTheme';
import { fetchConversationHistory, fetchConversations, fetchKnowledgeBaseStatus, sendMessageStream } from './api/client';
import { WORKSPACE } from './brand';
import type { AnswerOption, AnswerPayload, ChatMessage, Conversation, FollowUpQuestion, KnowledgeBaseStatus } from './types';

let messageIdCounter = 0;
const nextId = () => `m${++messageIdCounter}`;

// Turns the first symptom description of a case into a short sidebar title,
// with no model call. Strips scaffolding like "I have" or "my father has"
// so the title is the symptoms themselves.
const TITLE_LEAD_IN_RE =
  /^(i\s+(have|had|am\s+having|got)|i've\s+(had|got)|(my|the)\s+\w+\s+(has|have|had|is\s+having)|patient\s+(has|is\s+having)|there\s+is)\s+(a\s+|an\s+)?/i;

const TITLE_MAX_WORDS = 6;

function titleFromMessage(text: string): string {
  let trimmed = text.trim().replace(/\s+/g, ' ');
  if (!trimmed) return 'New case';
  trimmed = trimmed.replace(TITLE_LEAD_IN_RE, '').replace(/[?.!]+$/, '').trim();
  if (!trimmed) return 'New case';

  const words = trimmed.split(' ');
  const short = words.slice(0, TITLE_MAX_WORDS).join(' ');
  const capitalized = short.charAt(0).toUpperCase() + short.slice(1);
  return words.length > TITLE_MAX_WORDS ? `${capitalized}…` : capitalized;
}

export default function App({ onGoHome }: { onGoHome?: () => void }) {
  const { theme, toggleTheme } = useTheme();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string>('');
  const [kbStatus, setKbStatus] = useState<KnowledgeBaseStatus>({
    documentCount: 0,
    lastIndexed: 'Not indexed yet',
  });
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [liveSteps, setLiveSteps] = useState<string[]>([]);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(272);
  const [isDesktop, setIsDesktop] = useState(() => typeof window !== 'undefined' && window.innerWidth > 860);

  useEffect(() => {
    const onResize = () => setIsDesktop(window.innerWidth > 860);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsSearchOpen(true);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  // Initial load: conversations + knowledge base status come from the
  // backend (or mock data, depending on VITE_USE_MOCK_DATA).
  useEffect(() => {
    fetchConversations().then((convs) => {
      setConversations(convs);
      const active = convs.find((c) => c.active) ?? convs[0];
      if (active) {
        setActiveConversationId(active.id);
        fetchConversationHistory(active.id).then(setMessages);
      }
    });
    fetchKnowledgeBaseStatus().then(setKbStatus);
    // Knowledge-base status can change as documents are indexed in the
    // background; refresh it periodically instead of only once on load.
    const interval = setInterval(() => {
      fetchKnowledgeBaseStatus().then(setKbStatus);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const lastMessage = messages[messages.length - 1];
  const awaitingAnswer = !!(lastMessage?.role === 'ai' && lastMessage.question);

  const handleSend = async (text: string, answer?: AnswerPayload) => {
    const userMessage: ChatMessage = { id: nextId(), role: 'user', text };
    setMessages((prev) => [...prev, userMessage]);

    // The first message of a new case becomes its sidebar title (local only
    // until the backend persists conversations).
    const isFirstMessage = messages.length === 0;
    if (isFirstMessage && text.trim()) {
      const title = titleFromMessage(text);
      setConversations((prev) => prev.map((c) => (c.id === activeConversationId ? { ...c, title } : c)));
    }

    setIsLoading(true);
    setLiveSteps([]);
    try {
      const response = await sendMessageStream(
        text,
        (stepText) => setLiveSteps((prev) => [...prev, stepText]),
        activeConversationId,
        answer
      );
      const aiMessage: ChatMessage = {
        id: nextId(),
        role: 'ai',
        text: response.answer || response.reply || 'No answer returned.',
        steps: response.steps,
        candidates: response.candidates,
        question: response.question,
        progress: response.progress,
        explanation: response.explanation,
        evidence: response.evidence,
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      const errorMessage: ChatMessage = {
        id: nextId(),
        role: 'ai',
        text: "Can't reach the local backend. Check that the API and Ollama are running, then send the message again.",
      };
      setMessages((prev) => [...prev, errorMessage]);
      console.error(err);
    } finally {
      setIsLoading(false);
      setLiveSteps([]);
    }
  };

  const handleQuickAnswer = (option: AnswerOption, question: FollowUpQuestion) => {
    handleSend(option.label, { feature: question.feature, value: option.value });
  };

  const handleSelectConversation = (id: string) => {
    setActiveConversationId(id);
    setMessages([]);
    fetchConversationHistory(id).then(setMessages);
  };

  const handleNewConversation = () => {
    const newConv: Conversation = { id: `local-${Date.now()}`, title: 'New case' };
    setConversations((prev) => [newConv, ...prev]);
    setActiveConversationId(newConv.id);
    setMessages([]);
    // Backend wiring: POST /conversations to persist the new conversation.
  };

  const handleDeleteConversation = (id: string) => {
    setConversations((prev) => {
      const next = prev.filter((c) => c.id !== id);
      if (id === activeConversationId) {
        const fallback = next[0];
        if (fallback) {
          setActiveConversationId(fallback.id);
          fetchConversationHistory(fallback.id).then(setMessages);
        } else {
          setActiveConversationId('');
          setMessages([]);
        }
      }
      return next;
    });
    // Backend wiring: DELETE /conversations/{id} to persist the removal.
  };

  return (
    <div className="app" style={isDesktop ? { gridTemplateColumns: `${sidebarWidth}px 1fr` } : undefined}>
      <Sidebar
        workspace={WORKSPACE}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        documentCount={kbStatus.documentCount}
        lastIndexed={kbStatus.lastIndexed}
        width={sidebarWidth}
        onWidthChange={setSidebarWidth}
        onGoHome={onGoHome}
        onOpenSearch={() => setIsSearchOpen(true)}
      />

      <div className="main">
        <HeaderControls userInitials="Dr" theme={theme} toggleTheme={toggleTheme} />
        <ChatThread
          messages={messages}
          isLoading={isLoading}
          liveSteps={liveSteps}
          onAnswer={handleQuickAnswer}
          onPickExample={(text) => handleSend(text)}
        />
        <Composer
          onSend={(text) => handleSend(text)}
          disabled={isLoading}
          awaitingAnswer={awaitingAnswer}
        />
      </div>

      {isSearchOpen && <SearchOverlay onClose={() => setIsSearchOpen(false)} />}
    </div>
  );
}
