import { motion } from 'framer-motion';
import { GlassPanel } from '../components/Glass';
import { SplitDiagram } from '../components/SplitDiagram';

export function Split() {
  return (
    <section className="section" id="decide">
      <div className="wrap routing__layout">
        <motion.div initial={{ opacity: 0, x: -18 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true, amount: 0.3 }} transition={{ duration: 0.85, ease: [0.16, 1, 0.3, 1] }}>
          <GlassPanel className="routing__diagram-panel">
            <SplitDiagram />
          </GlassPanel>
        </motion.div>

        <motion.div initial={{ opacity: 0, x: 18 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true, amount: 0.5 }} transition={{ duration: 0.85, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}>
          <h2 className="section__title" style={{ marginBottom: 14, maxWidth: '16ch' }}>Code makes the decisions. The model only writes.</h2>
          <p className="section__desc">
            The local model is small, so it is weak at complex instructions. Everything that matters
            clinically, which diseases are likely and what to ask next, is decided by code you can
            test. The model's job stays narrow.
          </p>
        </motion.div>
      </div>
    </section>
  );
}
