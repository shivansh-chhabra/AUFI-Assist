import { motion } from 'framer-motion';
import { GlassPanel } from '../components/Glass';
import { NarrowingDemo } from '../components/NarrowingDemo';

export function Narrowing() {
  return (
    <section className="section" id="narrow">
      <div className="wrap">
        <div className="section__head section__head--center">
          <h2 className="section__title">Each answer shifts the odds.</h2>
          <p className="section__desc">
            After every answer the ranking is recalculated, and the next question is the one that
            separates the remaining conditions best.
          </p>
        </div>
        <motion.div initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.3 }} transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}>
          <GlassPanel className="narrow__panel" tick>
            <NarrowingDemo />
          </GlassPanel>
        </motion.div>
      </div>
    </section>
  );
}
