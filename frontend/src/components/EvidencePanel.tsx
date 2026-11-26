import { useMemo, useState } from 'react';
import { contentTypeLabel } from '../conditions';
import { groupSources } from '../utils/sourceDocs';
import type { DiseaseExplanation, EvidenceData, Source } from '../types';

interface EvidencePanelProps {
  evidence: EvidenceData;
  explanation?: DiseaseExplanation[] | null;
  onOpenSource: (source: Source) => void;
}

const TOP_N = 5;

export default function EvidencePanel({ evidence, explanation, onOpenSource }: EvidencePanelProps) {
  const { sources, chunkCount, documentsInIndex, droppedBelowThreshold, filters } = evidence;
  const nothingFound = sources.length === 0;
  const [showAll, setShowAll] = useState(false);
  const { docs } = useMemo(() => groupSources(sources, explanation), [sources, explanation]);
  const shown = showAll ? docs : docs.slice(0, TOP_N);

  return (
    <div className="evidence-block">
      {nothingFound ? (
        <div className="evidence-header">
          <div>
            <div className="evidence-title evidence-title--none">No close guideline match</div>
            <div className="evidence-meta">
              Nothing retrieved was close enough to the question, so no medical claim is made.
            </div>
          </div>
        </div>
      ) : (
        <details className="src-drop">
          <summary className="src-drop__summary">
            <span className="chev">▶</span>
            <span className="src-drop__title">Sources behind the recommended tests</span>
            <span className="src-drop__count">
              {docs.length} {docs.length === 1 ? 'guideline' : 'guidelines'}
            </span>
          </summary>
          <div className="src-drop__body">
            <p className="src-drop__note">
              The most relevant {Math.min(TOP_N, docs.length)} are listed first. The numbers match the ones beside each part of the summary.
            </p>
            <ul className="src-list">
              {shown.map((d) => (
                <li key={d.key}>
                  <button className="src-row" onClick={() => onOpenSource(d.primary)} type="button">
                    <span className="src-num">{d.num}</span>
                    <span className="src-row__text">
                      <span className="src-row__title">{d.title}</span>
                      <span className="src-row__loc">
                        {d.locations.slice(0, 3).join(' · ')}
                        {d.locations.length > 3 ? ` · +${d.locations.length - 3} more` : ''}
                      </span>
                    </span>
                    {d.body && <span className="tag tag--body">{d.body}</span>}
                    <span className="src-link">Open</span>
                  </button>
                </li>
              ))}
            </ul>
            {docs.length > TOP_N && (
              <button className="src-more" onClick={() => setShowAll((v) => !v)} type="button">
                {showAll ? 'Show fewer' : `Show all ${docs.length}`}
              </button>
            )}
          </div>
        </details>
      )}

      <div className="evidence-body">
        <details className="why-toggle" style={nothingFound ? { marginTop: 0, paddingTop: 0, borderTop: 'none' } : undefined}>
          <summary className="why-summary">
            <span className="chev">▶</span> How these were found
          </summary>
          <div className="why-content">
            {chunkCount > 0 && (<>
            <div className="why-row">
              <b>Searched</b>
              <span>
                {filters && filters.length > 0
                  ? filters.map((f) => `${f.disease} (${contentTypeLabel(f.contentType).toLowerCase()})`).join(', ')
                  : `${documentsInIndex} guideline documents`}
              </span>
            </div>
            <div className="why-row">
              <b>Kept</b>
              <span>
                {chunkCount} {chunkCount === 1 ? 'passage' : 'passages'} above the relevance threshold
                {droppedBelowThreshold ? `, ${droppedBelowThreshold} dropped` : ''}
              </span>
            </div>
            </>)}
            <div className="why-row">
              <b>Recommended tests</b>
              <span>Taken from the fixed ICMR and MoHFW test protocol, not searched.</span>
            </div>
            <div className="why-row">
              <b>External sources</b>
              <span>None. Internet disabled.</span>
            </div>
          </div>
        </details>
      </div>
    </div>
  );
}
