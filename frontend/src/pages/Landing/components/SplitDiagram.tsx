const CODE = [
  { t: 'Which diseases are likely', d: 'Bayesian update: each answer shifts every disease according to the table.' },
  { t: 'What to ask next', d: 'The question with the largest expected drop in uncertainty (entropy).' },
  { t: 'When to stop', d: 'One or two left, the question limit, or no question separates them.' },
  { t: 'Where to search', d: 'Retrieval is narrowed to the shortlisted disease and content type.' },
];
const MODEL = [
  { t: 'Phrase the question', d: 'Turns the chosen symptom into a plain-language question.' },
  { t: 'Write the explanation', d: 'Only from the retrieved guideline passages, with a citation on each claim.' },
];

/** Who decides what: deterministic code on the left, the small language model on the right. */
export function SplitDiagram() {
  return (
    <div className="split">
      <div className="split__col">
        <div className="split__head">
          <span className="split__title">Code decides</span>
          <span className="split__sub">Deterministic Python</span>
        </div>
        <ul>
          {CODE.map((i) => (
            <li key={i.t}><b>{i.t}</b><span>{i.d}</span></li>
          ))}
        </ul>
      </div>
      <div className="split__col split__col--model">
        <div className="split__head">
          <span className="split__title">The model writes</span>
          <span className="split__sub">llama3.2:3b, local</span>
        </div>
        <ul>
          {MODEL.map((i) => (
            <li key={i.t}><b>{i.t}</b><span>{i.d}</span></li>
          ))}
        </ul>
      </div>
    </div>
  );
}
