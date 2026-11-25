import type { ReactNode } from 'react';

/** Bold for **text**; nothing else. */
function inline(line: string): ReactNode[] {
  return line.split(/\*\*(.+?)\*\*/g).map((part, i) => (i % 2 ? <strong key={i}>{part}</strong> : part));
}

/**
 * Renders the small amount of formatting the backend uses in summaries:
 * "**bold**" and lines starting with "- " as bullets. Anything else is plain paragraphs.
 */
export default function RichText({ text }: { text: string }) {
  const blocks: ReactNode[] = [];
  let items: string[] = [];

  const flush = () => {
    if (!items.length) return;
    const list = items;
    items = [];
    blocks.push(
      <ul className="rich-list" key={`l${blocks.length}`}>
        {list.map((it, i) => (
          <li key={i}>{inline(it)}</li>
        ))}
      </ul>
    );
  };

  for (const raw of text.split('\n')) {
    const line = raw.trim();
    if (!line) {
      flush();
    } else if (line.startsWith('- ')) {
      items.push(line.slice(2));
    } else {
      flush();
      blocks.push(
        <p className="rich-p" key={`p${blocks.length}`}>
          {inline(line)}
        </p>
      );
    }
  }
  flush();
  return <div className="rich">{blocks}</div>;
}
