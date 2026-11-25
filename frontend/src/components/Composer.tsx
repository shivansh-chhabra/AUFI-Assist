import { useState } from 'react';
import { IconSend } from './Icons';

interface ComposerProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  /** True while a follow-up question is waiting on an answer. */
  awaitingAnswer?: boolean;
  /** Slimmer box, used under the question screen. */
  compact?: boolean;
}

export default function Composer({ onSend, disabled, awaitingAnswer, compact }: ComposerProps) {
  const [value, setValue] = useState('');

  const handleSend = () => {
    if (disabled || !value.trim()) return;
    onSend(value.trim());
    setValue('');
  };

  return (
    <div className="composer-wrap">
      <div className="composer">
        {/* No autofocus on purpose: the grey box already shows where to type. */}
        <div className={`composer-box${compact ? ' composer-box--compact' : ''}`}>
          <textarea
            className="composer-input"
            placeholder={awaitingAnswer ? 'Or answer in your own words…' : 'Describe the fever and any other symptoms…'}
            aria-label="Message"
            rows={compact ? 2 : 3}
            value={value}
            disabled={disabled}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
          />
          <button
            className="composer-send"
            onClick={handleSend}
            aria-label="Send message"
            disabled={disabled || !value.trim()}
          >
            <IconSend />
          </button>
        </div>

        <div className="composer-hint">
          Runs on this machine. Decision support only, not a diagnosis.
        </div>
      </div>
    </div>
  );
}
