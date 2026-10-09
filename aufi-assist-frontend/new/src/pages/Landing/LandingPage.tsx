import { NoiseOverlay } from './components/Glass';
import { NavBar, Footer } from './sections/Chrome';
import { Hero } from './sections/Hero';
import { Problem } from './sections/Problem';
import { Narrowing } from './sections/Narrowing';
import { Split } from './sections/Split';
import { AgentLoop } from './sections/AgentLoop';
import { Sources } from './sections/Sources';
import { Airgap, Deliverables, Specs, FinalCTA } from './sections/Proof';
import { useTheme } from '../../hooks/useTheme';
import './landing.css';

export default function LandingPage({ onLaunch }: { onLaunch: () => void }) {
  const { theme, toggleTheme } = useTheme();
  return (
    <div className="landing">
      <div className="landing-glow" aria-hidden="true" />
      <NoiseOverlay />
      <NavBar onLaunch={onLaunch} theme={theme} toggleTheme={toggleTheme} />
      <Hero onLaunch={onLaunch} theme={theme} />
      <Problem />
      <Narrowing />
      <Split />
      <AgentLoop />
      <Sources />
      <Airgap />
      <Deliverables />
      <Specs />
      <FinalCTA onLaunch={onLaunch} />
      <Footer />
    </div>
  );
}
