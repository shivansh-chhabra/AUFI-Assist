import { useMemo, useState } from 'react';
import { contentTypeLabel } from '../conditions';
import { groupSources } from '../utils/sourceDocs';
import RichText from './RichText';
import type { DiseaseExplanation, Source } from '../types';

interface ExplanationPanelProps {
  explanation: DiseaseExplanation[];
  sources: Source[];
  onOpenSource: (source: Source) => void;
  /** Backend PDF endpoint for this case; when absent the button prints the page instead. */
  reportUrl?: string;
}

/** The grounded explanation for each shortlisted disease, one tab per disease. */
export default function ExplanationPanel({ explanation, sources, onOpenSource, reportUrl }: ExplanationPanelProps) {
  const [active, setActive] = useState(0);
  const { docOf } = useMemo(() => groupSources(sources, explanation), [sources, explanation]);
  const current = explanation[Math.min(active, explanation.length - 1)];
  if (!current) return null;

  return (
    <div className="expl-panel">
      <div className="expl-head">
        <div className="expl-title">From the guidelines</div>
        <div className="expl-tag">Every statement is cited</div>
        {reportUrl ? (
          <a className="expl-print" href={reportUrl} download>
            Download PDF
          </a>
        ) : (
          <button className="expl-print" onClick={() => window.print()} type="button">
            Print / save as PDF
          </button>
        )}
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
        {current.sections.map((s) => {
          // One chip per document (not per passage), opening the passage this section actually cites.
          const chips: { num: number; src: Source; title: string }[] = [];
          for (const id of s.citations) {
            const doc = docOf.get(id);
            const src = sources.find((x) => x.id === id);
            if (doc && src && !chips.some((c) => c.num === doc.num)) chips.push({ num: doc.num, src, title: doc.title });
          }
          chips.sort((a, b) => a.num - b.num);
          return (
            <div className="expl-section" key={s.contentType}>
              <h4>{contentTypeLabel(s.contentType)}</h4>
              <RichText text={s.text} />
              {chips.length > 0 && (
                <div className="cite-row">
                  <span>Sources</span>
                  {chips.map((c) => (
                    <button
                      key={c.num}
                      className="cite"
                      onClick={() => onOpenSource(c.src)}
                      aria-label={`Open source ${c.num}: ${c.title}, ${c.src.location}`}
                      title={`${c.title} (${c.src.location})`}
                      type="button"
                    >
                      {c.num}
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="expl-foot">
        Decision support only. This is a shortlist to confirm with a clinician and tests, not a diagnosis.
      </div>
    </div>
  );
}
