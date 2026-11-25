import type { DiseaseExplanation, Source } from '../types';

/** One guideline document, with every cited page/section of it merged into a single entry. */
export interface SourceDoc {
  key: string;
  /** 1-based rank shown to the patient (1 = most relevant). */
  num: number;
  title: string;
  body?: Source['body'];
  locations: string[];
  /** The source to open for this document (the most relevant passage). */
  primary: Source;
  sources: Source[];
  cited: number;
}

const docKey = (s: Source) => s.file ?? s.title;

/**
 * Collapses the raw source list (one entry per cited passage, so often 20+) into one entry per
 * document, ranked by how much of the explanation relies on it.
 */
export function groupSources(sources: Source[], explanation?: DiseaseExplanation[] | null) {
  const citedIds = new Map<number, number>();
  for (const d of explanation ?? []) {
    for (const sec of d.sections) {
      for (const id of new Set(sec.citations)) citedIds.set(id, (citedIds.get(id) ?? 0) + 1);
    }
  }

  const groups = new Map<string, Source[]>();
  for (const s of sources) {
    const k = docKey(s);
    groups.set(k, [...(groups.get(k) ?? []), s]);
  }

  const docs = [...groups.entries()]
    .map(([key, list]) => {
      const best = [...list].sort(
        (a, b) => (citedIds.get(b.id) ?? 0) - (citedIds.get(a.id) ?? 0) || (b.relevance ?? 0) - (a.relevance ?? 0) || a.id - b.id
      )[0];
      return {
        key,
        title: best.title,
        body: best.body,
        locations: [...new Set(list.map((s) => s.location).filter(Boolean))],
        primary: best,
        sources: list,
        cited: list.reduce((n, s) => n + (citedIds.get(s.id) ?? 0), 0),
        rel: Math.max(...list.map((s) => s.relevance ?? 0)),
        first: Math.min(...list.map((s) => s.id)),
      };
    })
    .sort((a, b) => b.cited - a.cited || b.rel - a.rel || a.first - b.first)
    .map(({ rel: _r, first: _f, ...d }, i): SourceDoc => ({ ...d, num: i + 1 }));

  const docOf = new Map<number, SourceDoc>();
  for (const d of docs) for (const s of d.sources) docOf.set(s.id, d);
  return { docs, docOf };
}
