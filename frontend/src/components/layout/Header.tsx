import React from 'react';
import { useAccessibility, ColorMode } from '@/context/AccessibilityContext';
import styles from './Header.module.css';

const colorModeLabels: Record<ColorMode, string> = {
  light: 'Light',
  dark: 'Dark',
  'high-contrast': 'High Contrast',
  protanopia: 'Protanopia',
  deuteranopia: 'Deuteranopia',
  tritanopia: 'Tritanopia',
};

export function Header() {
  const { state, setColorMode } = useAccessibility();

  const handleColorModeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setColorMode(e.target.value as ColorMode);
  };

  return (
    <header className={styles.header} role="banner">
      <div className={styles.logo}>
        <span className={styles.logoIcon} aria-hidden="true">🛡️</span>
        <span className={styles.logoText}>CyberSec Teaching Tool</span>
      </div>

      <div className={styles.actions}>
        {/* Quick accessibility toggle */}
        <div className={styles.accessibilityToggle}>
          <label htmlFor="color-mode-select" className="sr-only">
            Color mode
          </label>
          <select
            id="color-mode-select"
            value={state.colorMode}
            onChange={handleColorModeChange}
            className={styles.select}
            aria-label="Select color mode"
          >
            {Object.entries(colorModeLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </header>
  );
}

export default Header;
