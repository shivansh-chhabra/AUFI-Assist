import { useEffect, useState } from 'react';
import type { Candidate } from '../types';

interface CandidatePanelProps {
  candidates: Candidate[];
  /** Open by default for the latest answer; older ones collapse when a new answer arrives. */
  isLatest: boolean;
}

const VISIBLE = 5;

function pct(p: number): string {
  if (p > 0 && p < 0.01) return '<1%';
  return `${Math.round(p * 100)}%`;
}

function Delta({ now, before }: { now: number; before?: number }) {
  if (before == null) return null;
  const diff = Math.round((now - before) * 100);
  if (diff === 0) return null;
  return (
    <span className={`cand-delta ${diff > 0 ? 'up' : 'down'}`} aria-label={`${diff > 0 ? 'up' : 'down'} ${Math.abs(diff)} points`}>
      {diff > 0 ? '+' : '−'}{Math.abs(diff)}
    </span>
  );
}

export default function CandidatePanel({ candidates, isLatest }: CandidatePanelProps) {
  const [open, setOpen] = useState(isLatest);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    if (!isLatest) setOpen(false);
  }, [isLatest]);

  const sorted = [...candidates].sort((a, b) => b.probability - a.probability);
  const shown = showAll ? sorted : sorted.slice(0, VISIBLE);
  const lead = sorted[0];
  const hidden = sorted.length - shown.length;

  return (
    <div className="cand-panel">
      <button className="cand-head" onClick={() => setOpen((o) => !o)} aria-expanded={open} type="button">
        <span>
          <span className="cand-title">Likely conditions</span>
          <span className="cand-sub">
            {lead ? `Leading: ${lead.name}, ${pct(lead.probability)}` : 'No candidates'}
          </span>
        </span>
        <span className={`chev${open ? ' open' : ''}`} aria-hidden="true">▶</span>
      </button>

      {open && (
        <>
          <ul className="cand-list">
            {shown.map((c, i) => (
              <li
                key={c.id}
                className={`cand-row${c.shortlisted ? ' cand-row--short' : i === 0 ? ' cand-row--lead' : ''}`}
              >
                <span className="cand-name">{c.name}</span>
                <span className="cand-bar" aria-hidden="true">
                  <span style={{ width: `${Math.max(1, c.probability * 100)}%` }} />
                </span>
                <span className="cand-val">
                  {pct(c.probability)}
                  <Delta now={c.probability} before={c.previous} />
                </span>
              </li>
            ))}
          </ul>
          {sorted.length > VISIBLE && (
            <button className="cand-more" onClick={() => setShowAll((s) => !s)} type="button">
              {showAll ? 'Show fewer' : `Show ${hidden} more`}
            </button>
          )}
        </>
      )}
    </div>
  );
}
