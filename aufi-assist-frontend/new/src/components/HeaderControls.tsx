import ThemeToggle from './ThemeToggle';
import { USE_MOCK_DATA } from '../config';

interface HeaderControlsProps {
  userInitials: string;
  theme: 'dark' | 'light';
  toggleTheme: () => void;
}

/** Floating theme + account controls pinned to the corner of the main pane. */
export default function HeaderControls({ userInitials, theme, toggleTheme }: HeaderControlsProps) {
  return (
    <div className="header-controls">
      {USE_MOCK_DATA && (
        <span className="demo-chip" title="The backend is not connected. Everything shown is scripted demo data.">
          Demo data
        </span>
      )}
      <ThemeToggle theme={theme} onToggle={toggleTheme} />
      <div className="avatar" aria-label="Signed in as clinician">{userInitials}</div>
    </div>
  );
}
