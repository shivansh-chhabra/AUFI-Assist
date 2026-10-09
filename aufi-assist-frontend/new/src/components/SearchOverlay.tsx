import { useEffect, useRef, useState } from 'react';
import { IconSearch, IconFile } from './Icons';
import DocumentPreviewModal from './DocumentPreviewModal';
import { searchDocuments } from '../api/client';
import { CONDITIONS, CONTENT_TYPES, contentTypeLabel } from '../conditions';
import type { ContentType, SearchResult } from '../types';

interface SearchOverlayProps {
  onClose: () => void;
}

export default function SearchOverlay({ onClose }: SearchOverlayProps) {
  const [query, setQuery] = useState('');
  const [disease, setDisease] = useState('');
  const [contentType, setContentType] = useState<ContentType | ''>('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [previewResult, setPreviewResult] = useState<SearchResult | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (previewResult) setPreviewResult(null);
        else onClose();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose, previewResult]);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setHasSearched(false);
      return;
    }
    setIsSearching(true);
    let stale = false;
    const handle = setTimeout(() => {
      searchDocuments(query, { disease: disease || undefined, contentType: contentType || undefined })
        .then((r) => {
          if (stale) return;
          setResults(r);
          setHasSearched(true);
        })
        .catch(() => {
          if (stale) return;
          setResults([]);
          setHasSearched(true);
        })
        .finally(() => {
          if (!stale) setIsSearching(false);
        });
    }, 220);
    return () => {
      stale = true;
      clearTimeout(handle);
    };
  }, [query, disease, contentType]);

  return (
    <div className="search-overlay" role="dialog" aria-modal="true" aria-label="Search the guidelines">
      <div className="search-overlay__backdrop" onClick={onClose} />
      <div className="search-overlay__panel">
        <div className="search-overlay__input-row">
          <span className="search-overlay__icon"><IconSearch /></span>
          <input
            ref={inputRef}
            className="search-overlay__input"
            placeholder="Search the ICMR and MoHFW guidelines…"
            aria-label="Search the guidelines"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="search-overlay__close" onClick={onClose} aria-label="Close search">Esc</button>
        </div>

        <div className="search-filters">
          <select value={disease} onChange={(e) => setDisease(e.target.value)} aria-label="Filter by condition">
            <option value="">All conditions</option>
            {CONDITIONS.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <select value={contentType} onChange={(e) => setContentType(e.target.value as ContentType | '')} aria-label="Filter by content type">
            <option value="">All content</option>
            {CONTENT_TYPES.map((c) => (
              <option key={c.id} value={c.id}>{c.label}</option>
            ))}
          </select>
        </div>

        <div className="search-overlay__results">
          {!hasSearched && !isSearching && (
            <div className="search-overlay__empty">Type a symptom, test or treatment to search the guideline text.</div>
          )}
          {isSearching && <div className="search-overlay__empty">Searching…</div>}
          {!isSearching && hasSearched && results.length === 0 && (
            <div className="search-overlay__empty">No passage was close enough. Try different words or remove a filter.</div>
          )}
          {!isSearching && results.map((r) => {
            const content = (
              <>
                <div className="search-result__snippet">{r.snippet}</div>
                <div className="search-result__source">
                  <IconFile />
                  <span>{r.documentTitle}</span>
                  <span className="search-result__loc">{r.location}</span>
                </div>
                {(r.body || r.disease || r.contentType) && (
                  <div className="src-tags">
                    {r.body && <span className="tag tag--body">{r.body}</span>}
                    {r.disease && <span className="tag">{r.disease}</span>}
                    {r.contentType && <span className="tag">{contentTypeLabel(r.contentType)}</span>}
                  </div>
                )}
              </>
            );
            return (
              <button className="search-result" key={r.id} onClick={() => setPreviewResult(r)} type="button">
                {content}
              </button>
            );
          })}
        </div>
      </div>

      {previewResult && (
        <DocumentPreviewModal
          filename={previewResult.documentTitle}
          highlight={previewResult.snippet}
          onClose={() => setPreviewResult(null)}
        />
      )}
    </div>
  );
}
