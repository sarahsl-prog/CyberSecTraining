/**
 * Settings page component.
 *
 * Provides configuration options for:
 * - Accessibility settings (color mode, font size, motion)
 * - Scan preferences
 * - LLM preferences
 * - Privacy controls
 */

import { useState } from 'react';
import { useAccessibility } from '@/context/AccessibilityContext';
import { useMode } from '@/context/ModeContext';
import { Card, Button, Modal } from '@/components/common';
import { logger } from '@/services';
import styles from './Settings.module.css';

const log = logger.create('Settings');

/**
 * Color mode options.
 */
const COLOR_MODES = [
  { value: 'light', label: 'Light', description: 'Default light theme' },
  { value: 'dark', label: 'Dark', description: 'Dark theme for low-light environments' },
  { value: 'high-contrast', label: 'High Contrast', description: 'Enhanced contrast for better visibility' },
  { value: 'protanopia', label: 'Protanopia', description: 'Red-blind safe colors' },
  { value: 'deuteranopia', label: 'Deuteranopia', description: 'Green-blind safe colors' },
  { value: 'tritanopia', label: 'Tritanopia', description: 'Blue-yellow safe colors' },
] as const;

/**
 * Font size presets.
 */
const FONT_SIZES = [
  { value: 100, label: 'Normal', description: '100%' },
  { value: 125, label: 'Large', description: '125%' },
  { value: 150, label: 'Extra Large', description: '150%' },
  { value: 200, label: 'Maximum', description: '200%' },
] as const;

/**
 * Settings page.
 */
