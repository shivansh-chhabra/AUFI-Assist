import { motion } from 'framer-motion';
import { GlassPanel } from '../components/Glass';
import { DotField } from '../components/DotField';

export function Airgap() {
  return (
    <section className="airgap" id="proof">
      <div className="wrap airgap__grid">
        <motion.div initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.5 }} transition={{ duration: 0.75 }}>
          <h2 className="section__title" style={{ maxWidth: '13ch', marginBottom: 14 }}>
            Nothing leaves this machine.
          </h2>
          <p className="section__desc" style={{ maxWidth: '48ch' }}>
            The language model, embeddings, reranker and vector store all run on your own hardware,
            with no cloud API anywhere in the path. That matters for anything touching health information.
          </p>
          <p className="section__desc" style={{ maxWidth: '48ch', marginTop: 14 }}>
            The interface bundles its own fonts and scripts too, so even loading the page makes
            no outside request.
          </p>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.4 }} transition={{ duration: 0.75, delay: 0.12 }}>
          <GlassPanel size="sm" className="airgap__stats">
            <div className="stat stat--lg">
              <div className="stat__value">0</div>
              <div className="stat__label">cloud APIs called while answering</div>
            </div>
            <div className="stat stat--lg">
              <div className="stat__value">100%</div>
              <div className="stat__label">of scoring, retrieval and generation run locally</div>
            </div>
            <div className="stat stat--lg">
              <div className="stat__value">3B</div>
              <div className="stat__label">parameters in llama3.2:3b, small enough for ordinary hardware</div>
            </div>
          </GlassPanel>
        </motion.div>
      </div>
    </section>
  );
}

const OUTPUT = [
  { kind: 'Features', name: 'What the disease typically looks like', meta: 'cited' },
  { kind: 'Tests', name: 'Which tests confirm it, and when in the illness they work', meta: 'cited' },
  { kind: 'Treatment', name: 'What the guideline recommends, and which signs need escalation', meta: 'cited' },
  { kind: 'No match', name: 'If nothing retrieved is close enough, it says so instead of answering from memory', meta: 'no guess' },
];

export function Deliverables() {
  return (
    <section className="section section--tight" id="deliverables">
      <div className="wrap">
        <div className="section__head section__head--center">
          <h2 className="section__title" style={{ maxWidth: '20ch' }}>Every explanation says where it came from.</h2>
          <p className="section__desc">
            For each shortlisted disease the answer covers three things. Each statement carries a
            citation you can open to the guideline passage.
          </p>
        </div>
        <div className="deliverables__list">
          {OUTPUT.map((f, i) => (
            <motion.div
              className="file-row"
              key={f.kind}
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.5 }}
              transition={{ duration: 0.65, delay: i * 0.08 }}
            >
              <span className="file-row__ext file-row__ext--wide">{f.kind}</span>
              <span className="file-row__name">{f.name}</span>
              <span className="file-row__meta">{f.meta}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

const SPECS = [
  { value: '11', label: 'conditions in the AUFI cluster, from malaria and dengue to TB and rheumatic fever.' },
  { value: '2', label: 'guideline bodies, ICMR and MoHFW, make up the citable corpus.' },
  { value: '1', label: 'question at a time, each chosen to rule out as many conditions as possible.' },
  { value: '0', label: 'medical claims made from the model\u2019s own memory.' },
];

export function Specs() {
  return (
    <section className="specs">
      <div className="wrap specs__grid">
        {SPECS.map((s, i) => (
          <motion.div key={s.label} initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true, amount: 0.6 }} transition={{ duration: 0.65, delay: i * 0.08 }}>
            <div className="spec-item__value">{s.value}</div>
            <div className="spec-item__label">{s.label}</div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

export function FinalCTA({ onLaunch }: { onLaunch: () => void }) {
  return (
    <section className="cta-final">
      <DotField count={36} />
      <div className="wrap">
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.5 }} transition={{ duration: 0.75 }}>
          <GlassPanel className="cta-final__panel" tick>
            <h2 className="cta-final__title">Start with what the patient says.</h2>
            <div className="cta-final__actions">
              <button className="btn btn--brass" onClick={onLaunch}>Start a case</button>
              <span className="cta-final__note">Runs entirely on this machine.</span>
            </div>
          </GlassPanel>
        </motion.div>
      </div>
    </section>
  );
}
