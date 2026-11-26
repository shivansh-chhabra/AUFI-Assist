import { useEffect, useRef, useState } from 'react';
import QuestionStage from './QuestionStage';
import ResultView from './ResultView';
import CaseProgress from './CaseProgress';
import DocumentPreviewModal from './DocumentPreviewModal';
import { EXAMPLE_PROMPTS } from '../conditions';
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

  // ---- result: summary, buttons for tests / other conditions / PDF, and questions about the condition ----
  const finalIdx = Math.max(0, messages.findIndex((m) => m.role === 'ai' && m.progress?.stopReason));
  const result = messages[finalIdx];
  const qa: { question: string; answer?: ChatMessage }[] = [];
  messages.slice(finalIdx + 1).forEach((m, i, arr) => {
    if (m.role === 'user') qa.push({ question: m.text, answer: arr[i + 1]?.role === 'ai' ? arr[i + 1] : undefined });
  });

  return (
    <>
      <ResultView
        result={result}
        qa={qa}
        isLoading={isLoading}
        liveSteps={liveSteps}
        reportUrl={reportUrl}
        onOpenSource={openSource}
      />
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
