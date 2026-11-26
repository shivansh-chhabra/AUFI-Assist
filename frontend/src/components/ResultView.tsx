import { useEffect, useMemo, useState } from 'react';
import EvidencePanel from './EvidencePanel';
import RichText from './RichText';
import { groupSources } from '../utils/sourceDocs';
import type { ChatMessage, ContentType, ExplanationSection, Source } from '../types';

type View = 'summary' | 'tests' | 'others' | 'ask';

interface ResultViewProps {
  /** The message that carries the result (candidates, explanation, evidence). */
  result: ChatMessage;
  /** Questions asked after the result, each with its answer (the answer is absent while loading). */
  qa: { question: string; answer?: ChatMessage }[];
  isLoading: boolean;
  liveSteps: string[];
  reportUrl?: string;
  onOpenSource: (s: Source) => void;
}

const pct = (p: number) => `${Math.round(p * 100)}%`;

/**
 * The result, one topic at a time: a short summary, then buttons for the recommended tests, the
 * other likely conditions, and the PDF. Nothing here needs scrolling to find the next thing.
 */
export default function ResultView({ result, qa, isLoading, liveSteps, reportUrl, onOpenSource }: ResultViewProps) {
  const [view, setView] = useState<View>('summary');
  const candidates = useMemo(() => [...(result.candidates ?? [])].sort((a, b) => b.probability - a.probability), [result]);
  const explanation = result.explanation ?? [];
  const sources = result.evidence?.sources ?? [];
  const { docOf } = useMemo(() => groupSources(sources, explanation), [sources, explanation]);

  const lead = candidates[0];
  const others = candidates.slice(1);
  const [otherId, setOtherId] = useState<string>('');
  const [testId, setTestId] = useState<string>('');
  const shortlist = explanation.filter((e) => e.sections.some((s) => s.contentType === 'confirmatory_tests'));

  // A new question jumps to the answers.
  useEffect(() => {
    if (qa.length > 0) setView('ask');
  }, [qa.length]);

  const section = (id: string, type: ContentType) =>
    explanation.find((e) => e.diseaseId === id)?.sections.find((s) => s.contentType === type);

  const cites = (s: ExplanationSection) => {
    const chips: { num: number; src: Source }[] = [];
    for (const id of s.citations) {
      const doc = docOf.get(id);
      const src = sources.find((x) => x.id === id);
      if (doc && src && !chips.some((c) => c.num === doc.num)) chips.push({ num: doc.num, src });
    }
    chips.sort((a, b) => a.num - b.num);
    return chips.length ? (
      <div className="cite-row">
        <span>Sources</span>
        {chips.map((c) => (
          <button key={c.num} className="cite" type="button" onClick={() => onOpenSource(c.src)} aria-label={`Open source ${c.num}`}>
            {c.num}
          </button>
        ))}
      </div>
    ) : null;
  };

  const infoOf = (id: string) => explanation.find((e) => e.diseaseId === id)?.info;

  /** The fixed, hand-written summary of a condition: what it is, what causes it, how to prevent it. */
  const infoBlocks = (id: string) => {
    const i = infoOf(id);
    return i ? (
      <>
        <div className="result-block">
          <h3>What it is</h3>
          <RichText text={i.summary} />
        </div>
        <div className="result-block">
          <h3>Cause and spread</h3>
          <RichText text={`**Caused by:** ${i.causativeAgent}\n\n**How it spreads:** ${i.transmission}`} />
        </div>
        <div className="result-block">
          <h3>How to prevent it</h3>
          <RichText text={i.preventiveMethods.map((m) => `- ${m}`).join('\n')} />
        </div>
      </>
    ) : null;
  };

  const leadId = lead?.id ?? '';
  const activeTest = testId || shortlist[0]?.diseaseId || '';
  const activeOther = otherId || others[0]?.id || '';
  const otherC = others.find((c) => c.id === activeOther);

  const nav: { id: View; label: string }[] = [
    { id: 'summary', label: 'Summary' },
    { id: 'tests', label: 'Recommended tests' },
    { id: 'others', label: 'Other likely conditions' },
  ];

  return (
    <div className="result">
      <div className="result-top">
        <div>
          <div className="result-kicker">Most likely</div>
          <h2 className="result-lead">{lead?.name ?? 'Result'}</h2>
        </div>
        {lead && <div className="result-pct">{pct(lead.probability)}</div>}
      </div>

      <nav className="result-nav" aria-label="Result sections">
        {nav.map((n) => (
          <button key={n.id} className={`rbtn${view === n.id ? ' on' : ''}`} onClick={() => setView(n.id)} type="button">
            {n.label}
          </button>
        ))}
        {qa.length > 0 && (
          <button className={`rbtn${view === 'ask' ? ' on' : ''}`} onClick={() => setView('ask')} type="button">
            Your questions
          </button>
        )}
        {reportUrl ? (
          <a className="rbtn rbtn--end" href={reportUrl} download>
            Download PDF
          </a>
        ) : (
          <button className="rbtn rbtn--end" onClick={() => window.print()} type="button">
            Print / save as PDF
          </button>
        )}
      </nav>

      <div className="result-body">
        {view === 'summary' && (
          <>
            {lead && infoBlocks(leadId)}
            {!infoOf(leadId) && <p className="result-muted">No summary could be prepared for this condition.</p>}
            {others.length > 0 && (
              <p className="result-also">
                Also possible:{' '}
                {others.slice(0, 3).map((c, i) => (
                  <span key={c.id}>
                    {i > 0 && ', '}
                    <b>{c.name}</b> {pct(c.probability)}
                  </span>
                ))}
                .
              </p>
            )}
            <p className="result-note">
              This is a shortlist to confirm with a doctor and tests. It is not a diagnosis.
            </p>
          </>
        )}

        {view === 'tests' && (
          <>
            {shortlist.length > 1 && (
              <div className="result-tabs" role="tablist">
                {shortlist.map((e) => (
                  <button key={e.diseaseId} role="tab" aria-selected={e.diseaseId === activeTest} className={e.diseaseId === activeTest ? 'on' : ''} onClick={() => setTestId(e.diseaseId)} type="button">
                    {e.disease}
                    <span> {pct(candidates.find((c) => c.id === e.diseaseId)?.probability ?? 0)}</span>
                  </button>
                ))}
              </div>
            )}
            {activeTest ? (
              (() => {
                const s = section(activeTest, 'confirmatory_tests');
                return s ? (
                  <div className="result-block">
                    <RichText text={s.text} />
                    {cites(s)}
                  </div>
                ) : null;
              })()
            ) : (
              <p className="result-muted">No test recommendations are available for this case.</p>
            )}
            {result.evidence && <EvidencePanel evidence={result.evidence} explanation={explanation} onOpenSource={onOpenSource} />}
          </>
        )}

        {view === 'others' && (
          <div className="others">
            <ul className="others-list">
              {others.map((c) => (
                <li key={c.id}>
                  <button className={c.id === activeOther ? 'on' : ''} onClick={() => setOtherId(c.id)} type="button">
                    <span>{c.name}</span>
                    <b>{pct(c.probability)}</b>
                  </button>
                </li>
              ))}
            </ul>
            <div className="others-detail">
              {otherC && (
                <>
                  <h3 className="others-name">{otherC.name}</h3>
                  {infoOf(activeOther) ? (
                    <>
                      {infoBlocks(activeOther)}
                      {section(activeOther, 'confirmatory_tests') && (
                        <button className="result-link" onClick={() => { setTestId(activeOther); setView('tests'); }} type="button">
                          See the recommended tests for {otherC.name}
                        </button>
                      )}
                    </>
                  ) : (
                    <p className="result-muted">No summary could be prepared for this condition. You can ask about it below.</p>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        {view === 'ask' && (
          <div className="ask">
            {qa.map((x, i) => {
              const ans = x.answer;
              const open = (n: number) => {
                const src = ans?.evidence?.sources.find((s) => s.id === n);
                if (src) onOpenSource(src);
              };
              return (
                <div className="ask-item" key={i}>
                  <div className="ask-q">{x.question}</div>
                  {ans ? (
                    <>
                      <RichText text={ans.text} onCite={open} />
                    </>
                  ) : (
                    <div className="ask-wait">{liveSteps[liveSteps.length - 1] ?? 'Looking in the guidelines…'}</div>
                  )}
                </div>
              );
            })}
            {isLoading && qa.every((x) => x.answer) && <div className="ask-wait">Looking in the guidelines…</div>}
            <p className="result-note">General information from ICMR and MoHFW guidelines, not personal medical advice.</p>
          </div>
        )}
      </div>
    </div>
  );
}
