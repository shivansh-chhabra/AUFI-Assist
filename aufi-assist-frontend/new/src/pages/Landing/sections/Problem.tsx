import { motion } from 'framer-motion';
import { GlassPanel } from '../components/Glass';
import { SymptomOverlap } from '../components/Diagrams';

export function Problem() {
  return (
    <section className="section section--tight" style={{ overflow: 'clip' }}>
      <div className="wrap problem__grid">
        <motion.div className="problem__body" initial={{ opacity: 0, x: -18 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true, amount: 0.5 }} transition={{ duration: 0.85, ease: [0.16, 1, 0.3, 1] }}>
          <h2 className="section__title" style={{ marginBottom: 20, maxWidth: '17ch' }}>
            A fever with no obvious cause looks the same at first.
          </h2>
          <p>
            In India, malaria, dengue, typhoid, scrub typhus, leptospirosis and others all begin with
            fever, headache and body ache. The first description is vague, and a document search on
            vague input returns vague results.
          </p>
          <p>
            A clinician asks targeted questions until the picture clears. This assistant does the same,
            and only searches the guidelines once it knows what to look for.
          </p>
        </motion.div>

        <motion.div initial={{ opacity: 0, x: 18 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true, amount: 0.4 }} transition={{ duration: 0.85, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}>
          <GlassPanel className="problem__panel">
            <SymptomOverlap />
          </GlassPanel>
        </motion.div>
      </div>
    </section>
  );
}
