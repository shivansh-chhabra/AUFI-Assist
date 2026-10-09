import type { AnswerOption, FollowUpQuestion } from '../types';

const DEFAULT_OPTIONS: AnswerOption[] = [
  { label: 'Yes', value: 'yes' },
  { label: 'No', value: 'no' },
  { label: 'Not sure', value: 'unsure' },
];

interface QuestionCardProps {
  question: FollowUpQuestion;
  onAnswer: (option: AnswerOption, question: FollowUpQuestion) => void;
  disabled?: boolean;
}

/** Quick-reply buttons for the one question currently waiting on an answer. */
export default function QuestionCard({ question, onAnswer, disabled }: QuestionCardProps) {
  const options = question.options?.length ? question.options : DEFAULT_OPTIONS;
  const why: string[] = [];
  if (question.candidatesSeparated) why.push(`separates ${question.candidatesSeparated} candidates`);
  if (question.informationGain != null) why.push(`${question.informationGain.toFixed(2)} bits expected gain`);

  return (
    <div className="question-card">
      <div className="quick-replies" role="group" aria-label="Answer this question">
        {options.map((o) => (
          <button
            key={o.value}
            className="quick-btn"
            onClick={() => onAnswer(o, question)}
            disabled={disabled}
            type="button"
          >
            {o.label}
          </button>
        ))}
      </div>
      <div className="quick-why">
        {why.length > 0 ? `Chosen because it ${why.join(', ')}. ` : ''}
        You can also answer in your own words below.
      </div>
    </div>
  );
}
