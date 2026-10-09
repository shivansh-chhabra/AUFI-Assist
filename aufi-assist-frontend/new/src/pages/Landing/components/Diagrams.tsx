import { motion, useReducedMotion, useMotionValue, useTransform, animate } from 'framer-motion';
import { useEffect, useState } from 'react';

const nodeIn = {
  hidden: { opacity: 0, y: 6 },
  show: (i: number) => ({ opacity: 1, y: 0, transition: { duration: 0.6, delay: 0.42 + i * 0.08 } }),
};

const LOOP_STAGES = ['Intake', 'Score', 'Ask', 'Repeat', 'Explain'];

interface AgentLoopDiagramProps {
  activeIndex: number;
  onSelect: (i: number) => void;
}

/** Circular plan → act → observe loop. A dot continuously travels the ring
 *  and the node it is currently passing is highlighted in real time.
 *  Clicking a node re-starts the dot from that stage. */
export function AgentLoopDiagram({ activeIndex, onSelect }: AgentLoopDiagramProps) {
  const reduced = useReducedMotion();
  const cx = 190, cy = 190, r = 138;
  const n = LOOP_STAGES.length;
  const points = LOOP_STAGES.map((label, i) => {
    const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
    return { label, x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
  });

  const progress = useMotionValue(0);
  const [visited, setVisited] = useState(activeIndex);

  const dotX = useTransform(progress, (p) => {
    const angle = ((activeIndex / n) + p) * Math.PI * 2 - Math.PI / 2;
    return cx + r * Math.cos(angle);
  });
  const dotY = useTransform(progress, (p) => {
    const angle = ((activeIndex / n) + p) * Math.PI * 2 - Math.PI / 2;
    return cy + r * Math.sin(angle);
  });

  useEffect(() => {
    progress.set(0);
    setVisited(activeIndex);
    if (reduced) return;
    const controls = animate(progress, 1, { duration: 9, ease: 'linear', repeat: Infinity });
    return () => controls.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeIndex, reduced]);

  useEffect(() => {
    const unsub = progress.on('change', (p) => {
      const idx = (activeIndex + Math.round(p * n)) % n;
      setVisited((prev) => (prev === idx ? prev : idx));
    });
    return unsub;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeIndex]);

  return (
    <svg viewBox="0 0 380 380" width="100%" role="img" aria-label="Question loop: intake, score, ask, repeat, then explain">
      <motion.circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--line-strong)" strokeWidth={1} strokeDasharray="2 6" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} transition={{ duration: 0.75 }} />
      {points.map((p, i) => {
        const isVisited = i === visited;
        return (
          <motion.g
            key={p.label}
            custom={i}
            variants={nodeIn}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, amount: 0.6 }}
            onClick={() => onSelect(i)}
            style={{ cursor: 'pointer' }}
          >
            <circle cx={p.x} cy={p.y} r={24} fill="transparent" />
            <circle
              cx={p.x} cy={p.y} r={22}
              fill={isVisited ? 'var(--brass-dim)' : 'var(--bg-2)'}
              stroke={isVisited ? 'var(--brass)' : 'var(--line-strong)'}
              strokeWidth={isVisited ? 1.8 : 1.2}
              style={{ transition: 'fill 0.35s ease, stroke 0.35s ease' }}
            />
            <text x={p.x} y={p.y + 4} fill={isVisited ? 'var(--brass)' : 'var(--ink)'} fontSize="11.5" fontFamily="var(--mono)" fontStyle="italic" fontWeight={isVisited ? 500 : 300} textAnchor="middle">{String(i + 1).padStart(2, '0')}</text>
          </motion.g>
        );
      })}
      <text x={cx} y={cy + 5} fill="var(--ink)" fontSize="16" fontFamily="var(--display)" fontWeight={700} textAnchor="middle">Question loop</text>
      {!reduced && (
        <motion.circle r={3.5} fill="var(--brass-soft)" style={{ cx: dotX, cy: dotY }} />
      )}
    </svg>
  );
}

type Level = 0 | 1 | 2;
const OVERLAP_COLS = ['Fever', 'Headache', 'Body ache', 'Nausea', 'Chills', 'Rash'];
const OVERLAP_ROWS: { name: string; levels: Level[] }[] = [
  { name: 'Malaria', levels: [2, 2, 2, 1, 2, 0] },
  { name: 'Dengue', levels: [2, 2, 2, 2, 1, 1] },
  { name: 'Typhoid fever', levels: [2, 2, 1, 1, 1, 0] },
  { name: 'Scrub typhus', levels: [2, 2, 2, 1, 2, 1] },
  { name: 'Leptospirosis', levels: [2, 2, 2, 1, 1, 0] },
];
const LEVEL_LABEL = ['uncommon', 'sometimes', 'common'];

/** Early-symptom overlap between five of the conditions. Illustrative, not data from the scoring table. */
export function SymptomOverlap() {
  return (
    <div className="overlap">
      <table>
        <caption className="overlap__caption">How early symptoms overlap (illustrative)</caption>
        <thead>
          <tr>
            <th scope="col"><span className="sr-only">Condition</span></th>
            {OVERLAP_COLS.map((c) => (
              <th scope="col" key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {OVERLAP_ROWS.map((r) => (
            <tr key={r.name}>
              <th scope="row">{r.name}</th>
              {r.levels.map((l, i) => (
                <td key={i}>
                  <span className={`dotlvl dotlvl--${l}`} role="img" aria-label={LEVEL_LABEL[l]} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="overlap__legend">
        <span><span className="dotlvl dotlvl--2" aria-hidden="true" /> common</span>
        <span><span className="dotlvl dotlvl--1" aria-hidden="true" /> sometimes</span>
        <span><span className="dotlvl dotlvl--0" aria-hidden="true" /> uncommon</span>
      </div>
    </div>
  );
}
