import { motion } from 'framer-motion';

const lineUp = {
  hidden: { y: '110%' },
  show: (i: number) => ({
    y: '0%',
    transition: { duration: 0.9, delay: 0.14 + i * 0.11, ease: [0.16, 1, 0.3, 1] },
  }),
};

const fadeUp = {
  hidden: { opacity: 0, y: 14 },
  show: (delay: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.75, delay, ease: [0.16, 1, 0.3, 1] },
  }),
};

export function Hero({ onLaunch }: { onLaunch: () => void; theme: 'dark' | 'light' }) {
  return (
    <section className="hero hero--immersive">
      <motion.div
        className="hero__arc-bg"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1.3, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
        aria-hidden="true"
      >
        <svg viewBox="0 0 1440 900" width="100%" height="100%" preserveAspectRatio="xMidYMax slice">
          <ellipse cx="720" cy="760" rx="980" ry="520" fill="var(--horizon-fill)" />
          <ellipse cx="720" cy="760" rx="980" ry="520" fill="none" stroke="var(--horizon-line)" strokeWidth={1.4} />
        </svg>
      </motion.div>

      <div className="hero__content">
        <h1 className="hero__title" style={{ fontSize: 'clamp(2.6rem, 4.8vw, 4.9rem)' }}>
          <span className="hero__title-line">
            <motion.span style={{ display: 'inline-block' }} custom={0} variants={lineUp} initial="hidden" animate="show">
              Narrow down a fever
            </motion.span>
          </span>
          <span className="hero__title-line">
            <motion.span className="hero__title-accent" style={{ display: 'inline-block' }} custom={1} variants={lineUp} initial="hidden" animate="show">
              one question at a time.
            </motion.span>
          </span>
        </h1>

        <motion.p className="hero__tagline" custom={0.5} variants={fadeUp} initial="hidden" animate="show">
          Describe the symptoms. The assistant asks what a clinician would ask, ranks the likely
          diseases, then explains them from ICMR and MoHFW guidelines, with citations.
        </motion.p>

        <motion.div className="hero__actions" custom={0.74} variants={fadeUp} initial="hidden" animate="show">
          <button className="btn btn--brass" onClick={onLaunch}>Start a case</button>
          <span className="hero__note">Decision support for clinicians. Not a diagnosis.</span>
        </motion.div>
      </div>
    </section>
  );
}