export function Settings() {
  const {
    state,
    setColorMode,
    setFontSize,
    setReduceMotion,
    setScreenReaderOptimized,
    setShowFocusIndicator,
    resetToDefaults,
  } = useAccessibility();

  const { mode, setMode, isLoading: isModeLoading } = useMode();

  const { colorMode, fontSize, reduceMotion, showFocusIndicator, screenReaderOptimized } = state;

  // State for confirmation modal
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [pendingMode, setPendingMode] = useState<'training' | 'live' | null>(null);

  log.debug('Settings page rendering', { colorMode, fontSize, reduceMotion, mode });

  /**
   * Handle color mode change.
   */
  const handleColorModeChange = (mode: typeof colorMode) => {
    log.info('Changing color mode', { from: colorMode, to: mode });
    setColorMode(mode);
  };

  /**
   * Handle font size change.
   */
  const handleFontSizeChange = (size: number) => {
    log.info('Changing font size', { from: fontSize, to: size });
    setFontSize(size);
  };

  /**
   * Reset all settings to defaults.
   */
  const handleResetSettings = () => {
    log.info('Resetting all settings to defaults');
    resetToDefaults();
  };

  /**
   * Handle mode change request.
   * Shows confirmation dialog for live mode.
   */
  const handleModeChange = (newMode: 'training' | 'live') => {
    if (newMode === mode) return;

    log.info('Mode change requested', { from: mode, to: newMode });

    // If switching to live mode, show confirmation dialog
    if (newMode === 'live') {
      setPendingMode(newMode);
      setShowConfirmModal(true);
    } else {
      // Switching to training mode - no confirmation needed
      setMode(newMode);
    }
  };

  /**
   * Confirm mode change to live mode.
   */
  const handleConfirmModeChange = async () => {
    if (pendingMode) {
      log.info('Confirming mode change to live');
      await setMode(pendingMode);
      setPendingMode(null);
      setShowConfirmModal(false);
    }
  };

  /**
   * Cancel mode change.
   */
  const handleCancelModeChange = () => {
    log.info('Canceling mode change');
    setPendingMode(null);
    setShowConfirmModal(false);
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Settings</h1>
        <p className={styles.subtitle}>
          Customize your experience and accessibility preferences
        </p>
      </header>

      <div className={styles.content}>
        {/* Accessibility Settings */}
        <Card title="Accessibility" subtitle="WCAG 2.1 AA compliant options">
          <div className={styles.settingsGroup}>
            {/* Color Mode */}
            <div className={styles.setting}>
              <div className={styles.settingHeader}>
                <h3 className={styles.settingTitle}>Color Mode</h3>
                <p className={styles.settingDescription}>
                  Choose a color theme that works best for you
                </p>
              </div>
              <div className={styles.colorModeGrid}>
                {COLOR_MODES.map((mode) => (
                  <label
                    key={mode.value}
                    className={`${styles.colorModeOption} ${
                      colorMode === mode.value ? styles.selected : ''
                    }`}
                  >
                    <input
                      type="radio"
                      name="colorMode"
                      value={mode.value}
                      checked={colorMode === mode.value}
                      onChange={() => handleColorModeChange(mode.value)}
                      className={styles.radioInput}
                    />
                    <span className={styles.colorModeLabel}>{mode.label}</span>
                    <span className={styles.colorModeDescription}>
                      {mode.description}
                    </span>
                    <span
                      className={`${styles.colorModePreview} ${styles[`preview-${mode.value}`]}`}
                      aria-hidden="true"
                    />
                  </label>
                ))}
              </div>
            </div>

            {/* Font Size */}
            <div className={styles.setting}>
              <div className={styles.settingHeader}>
                <h3 className={styles.settingTitle}>Text Size</h3>
                <p className={styles.settingDescription}>
                  Adjust the base font size for better readability
                </p>
              </div>
              <div className={styles.fontSizeOptions}>
                {FONT_SIZES.map((size) => (
                  <button
                    key={size.value}
                    type="button"
                    className={`${styles.fontSizeOption} ${
                      fontSize === size.value ? styles.selected : ''
                    }`}
                    onClick={() => handleFontSizeChange(size.value)}
                    aria-pressed={fontSize === size.value}
                  >
                    <span className={styles.fontSizeLabel}>{size.label}</span>
                    <span className={styles.fontSizeValue}>{size.description}</span>
                  </button>
                ))}
              </div>
              <div className={styles.fontSizeSlider}>
                <label htmlFor="fontSize" className="sr-only">
                  Font size: {fontSize}%
                </label>
                <input
                  id="fontSize"
                  type="range"
                  min="100"
                  max="200"
                  step="5"
                  value={fontSize}
                  onChange={(e) => handleFontSizeChange(Number(e.target.value))}
                  className={styles.slider}
                  aria-valuenow={fontSize}
                  aria-valuemin={100}
                  aria-valuemax={200}
                  aria-label={`Font size: ${fontSize}%`}
                />
                <span className={styles.sliderValue}>{fontSize}%</span>
              </div>
            </div>

            {/* Motion */}
            <div className={styles.setting}>
              <label className={styles.toggleSetting}>
                <div className={styles.settingHeader}>
                  <h3 className={styles.settingTitle}>Reduce Motion</h3>
                  <p className={styles.settingDescription}>
                    Minimize animations and transitions
                  </p>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={reduceMotion}
                  className={`${styles.toggle} ${reduceMotion ? styles.toggleOn : ''}`}
                  onClick={() => setReduceMotion(!reduceMotion)}
                >
                  <span className={styles.toggleThumb} />
                </button>
              </label>
            </div>

            {/* Focus Indicators */}
            <div className={styles.setting}>
              <label className={styles.toggleSetting}>
                <div className={styles.settingHeader}>
                  <h3 className={styles.settingTitle}>Enhanced Focus Indicators</h3>
                  <p className={styles.settingDescription}>
                    Show prominent focus outlines for keyboard navigation
                  </p>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={showFocusIndicator}
                  className={`${styles.toggle} ${showFocusIndicator ? styles.toggleOn : ''}`}
                  onClick={() => setShowFocusIndicator(!showFocusIndicator)}
                >
                  <span className={styles.toggleThumb} />
                </button>
              </label>
            </div>

            {/* Screen Reader Optimization */}
            <div className={styles.setting}>
              <label className={styles.toggleSetting}>
                <div className={styles.settingHeader}>
                  <h3 className={styles.settingTitle}>Screen Reader Optimized</h3>
                  <p className={styles.settingDescription}>
                    Optimize content structure for screen readers
                  </p>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={screenReaderOptimized}
                  className={`${styles.toggle} ${screenReaderOptimized ? styles.toggleOn : ''}`}
                  onClick={() => setScreenReaderOptimized(!screenReaderOptimized)}
                >
                  <span className={styles.toggleThumb} />
                </button>
              </label>
            </div>
          </div>
        </Card>

        {/* Application Mode */}
        <Card title="Application Mode" subtitle="Choose between training and live scanning">
          <div className={styles.settingsGroup}>
            <div className={styles.setting}>
              <div className={styles.modeOptions}>
                {/* Training Mode Option */}
                <label
                  className={`${styles.modeOption} ${
                    mode === 'training' ? styles.selected : ''
                  }`}
                >
                  <input
                    type="radio"
                    name="applicationMode"
                    value="training"
                    checked={mode === 'training'}
                    onChange={() => handleModeChange('training')}
                    disabled={isModeLoading}
                    className={styles.radioInput}
                  />
                  <div className={styles.modeContent}>
                    <div className={styles.modeHeader}>
                      <span className={styles.modeIcon} aria-hidden="true">
                        🎓
                      </span>
                      <h3 className={styles.modeTitle}>Training Mode</h3>
                    </div>
                    <p className={styles.modeDescription}>
                      Safe practice environment with realistic simulated network data.
                      Perfect for learning and experimentation without affecting real networks.
                    </p>
                    <ul className={styles.modeFeatures}>
                      <li>✓ No real network scanning</li>
                      <li>✓ Deterministic, predictable results</li>
                      <li>✓ Safe for beginners</li>
                    </ul>
                  </div>
                </label>

                {/* Live Mode Option */}
                <label
                  className={`${styles.modeOption} ${
                    mode === 'live' ? styles.selected : ''
                  }`}
                >
                  <input
                    type="radio"
                    name="applicationMode"
                    value="live"
                    checked={mode === 'live'}
                    onChange={() => handleModeChange('live')}
                    disabled={isModeLoading}
                    className={styles.radioInput}
                  />
                  <div className={styles.modeContent}>
                    <div className={styles.modeHeader}>
                      <span className={styles.modeIcon} aria-hidden="true">
                        ⚡
                      </span>
                      <h3 className={styles.modeTitle}>Live Mode</h3>
                    </div>
                    <p className={styles.modeDescription}>
                      Real network scanning using nmap. Only use on networks you own
                      or have explicit permission to scan.
                    </p>
                    <ul className={styles.modeFeatures}>
                      <li>⚠️ Scans actual networks</li>
                      <li>⚠️ Requires nmap installation</li>
                      <li>⚠️ Use with permission only</li>
                    </ul>
                  </div>
                </label>
              </div>
            </div>
          </div>
        </Card>

        {/* Scan Preferences */}
        <Card title="Scan Preferences" subtitle="Default settings for network scans">
          <div className={styles.settingsGroup}>
            <div className={styles.setting}>
              <div className={styles.settingHeader}>
                <h3 className={styles.settingTitle}>Default Scan Type</h3>
                <p className={styles.settingDescription}>
                  Pre-selected scan type for new scans
                </p>
              </div>
              <select className={styles.select} defaultValue="quick">
                <option value="quick">Quick Scan</option>
                <option value="deep">Deep Scan</option>
                <option value="vulnerability">Vulnerability Scan</option>
              </select>
            </div>

            <div className={styles.setting}>
              <label className={styles.toggleSetting}>
                <div className={styles.settingHeader}>
                  <h3 className={styles.settingTitle}>Auto-detect Network</h3>
                  <p className={styles.settingDescription}>
                    Automatically detect and populate local network
                  </p>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={true}
                  className={`${styles.toggle} ${styles.toggleOn}`}
                  onClick={() => {}}
                >
                  <span className={styles.toggleThumb} />
                </button>
              </label>
            </div>
          </div>
        </Card>

        {/* LLM Preferences */}
        <Card title="AI Assistant" subtitle="Configure AI-powered explanations">
          <div className={styles.settingsGroup}>
            <div className={styles.setting}>
              <div className={styles.settingHeader}>
                <h3 className={styles.settingTitle}>Explanation Detail Level</h3>
                <p className={styles.settingDescription}>
                  How detailed should AI explanations be
                </p>
              </div>
              <select className={styles.select} defaultValue="standard">
                <option value="brief">Brief</option>
                <option value="standard">Standard</option>
                <option value="detailed">Detailed</option>
              </select>
            </div>

            <div className={styles.setting}>
              <label className={styles.toggleSetting}>
                <div className={styles.settingHeader}>
                  <h3 className={styles.settingTitle}>Use Local AI (Ollama)</h3>
                  <p className={styles.settingDescription}>
                    Prefer local AI when available for privacy
                  </p>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={true}
                  className={`${styles.toggle} ${styles.toggleOn}`}
                  onClick={() => {}}
                >
                  <span className={styles.toggleThumb} />
                </button>
              </label>
            </div>
          </div>
        </Card>

        {/* Privacy */}
        <Card title="Privacy" subtitle="Control your data and privacy">
          <div className={styles.settingsGroup}>
            <div className={styles.setting}>
              <label className={styles.toggleSetting}>
                <div className={styles.settingHeader}>
                  <h3 className={styles.settingTitle}>Store Scan History</h3>
                  <p className={styles.settingDescription}>
                    Keep a record of previous scans locally
                  </p>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={true}
                  className={`${styles.toggle} ${styles.toggleOn}`}
                  onClick={() => {}}
                >
                  <span className={styles.toggleThumb} />
                </button>
              </label>
            </div>

            <div className={styles.setting}>
              <div className={styles.settingHeader}>
                <h3 className={styles.settingTitle}>Clear Data</h3>
                <p className={styles.settingDescription}>
                  Delete all stored scan data and preferences
                </p>
              </div>
              <Button variant="destructive" size="sm">
                Clear All Data
              </Button>
            </div>
          </div>
        </Card>

        {/* Reset */}
        <div className={styles.resetSection}>
          <Button variant="outline" onClick={handleResetSettings}>
            Reset All Settings to Defaults
          </Button>
        </div>
      </div>

      {/* Live Mode Confirmation Modal */}
      <Modal
        isOpen={showConfirmModal}
        onClose={handleCancelModeChange}
        title="Switch to Live Scanning Mode?"
      >
        <div className={styles.confirmModal}>
          <p className={styles.confirmWarning}>
            <strong>⚠️ Warning:</strong> You are about to switch to Live Mode,
            which will perform real network scans on your actual network.
          </p>
          <p className={styles.confirmDescription}>
            Live Mode uses nmap to scan real networks. Only proceed if:
          </p>
          <ul className={styles.confirmList}>
            <li>You own the network you intend to scan</li>
            <li>You have explicit permission to scan the network</li>
            <li>You have nmap installed and properly configured</li>
            <li>You understand the legal implications of network scanning</li>
          </ul>
          <p className={styles.confirmNote}>
            Unauthorized network scanning may be illegal in your jurisdiction.
          </p>
          <div className={styles.confirmActions}>
            <Button variant="outline" onClick={handleCancelModeChange}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleConfirmModeChange}>
              I Understand - Enable Live Mode
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
