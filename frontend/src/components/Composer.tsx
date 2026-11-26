import { useEffect, useRef, useState } from 'react';
import { IconSend } from './Icons';

interface ComposerProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function Composer({ onSend, disabled, placeholder }: ComposerProps) {
  const [value, setValue] = useState('');
  const ref = useRef<HTMLTextAreaElement>(null);

  // Grow with the text, up to about four lines.
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 112)}px`;
  }, [value]);

  const handleSend = () => {
    if (disabled || !value.trim()) return;
    onSend(value.trim());
    setValue('');
  };

  return (
    <div className="composer-wrap">
      <div className="composer">
        {/* No autofocus on purpose: the grey box already shows where to type. */}
        <div className="composer-box">
          <textarea
            ref={ref}
            className="composer-input"
            placeholder={placeholder ?? 'Describe the fever and any other symptoms…'}
            aria-label="Message"
            rows={1}
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
          <button className="composer-send" onClick={handleSend} aria-label="Send message" disabled={disabled || !value.trim()}>
            <IconSend />
          </button>
        </div>
        <div className="composer-hint">Runs on this machine. Decision support only, not a diagnosis.</div>
      </div>
    </div>
  );
}
