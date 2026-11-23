import { useEffect, useRef, useState } from 'react';
import { motion, useInView, useReducedMotion } from 'framer-motion';

type Row = [name: string, pct: number];

interface Step {
  label: string;
  question?: string;
  answer?: string;
  rows: Row[];
  other: number;
}

// Illustrative numbers, matching the scripted demo case in the workbench.
const STEPS: Step[] = [
  { label: 'Symptoms', answer: 'Fever for three days with body ache', other: 19,
    rows: [['Dengue', 22], ['Viral influenza-like illness', 18], ['Malaria', 14], ['Typhoid fever', 11], ['Chikungunya', 9], ['Scrub typhus', 7]] },
  { label: 'Chills', question: 'Chills and shaking in a repeating pattern?', answer: 'No', other: 16,
    rows: [['Dengue', 27], ['Viral influenza-like illness', 21], ['Malaria', 4], ['Typhoid fever', 12], ['Chikungunya', 12], ['Scrub typhus', 8]] },
  { label: 'Rash', question: 'Any rash, or bleeding from gums or nose?', answer: 'Yes', other: 10,
    rows: [['Dengue', 44], ['Viral influenza-like illness', 6], ['Malaria', 2], ['Typhoid fever', 8], ['Chikungunya', 20], ['Scrub typhus', 10]] },
  { label: 'Joints', question: 'Joint pain severe enough to limit movement?', answer: 'Yes', other: 3,
    rows: [['Dengue', 47], ['Viral influenza-like illness', 1], ['Malaria', 1], ['Typhoid fever', 2], ['Chikungunya', 43], ['Scrub typhus', 3]] },
];

const INTERVAL = 3200;

/** Auto-playing walkthrough of one case narrowing from 11 candidates to 2. */
export function NarrowingDemo() {
  const reduced = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { amount: 0.4 });
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(true);

  useEffect(() => {
    if (!playing || reduced || !inView) return;
    const id = setTimeout(() => setStep((s) => (s + 1) % STEPS.length), step === STEPS.length - 1 ? INTERVAL + 1800 : INTERVAL);
    return () => clearTimeout(id);
  }, [step, playing, reduced, inView]);

  const current = STEPS[step];
  const sorted = [...current.rows].sort((a, b) => b[1] - a[1]);
  const done = step === STEPS.length - 1;

  return (
    <div className="narrow" ref={ref}>
      <div className="narrow__talk" aria-live="polite">
        {STEPS.slice(0, step + 1).map((s, i) => (
          <motion.div
            key={s.label}
            className="narrow__turn"
            initial={reduced ? false : { opacity: 0, y: 8 }}
            animate={{ opacity: i === step ? 1 : 0.55, y: 0 }}
            transition={{ duration: 0.45 }}
          >
            {s.question && <div className="narrow__q">{s.question}</div>}
            <div className="narrow__a">{s.answer}</div>
          </motion.div>
        ))}
        {done && (
          <motion.div className="narrow__stop" initial={reduced ? false : { opacity: 0 }} animate={{ opacity: 1 }}>
            Two conditions left. Explaining both from the guidelines.
          </motion.div>
        )}
      </div>

      <div className="narrow__bars">
        <ul>
          {sorted.map(([name, pct], i) => (
            <motion.li
              key={name}
              layout={!reduced}
              transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              className={`narrow__row${i === 0 || (done && i === 1) ? ' narrow__row--lead' : ''}`}
            >
              <span className="narrow__name">{name}</span>
              <span className="narrow__bar" aria-hidden="true">
                <motion.span
                  initial={false}
                  animate={{ width: `${Math.max(1, pct)}%` }}
                  transition={{ duration: reduced ? 0 : 0.6, ease: [0.16, 1, 0.3, 1] }}
                />
              </span>
              <span className="narrow__pct">{pct}%</span>
            </motion.li>
          ))}
        </ul>
        <div className="narrow__other">Other 5 conditions together: {current.other}%</div>
      </div>

      <div className="narrow__controls">
        {STEPS.map((s, i) => (
          <button
            key={s.label}
            className={`narrow__step${i === step ? ' on' : ''}`}
            onClick={() => { setStep(i); setPlaying(false); }}
            aria-current={i === step}
            type="button"
          >
            {s.label}
          </button>
        ))}
        {!reduced && (
          <button className="narrow__play" onClick={() => setPlaying((p) => !p)} type="button">
            {playing ? 'Pause' : 'Play'}
          </button>
        )}
        <span className="narrow__note">Illustrative numbers</span>
      </div>
    </div>
  );
}
