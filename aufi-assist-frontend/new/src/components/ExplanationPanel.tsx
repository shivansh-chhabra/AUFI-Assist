import { useState } from 'react';
import { contentTypeLabel } from '../conditions';
import type { DiseaseExplanation, Source } from '../types';

interface ExplanationPanelProps {
  explanation: DiseaseExplanation[];
  sources: Source[];
  onOpenSource: (source: Source) => void;
}

/** The grounded explanation for each shortlisted disease, one tab per disease. */
export default function ExplanationPanel({ explanation, sources, onOpenSource }: ExplanationPanelProps) {
  const [active, setActive] = useState(0);
  const current = explanation[Math.min(active, explanation.length - 1)];
  if (!current) return null;

  const byId = new Map(sources.map((s) => [s.id, s]));

  return (
    <div className="expl-panel">
      <div className="expl-head">
        <div className="expl-title">From the guidelines</div>
        <div className="expl-tag">Every statement is cited</div>
      </div>

      {explanation.length > 1 && (
        <div className="expl-tabs" role="tablist">
          {explanation.map((d, i) => (
            <button
              key={d.diseaseId}
              className="expl-tab"
              role="tab"
              aria-selected={i === active}
              onClick={() => setActive(i)}
              type="button"
            >
              {d.disease}
            </button>
          ))}
        </div>
      )}

      <div className="expl-body" role="tabpanel">
        {explanation.length === 1 && <h3 className="expl-disease">{current.disease}</h3>}
        {current.sections.map((s) => (
          <div className="expl-section" key={s.contentType}>
            <h4>{contentTypeLabel(s.contentType)}</h4>
            <p>
              {s.text}
              {s.citations.map((id) => {
                const src = byId.get(id);
                return (
                  <button
                    key={id}
                    className="cite"
                    onClick={() => src && onOpenSource(src)}
                    disabled={!src}
                    aria-label={src ? `Open source ${id}: ${src.title}, ${src.location}` : `Source ${id}`}
                    type="button"
                  >
                    {id}
                  </button>
                );
              })}
            </p>
          </div>
        ))}
      </div>

      <div className="expl-foot">
        Decision support for clinicians. This is a shortlist to confirm with tests, not a diagnosis.
      </div>
    </div>
  );
}
