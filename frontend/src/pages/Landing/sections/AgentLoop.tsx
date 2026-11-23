import { useState } from 'react';
import { motion } from 'framer-motion';
import { AgentLoopDiagram } from '../components/Diagrams';

const STEPS = [
  { title: 'Intake', desc: 'The user types their symptoms in free text. Nothing is assumed about the cause yet.' },
  { title: 'Score', desc: 'The symptoms are compared with the table of how often each disease shows each feature, giving a ranked list of candidate diseases.' },
  { title: 'Ask', desc: 'Among the symptoms not yet asked about, the one that best separates the remaining candidates becomes the next question.' },
  { title: 'Repeat', desc: 'The answer updates the ranking and the loop goes round again. It stops when one or two candidates remain, the question limit is reached, or no question would tell them apart.' },
  { title: 'Explain', desc: 'For the shortlist, the guideline documents are searched and an explanation is written: typical clinical features, confirmatory tests, and treatment, with citations.' },
];

export function AgentLoop() {
  // `loopStart` drives the diagram's travelling dot and persists once set.
  // `hovered` only controls which step description is expanded, and clears
  // as soon as the cursor leaves the step list entirely.
  const [loopStart, setLoopStart] = useState(0);
  const [hovered, setHovered] = useState<number | null>(null);

  const select = (i: number) => {
    setLoopStart(i);
    setHovered(i);
  };

  return (
    <section className="section" id="agent">
      <div className="wrap agentloop__grid">
        <div>
          <h2 className="section__title" style={{ marginBottom: 14 }}>A loop, not a single search.</h2>
          <p className="section__desc" style={{ marginBottom: 44 }}>
            A vague first description gives vague search results. So the assistant asks first, and
            only searches the guidelines once the picture is clear.
          </p>
          <div className="agentloop__steps" onMouseLeave={() => setHovered(null)}>
            {STEPS.map((s, i) => (
              <motion.div
                className={`loop-step${hovered === i ? ' loop-step--open' : ''}`}
                key={s.title}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.7 }}
                transition={{ duration: 0.65, delay: i * 0.08 }}
                onMouseEnter={() => setHovered(i)}
                onFocus={() => setHovered(i)}
                onBlur={() => setHovered(null)}
                onClick={() => select(i)}
                tabIndex={0}
              >
                <div className="loop-step__row">
                  <span className="loop-step__index">{String(i + 1).padStart(2, '0')}</span>
                  <span className="loop-step__title">{s.title}</span>
                </div>
                <div className="loop-step__desc-wrap">
                  <p className="loop-step__desc">{s.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
        <motion.div initial={{ opacity: 0, scale: 0.94 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true, amount: 0.4 }} transition={{ duration: 0.85, ease: [0.16, 1, 0.3, 1] }}>
          <AgentLoopDiagram activeIndex={loopStart} onSelect={select} />
        </motion.div>
      </div>
    </section>
  );
}
