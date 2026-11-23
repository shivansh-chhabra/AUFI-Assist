import type { CaseProgress as CaseProgressData, StopReason } from '../types';

const STOP_LABEL: Record<StopReason, string> = {
  shortlist: 'Shortlist reached',
  question_limit: 'Question limit reached',
  no_discriminating_question: 'No remaining question separates the candidates',
};

/** Strip above the thread: where this case is in the question loop. */
export default function CaseProgress({ progress }: { progress?: CaseProgressData }) {
  if (!progress) {
    return (
      <div className="case-strip">
        <span>New case. Describe the fever to begin.</span>
      </div>
    );
  }

  const { questionsAsked, maxQuestions, candidatesRemaining, stopReason } = progress;
  return (
    <div className="case-strip">
      <div className="case-ticks" aria-hidden="true">
        {Array.from({ length: maxQuestions }, (_, i) => (
          <span key={i} className={`case-tick${i < questionsAsked ? ' on' : ''}`} />
        ))}
      </div>
      <span className="case-label">
        {stopReason ? STOP_LABEL[stopReason] : `Question ${Math.min(questionsAsked + 1, maxQuestions)} of ${maxQuestions}`}
      </span>
      <span>
        {candidatesRemaining} {candidatesRemaining === 1 ? 'condition' : 'conditions'} remaining
      </span>
    </div>
  );
}
