import { motion } from 'framer-motion';
import ThemeToggle from '../../../components/ThemeToggle';
import { BRAND_NAME } from '../../../brand';

interface NavBarProps {
  onLaunch: () => void;
  theme: 'dark' | 'light';
  toggleTheme: () => void;
}

export function NavBar({ onLaunch, theme, toggleTheme }: NavBarProps) {
  return (
    <motion.div className="landing-nav" initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.6, delay: 0.05 }}>
      <div className="landing-nav__inner">
        <button className="landing-nav__mark" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} aria-label="Back to top">
          <span className="landing-nav__mark-glyph" />
          {BRAND_NAME} <span>Acute undifferentiated fever</span>
        </button>
        <nav className="landing-nav__links">
          <a href="#narrow">How it narrows</a>
          <a href="#decide">Code and model</a>
          <a href="#agent">The loop</a>
          <a href="#sources">Data sources</a>
          <a href="#proof">Privacy</a>
        </nav>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <ThemeToggle theme={theme} onToggle={toggleTheme} />
          <button className="btn btn--ghost btn--sm" onClick={onLaunch}>Start a case</button>
        </div>
      </div>
    </motion.div>
  );
}

export function Footer() {
  return (
    <footer className="landing-footer">
      <div className="wrap landing-footer__inner">
        <div className="landing-footer__mark">{BRAND_NAME}</div>
        <div className="landing-footer__meta">
          <span>Minor project</span>
          <span>Agentic clinical decision support for AUFI</span>
          <span>Decision support only, not a diagnosis</span>
        </div>
      </div>
    </footer>
  );
}
