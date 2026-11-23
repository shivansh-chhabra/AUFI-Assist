import { useCallback, useRef, useState } from 'react';
import type { Conversation } from '../types';
import { IconSearch, IconX } from './Icons';
import { CONDITIONS } from '../conditions';
import { BRAND_NAME, MODEL_LABEL } from '../brand';

const MIN_WIDTH = 220;
const MAX_WIDTH = 420;

interface SidebarProps {
  workspace: string;
  conversations: Conversation[];
  activeConversationId: string;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
  documentCount: number;
  lastIndexed: string;
  width: number;
  onWidthChange: (width: number) => void;
  onGoHome?: () => void;
  onOpenSearch?: () => void;
}

export default function Sidebar({
  workspace,
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  documentCount,
  lastIndexed,
  width,
  onWidthChange,
  onGoHome,
  onOpenSearch,
}: SidebarProps) {
  const [isDragging, setIsDragging] = useState(false);
  const startRef = useRef({ x: 0, width });

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    e.preventDefault();
    startRef.current = { x: e.clientX, width };
    setIsDragging(true);

    const onMove = (ev: PointerEvent) => {
      const delta = ev.clientX - startRef.current.x;
      const next = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, startRef.current.width + delta));
      onWidthChange(next);
    };
    const onUp = () => {
      setIsDragging(false);
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
    };
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
  }, [width, onWidthChange]);

  return (
    <div className="sidebar">
      <div className="sidebar-brand">
        <button className="wordmark" onClick={onGoHome} aria-label={`Back to ${BRAND_NAME} home`}>
          <span className="mark" />
          {BRAND_NAME}
        </button>
        <div className="crumb">
          Setting <b>{workspace}</b>
        </div>
      </div>

      <button className="search-trigger search-trigger--sidebar" onClick={onOpenSearch} aria-label="Search the guidelines">
        <IconSearch />
        <span>Search guidelines</span>
        <span className="search-trigger__kbd">⌘K</span>
      </button>

      <button className="new-chat-btn" onClick={onNewConversation}>
        <span className="plus">+</span> New case
      </button>

      <div className="side-section">
        <div className="side-heading">Cases</div>
        {conversations.length === 0 && <div className="side-empty">No cases yet.</div>}
        {conversations.map((c) => (
          <div
            key={c.id}
            className={`conv-item${c.id === activeConversationId ? ' active' : ''}`}
            onClick={() => onSelectConversation(c.id)}
          >
            <span className="conv-item__title">{c.title}</span>
            <button
              className="conv-item__delete"
              aria-label={`Delete case "${c.title}"`}
              onClick={(e) => {
                e.stopPropagation();
                onDeleteConversation(c.id);
              }}
            >
              <IconX />
            </button>
          </div>
        ))}
      </div>

      <div className="side-section">
        <div className="side-heading">Guideline corpus</div>
        <div className="kb-stat">
          <span className="kb-num">{documentCount}</span>
          <span className="kb-lbl">guideline documents indexed</span>
        </div>
        <div className="kb-meta">
          From <b>ICMR</b> and <b>MoHFW</b>
          <br />
          Last indexed <b>{lastIndexed}</b>
        </div>
      </div>

      <div className="side-section">
        <details className="cond-list">
          <summary className="side-heading side-heading--toggle">
            <span>Conditions covered</span>
            <span className="count">{CONDITIONS.length}</span>
          </summary>
          <ul>
            {CONDITIONS.map((c) => (
              <li key={c.id}>{c.name}</li>
            ))}
          </ul>
        </details>
      </div>

      <div className="sidebar-footer">
        <div className="exec-mini">
          <span>Model</span>
          <b>{MODEL_LABEL}</b>
        </div>
        <div className="exec-mini">
          <span>Internet</span>
          <span>Disabled</span>
        </div>
      </div>

      <div
        className={`sidebar-resize-handle${isDragging ? ' active' : ''}`}
        onPointerDown={onPointerDown}
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize sidebar"
      />
    </div>
  );
}
