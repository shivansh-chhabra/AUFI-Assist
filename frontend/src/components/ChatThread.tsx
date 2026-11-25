import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import EvidencePanel from './EvidencePanel';
import ExplanationPanel from './ExplanationPanel';
import CandidatePanel from './CandidatePanel';
import QuestionStage from './QuestionStage';
import CaseProgress from './CaseProgress';
import ReasoningPanel from './ReasoningPanel';
import DocumentPreviewModal from './DocumentPreviewModal';
import { EXAMPLE_PROMPTS } from '../conditions';
import { BRAND_NAME } from '../brand';
import { deriveCase } from '../utils/caseState';
import type { AnswerOption, ChatMessage, FollowUpQuestion, Source } from '../types';

interface ChatThreadProps {
  messages: ChatMessage[];
  isLoading?: boolean;
  /** Reasoning-trace lines received so far for the in-flight message, in order. */
  liveSteps?: string[];
  onAnswer: (option: AnswerOption, question: FollowUpQuestion) => void;
  onPickExample: (text: string) => void;
  onBack: () => void;
  direction: 'forward' | 'back';
  canGoBack: boolean;
  /** Where the finished case's PDF can be downloaded. */
  reportUrl?: string;
}

export default function ChatThread({
  messages, isLoading = false, liveSteps = [], onAnswer, onPickExample, onBack, direction, canGoBack, reportUrl,
}: ChatThreadProps) {
  const [previewSource, setPreviewSource] = useState<Source | null>(null);
  const topRef = useRef<HTMLDivElement>(null);
  const { progress, finished, inCase, last } = deriveCase(messages);

  // Sources that have a local PDF open in the preview; the rest open the official guideline page.
  const openSource = (s: Source) => {
    if (s.file) setPreviewSource(s);
    else if (s.url && /^https?:/i.test(s.url)) window.open(s.url, '_blank', 'noopener,noreferrer');
    else setPreviewSource(s);
  };

  useEffect(() => {
    if (finished) topRef.current?.scrollIntoView({ block: 'start' });
  }, [finished]);

  // ---- welcome ----
  if (messages.length === 0 && !isLoading) {
    return (
      <>
        <CaseProgress progress={undefined} />
        <div className="thread thread--welcome">
          <div className="empty">
            <h2>Describe the fever in your own words.</h2>
            <p>
              I'll ask one follow-up question at a time, each chosen to rule out as many of the
              11 conditions as possible, then explain the likely ones from ICMR and MoHFW guidelines.
            </p>
            <div className="example-list">
              {EXAMPLE_PROMPTS.map((p, i) => (
                <button
                  key={p}
                  className="example-btn"
                  style={{ animationDelay: `${0.12 * i + 0.1}s` }}
                  onClick={() => onPickExample(p)}
                  type="button"
                >
                  <span className="example-n">{i + 1}</span>
                  {p}
                </button>
              ))}
            </div>
          </div>
        </div>
      </>
    );
  }

  // ---- questions: one fixed screen, content swapped in place ----
  if (inCase || (isLoading && messages.length === 0)) {
    const question = last?.role === 'ai' ? last.question : null;
    return (
      <QuestionStage
        question={question}
        message={last?.role === 'ai' && !question ? last.text : undefined}
        progress={progress}
        isLoading={isLoading}
        liveSteps={liveSteps}
        direction={direction}
        canGoBack={canGoBack}
        onAnswer={onAnswer}
        onBack={onBack}
      />
    );
  }

  // ---- result: the first description, then the final answer (the Q&A is folded away) ----
  const finalIdx = Math.max(0, messages.findIndex((m) => m.role === 'ai' && m.progress?.stopReason));
  const firstUser = messages.find((m) => m.role === 'user');
  const visible: ChatMessage[] = [...(firstUser ? [firstUser] : []), ...messages.slice(finalIdx)];
  const answers: { q: string; a: string }[] = [];
  messages.slice(0, finalIdx).forEach((m, i, arr) => {
    const next = arr[i + 1];
    if (m.role === 'ai' && m.question && next?.role === 'user') answers.push({ q: m.question.text, a: next.text });
  });
  const lastAiWithCandidates = [...messages].reverse().find((m) => m.role === 'ai' && m.candidates?.length);

  return (
    <>
      <CaseProgress progress={progress} />
      <div className="thread">
        <div ref={topRef} />
        {visible.map((msg, idx) => (
          <div className={`msg${msg.role === 'user' ? ' user' : ' ai'}`} key={msg.id}>
            <div className="msg-inner">
              <div className={`msg-role${msg.role === 'ai' ? ' ai' : ''}`}>{msg.role === 'user' ? 'You' : BRAND_NAME}</div>

              {msg.role === 'ai' ? (
                <div className="msg-body markdown-body">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
                </div>
              ) : (
                <div className="msg-body">{msg.text}</div>
              )}

              {idx === 1 && answers.length > 0 && (
                <details className="why-toggle" style={{ marginTop: '0.75rem' }}>
                  <summary className="why-summary">
                    <span className="chev">▶</span> Your answers ({answers.length})
                  </summary>
                  <ul className="answers-list">
                    {answers.map((x, i) => (
                      <li key={i}>
                        <span>{x.q}</span>
                        <b>{x.a}</b>
                      </li>
                    ))}
                  </ul>
                </details>
              )}

              {msg.candidates && msg.candidates.length > 0 && (
                <CandidatePanel candidates={msg.candidates} isLatest={msg === lastAiWithCandidates} />
              )}

              {msg.explanation && msg.explanation.length > 0 && (
                <ExplanationPanel
                  explanation={msg.explanation}
                  sources={msg.evidence?.sources ?? []}
                  onOpenSource={openSource}
                  reportUrl={reportUrl}
                />
              )}

              {msg.evidence && (
                <EvidencePanel evidence={msg.evidence} explanation={msg.explanation} onOpenSource={openSource} />
              )}

              {msg.steps && msg.steps.length > 0 && (
                <details className="why-toggle" style={{ marginTop: '0.75rem' }}>
                  <summary className="why-summary">
                    <span className="chev">▶</span> What the system did ({msg.steps.length} steps)
                  </summary>
                  <ReasoningPanel steps={msg.steps} />
                </details>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="msg ai">
            <div className="msg-inner">
              <div className="msg-role ai">{BRAND_NAME}</div>
              <ReasoningPanel steps={liveSteps} live />
            </div>
          </div>
        )}
      </div>

      {previewSource && (
        <DocumentPreviewModal
          filename={previewSource.file ?? previewSource.title}
          location={previewSource.location}
          highlight={previewSource.snippet}
          onClose={() => setPreviewSource(null)}
        />
      )}
    </>
  );
}
