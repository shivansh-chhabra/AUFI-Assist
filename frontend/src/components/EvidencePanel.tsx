import { contentTypeLabel } from '../conditions';
import type { EvidenceData, Source } from '../types';

interface EvidencePanelProps {
  evidence: EvidenceData;
  onOpenSource: (source: Source) => void;
}

export default function EvidencePanel({ evidence, onOpenSource }: EvidencePanelProps) {
  const { sources, sourceCount, chunkCount, retrievalMs, documentsInIndex, droppedBelowThreshold, filters } = evidence;
  const nothingFound = sources.length === 0;

  return (
    <div className="evidence-block">
      <div className="evidence-header">
        <div>
          <div className={`evidence-title${nothingFound ? ' evidence-title--none' : ''}`}>
            {nothingFound ? 'No close guideline match' : 'Guideline sources'}
          </div>
          <div className="evidence-meta">
            {nothingFound
              ? 'Nothing retrieved was close enough to the question, so no medical claim is made.'
              : `${sourceCount} ${sourceCount === 1 ? 'passage' : 'passages'} · local vector search and rerank · ${retrievalMs} ms`}
          </div>
        </div>
        {!nothingFound && <span className="state-badge verified">Real guideline text only</span>}
      </div>

      <div className="evidence-body">
        {!nothingFound && (
          <div className="source-grid">
            {sources.map((s) => (
              <button
                className="source-card"
                key={s.id}
                onClick={() => onOpenSource(s)}
                type="button"
              >
                <div className="src-top">
                  <span className="src-num">{s.id}</span>
                  {s.body && <span className="tag tag--body">{s.body}</span>}
                </div>
                <div className="src-title">{s.title}</div>
                <div className="src-loc">{s.location}</div>
                <div className="src-tags">
                  {s.disease && <span className="tag">{s.disease}</span>}
                  {s.contentType && <span className="tag">{contentTypeLabel(s.contentType)}</span>}
                </div>
                <div className="src-link">Preview source</div>
              </button>
            ))}
          </div>
        )}

        <details className="why-toggle" style={nothingFound ? { marginTop: 0, paddingTop: 0, borderTop: 'none' } : undefined}>
          <summary className="why-summary">
            <span className="chev">▶</span> How these were found
          </summary>
          <div className="why-content">
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
            <div className="why-row">
              <b>Scoring table</b>
              <span>Not searchable. It only ranks conditions and picks questions.</span>
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
