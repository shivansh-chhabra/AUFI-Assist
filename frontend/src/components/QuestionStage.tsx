import { useEffect, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import type { AnswerOption, CaseProgress, FollowUpQuestion } from '../types';

const DEFAULT_OPTIONS: AnswerOption[] = [
  { label: 'Yes', value: 'yes' },
  { label: 'No', value: 'no' },
  { label: 'Not sure', value: 'unsure' },
];

const ICONS: Record<string, string> = {
  yes: 'M5 12.5l4.5 4.5L19 7.5',
  no: 'M6 6l12 12M18 6L6 18',
  unsure: 'M9.2 9.2a2.9 2.9 0 1 1 4.1 2.6c-.8.5-1.3 1-1.3 1.9M12 17.4h.01',
  skip: 'M5 12h14M13 6l6 6-6 6',
};

interface QuestionStageProps {
  question?: FollowUpQuestion | null;
  /** Text to show when there is no question and nothing is loading (an error or a retry prompt). */
  message?: string;
  progress?: CaseProgress;
  isLoading: boolean;
  liveSteps: string[];
  direction: 'forward' | 'back';
  canGoBack: boolean;
  onAnswer: (option: AnswerOption, question: FollowUpQuestion) => void;
  onBack: () => void;
}

/**
 * The one-question-at-a-time screen. It never scrolls: the question and its choices are swapped in
 * place, sliding out and in, and a back button on the left re-opens the previous question.
 */
export default function QuestionStage({
  question, message, progress, isLoading, liveSteps, direction, canGoBack, onAnswer, onBack,
}: QuestionStageProps) {
  const reduce = useReducedMotion();
  const [chosen, setChosen] = useState<string | null>(null);
  const [slow, setSlow] = useState(false);
  const options = question?.options?.length ? question.options : DEFAULT_OPTIONS;

  useEffect(() => setChosen(null), [question?.feature]);

  // Only show the "thinking" scene if the wait is noticeable, so quick replies feel instant.
  useEffect(() => {
    if (!isLoading) return setSlow(false);
    const t = setTimeout(() => setSlow(true), 350);
    return () => clearTimeout(t);
  }, [isLoading]);

  const pick = (o: AnswerOption) => {
    if (!question || chosen || isLoading) return;
    setChosen(o.value);
    setTimeout(() => onAnswer(o, question), reduce ? 0 : 520);
  };

  // Keyboard: 1-3 pick an option, Backspace goes back (ignored while typing in the box).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement;
      if (el && (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT')) return;
      if (e.key === 'Backspace' && canGoBack && !isLoading) return onBack();
      const i = Number(e.key) - 1;
      if (question && i >= 0 && i < options.length) pick(options[i]);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  const asked = progress?.questionsAsked ?? 0;
  const max = progress?.maxQuestions ?? 12;
  const dx = direction === 'back' ? -1 : 1;
  const D = reduce ? 0.01 : 1;

  const card = {
    enter: { opacity: 0, x: 90 * dx, scale: 0.96, filter: 'blur(8px)' },
    center: {
      opacity: 1, x: 0, scale: 1, filter: 'blur(0px)',
      transition: { type: 'spring' as const, stiffness: 150, damping: 22, staggerChildren: 0.09 * D },
    },
    exit: { opacity: 0, x: -90 * dx, scale: 0.96, filter: 'blur(8px)', transition: { duration: 0.28 * D } },
  };
  const rise = { enter: { opacity: 0, y: 26, rotate: -1.5 }, center: { opacity: 1, y: 0, rotate: 0 } };

  const showQuestion = !!question && !isLoading;
  const showThinking = isLoading && slow;
  const showMessage = !question && !isLoading;

  return (
    <div className="stage">
      <div className="stage-aurora" aria-hidden="true">
        <span /><span /><span />
      </div>

      <div className="stage-top">
        <button
          className="stage-back"
          onClick={onBack}
          disabled={!canGoBack || isLoading}
          style={{ visibility: canGoBack ? 'visible' : 'hidden' }}
          type="button"
          aria-label="Go back and change the previous answer"
        >
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 5l-7 7 7 7" />
          </svg>
          Back
        </button>

        <div className="stage-path" aria-label={`Question ${Math.min(asked + 1, max)} of ${max}`}>
          {Array.from({ length: max }, (_, i) => (
            <span key={i} className={`stage-dot${i < asked ? ' done' : ''}${i === asked ? ' now' : ''}`} />
          ))}
        </div>

        <div className="stage-count">
          {progress ? `${progress.candidatesRemaining} of 11 conditions left` : ''}
        </div>
      </div>

      <div className="stage-main">
        <AnimatePresence mode="wait" custom={direction}>
          {showQuestion && question && (
            <motion.div
              key={question.feature}
              className="stage-card"
              variants={card}
              initial="enter"
              animate="center"
              exit="exit"
            >
              <motion.div className="stage-kicker" variants={rise}>
                Question {Math.min(asked + 1, max)}
              </motion.div>
              <motion.h2 className="stage-q" variants={rise}>
                {question.text}
              </motion.h2>
              <div className="stage-options" role="group" aria-label="Answer this question">
                {options.map((o, i) => (
                  <motion.button
                    key={o.value}
                    variants={rise}
                    className={`opt-card opt-${o.value}${chosen === o.value ? ' is-chosen' : ''}${chosen && chosen !== o.value ? ' is-dim' : ''}`}
                    onClick={() => pick(o)}
                    whileHover={reduce || chosen ? undefined : { y: -8, scale: 1.03 }}
                    whileTap={reduce ? undefined : { scale: 0.96 }}
                    type="button"
                  >
                    <span className="opt-key">{i + 1}</span>
                    <svg className="opt-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d={ICONS[o.value] ?? ICONS.skip} />
                    </svg>
                    <span className="opt-label">{o.label}</span>
                  </motion.button>
                ))}
              </div>
              <motion.p className="stage-hint" variants={rise}>
                Press 1, 2 or 3 to choose. You can also answer in your own words below.
              </motion.p>
            </motion.div>
          )}

          {showThinking && (
            <motion.div
              key="thinking"
              className="stage-card stage-thinking"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 * D } }}
            >
              <div className="stage-orb" aria-hidden="true"><i /><i /><i /></div>
              <AnimatePresence mode="wait">
                <motion.div
                  key={liveSteps[liveSteps.length - 1] ?? 'start'}
                  className="stage-step"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.2 * D }}
                >
                  {liveSteps[liveSteps.length - 1] ?? 'Thinking…'}
                </motion.div>
              </AnimatePresence>
            </motion.div>
          )}

          {showMessage && (
            <motion.div
              key="message"
              className="stage-card stage-message"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <div className="markdown-body">
                <ReactMarkdown>{message ?? 'Describe the fever to begin.'}</ReactMarkdown>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
