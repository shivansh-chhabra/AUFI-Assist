import { useEffect, useRef, useState } from 'react';
import { IconSend } from './Icons';

interface ComposerProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  /** True while a follow-up question is waiting on an answer. */
  awaitingAnswer?: boolean;
}

export default function Composer({ onSend, disabled, awaitingAnswer }: ComposerProps) {
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!disabled) inputRef.current?.focus();
  }, [disabled]);

  const handleSend = () => {
    if (disabled || !value.trim()) return;
    onSend(value.trim());
    setValue('');
  };

  return (
    <div className="composer-wrap">
      <div className="composer">
        <div className="composer-box">
          <textarea
            className="composer-input"
            placeholder={awaitingAnswer ? 'Or answer in your own words…' : 'Describe the fever and any other symptoms…'}
            aria-label="Message"
            rows={1}
            ref={inputRef}
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
