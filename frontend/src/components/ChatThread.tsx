import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import EvidencePanel from './EvidencePanel';
import ExplanationPanel from './ExplanationPanel';
import CandidatePanel from './CandidatePanel';
import QuestionCard from './QuestionCard';
import CaseProgress from './CaseProgress';
import ReasoningPanel from './ReasoningPanel';
import DocumentPreviewModal from './DocumentPreviewModal';
import { EXAMPLE_PROMPTS } from '../conditions';
import { BRAND_NAME } from '../brand';
import type { AnswerOption, ChatMessage, FollowUpQuestion, Source } from '../types';

interface ChatThreadProps {
  messages: ChatMessage[];
  isLoading?: boolean;
  /** Reasoning-trace lines received so far for the in-flight message, in order. */
  liveSteps?: string[];
  onAnswer: (option: AnswerOption, question: FollowUpQuestion) => void;
  onPickExample: (text: string) => void;
  /** Where the finished case's PDF can be downloaded. */
  reportUrl?: string;
}

export default function ChatThread({ messages, isLoading, liveSteps, onAnswer, onPickExample, reportUrl }: ChatThreadProps) {
  const messageRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const prevIsLoading = useRef(isLoading);
  const [previewSource, setPreviewSource] = useState<Source | null>(null);

  // After a reply finishes, scroll so the question that started the exchange
  // sits near the top, so a long answer doesn't push it out of view.
  useEffect(() => {
    if (prevIsLoading.current && !isLoading) {
      const lastUserMessage = [...messages].reverse().find((m) => m.role === 'user');
      if (lastUserMessage) {
        messageRefs.current[lastUserMessage.id]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
    prevIsLoading.current = isLoading;
  }, [isLoading, messages]);

  const latestProgress = [...messages].reverse().find((m) => m.progress)?.progress;
  const lastMessage = messages[messages.length - 1];
  const lastAiWithCandidates = [...messages].reverse().find((m) => m.role === 'ai' && m.candidates?.length);

  return (
    <>
      <CaseProgress progress={latestProgress} />
      <div className="thread">
        {messages.length === 0 && !isLoading && (
          <div className="empty">
            <h2>Describe the fever in your own words.</h2>
            <p>
              I'll ask one follow-up question at a time, each chosen to rule out as many of the
              11 conditions as possible, then explain the likely ones from ICMR and MoHFW guidelines.
            </p>
            <div className="example-list">
              {EXAMPLE_PROMPTS.map((p) => (
                <button key={p} className="example-btn" onClick={() => onPickExample(p)} type="button">
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => {
          const isWaitingOnAnswer = msg.role === 'ai' && msg.question && msg === lastMessage && !isLoading;
          return (
            <div
              className={`msg${msg.role === 'user' ? ' user' : ' ai'}`}
              key={msg.id}
              ref={(el) => {
                messageRefs.current[msg.id] = el;
              }}
            >
              <div className="msg-inner">
                <div className={`msg-role${msg.role === 'ai' ? ' ai' : ''}`}>
                  {msg.role === 'user' ? 'You' : BRAND_NAME}
                </div>

                {msg.role === 'ai' ? (
                  <div className="msg-body markdown-body">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
                    {msg.question && <p className="followup-q">{msg.question.text}</p>}
                  </div>
                ) : (
                  <div className="msg-body">{msg.text}</div>
                )}

                {isWaitingOnAnswer && msg.question && (
                  <QuestionCard question={msg.question} onAnswer={onAnswer} disabled={isLoading} />
                )}

                {msg.candidates && msg.candidates.length > 0 && (
                  <CandidatePanel candidates={msg.candidates} isLatest={msg === lastAiWithCandidates} />
                )}

                {msg.explanation && msg.explanation.length > 0 && (
                  <ExplanationPanel
                    explanation={msg.explanation}
                    sources={msg.evidence?.sources ?? []}
                    onOpenSource={setPreviewSource}
                    reportUrl={reportUrl}
                  />
                )}

                {msg.steps && msg.steps.length > 0 && (
                  <details className="why-toggle" style={{ marginTop: '0.75rem' }}>
                    <summary className="why-summary">
                      <span className="chev">▶</span> What the system did ({msg.steps.length} steps)
                    </summary>
                    <ReasoningPanel steps={msg.steps} />
                  </details>
                )}

                {msg.evidence && <EvidencePanel evidence={msg.evidence} onOpenSource={setPreviewSource} />}
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="msg ai">
            <div className="msg-inner">
              <div className="msg-role ai">{BRAND_NAME}</div>
              <ReasoningPanel steps={liveSteps ?? []} live />
            </div>
          </div>
        )}
      </div>

      {previewSource && (
        <DocumentPreviewModal
          filename={previewSource.file ?? previewSource.title}
          highlight={previewSource.snippet}
          onClose={() => setPreviewSource(null)}
        />
      )}
    </>
  );
}
