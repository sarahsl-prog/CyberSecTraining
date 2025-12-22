/**
 * ModeBanner component.
 *
 * Displays the current application mode (Training or Live) prominently
 * at the top of the application. Provides visual feedback about which
 * mode the user is currently in.
 */

import { useMode } from '@/context/ModeContext';
import clsx from 'clsx';
import styles from './ModeBanner.module.css';

/**
 * ModeBanner component props.
 */
export interface ModeBannerProps {
  /** Additional CSS class name */
  className?: string;
}

/**
 * ModeBanner component that displays the current application mode.
 *
 * - Training Mode: Blue/teal background with graduation cap icon
 * - Live Mode: Orange/red background with lightning bolt icon
 *
 * Accessible with ARIA live region and proper role attributes.
 *
 * @example
 * ```tsx
 * <ModeBanner />
 * ```
 */
export function ModeBanner({ className }: ModeBannerProps) {
  const { mode } = useMode();

  const isTrainingMode = mode === 'training';

  // Mode-specific content
  const icon = isTrainingMode ? '🎓' : '⚡';
  const title = isTrainingMode ? 'Training Mode Active' : 'Live Scanning Mode Active';
  const description = isTrainingMode
    ? 'Safe Practice Environment - Using Simulated Data'
    : 'Real Network Scanning - Actual Network Data';

  return (
    <div
      className={clsx(
        styles.banner,
        isTrainingMode ? styles.training : styles.live,
        className
      )}
      role="banner"
      aria-live="polite"
      aria-atomic="true"
    >
      <div className={styles.content}>
        <span className={styles.icon} aria-hidden="true">
          {icon}
        </span>
        <div className={styles.text}>
          <span className={styles.title}>{title}</span>
          <span className={styles.description}>{description}</span>
        </div>
      </div>
    </div>
  );
}
