/**
 * Spinner component.
 *
 * An accessible loading spinner with customizable size and label.
 */

import type { HTMLAttributes } from 'react';
import clsx from 'clsx';
import styles from './Spinner.module.css';

/**
 * Spinner component props.
 */
export interface SpinnerProps extends HTMLAttributes<HTMLDivElement> {
  /** Spinner size */
  size?: 'sm' | 'md' | 'lg';
  /** Accessible label for screen readers */
  label?: string;
}

/**
 * Loading spinner component.
 *
 * @example
 * ```tsx
 * <Spinner size="lg" label="Loading devices..." />
 * ```
 */
export function Spinner({
  size = 'md',
  label = 'Loading',
  className,
  ...props
}: SpinnerProps) {
  return (
    <div
      role="status"
      aria-label={label}
      className={clsx(styles.spinner, styles[`size-${size}`], className)}
      {...props}
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <circle
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          className={styles.track}
        />
        <circle
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray="31.416"
          strokeDashoffset="23.562"
          className={styles.indicator}
        />
      </svg>
      <span className="sr-only">{label}</span>
    </div>
  );
}
