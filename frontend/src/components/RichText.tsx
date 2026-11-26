import type { ReactNode } from 'react';

/** Bold for **text**, and [n] markers as small clickable numbers when onCite is given. */
function inline(line: string, onCite?: (n: number) => void): ReactNode[] {
  return line.split(/(\*\*.+?\*\*|\[\d+\])/g).map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) return <strong key={i}>{part.slice(2, -2)}</strong>;
    const m = /^\[(\d+)\]$/.exec(part);
    if (m && onCite) {
      return (
        <button key={i} className="cite" type="button" onClick={() => onCite(Number(m[1]))} aria-label={`Open source ${m[1]}`}>
          {m[1]}
        </button>
      );
    }
    return part;
  });
}

/**
 * Renders the small amount of formatting the backend uses in summaries:
 * "**bold**" and lines starting with "- " as bullets. Anything else is plain paragraphs.
 */
export default function RichText({ text, onCite }: { text: string; onCite?: (n: number) => void }) {
  const blocks: ReactNode[] = [];
  let items: string[] = [];

  const flush = () => {
    if (!items.length) return;
    const list = items;
    items = [];
    blocks.push(
      <ul className="rich-list" key={`l${blocks.length}`}>
        {list.map((it, i) => (
          <li key={i}>{inline(it, onCite)}</li>
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
          {inline(line, onCite)}
        </p>
      );
    }
  }
  flush();
  return <div className="rich">{blocks}</div>;
}
