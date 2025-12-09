/**
 * Progress component.
 *
 * An accessible progress bar with label and percentage display.
 */

import type { HTMLAttributes } from 'react';
import clsx from 'clsx';
import styles from './Progress.module.css';

/**
 * Progress component props.
 */
export interface ProgressProps extends HTMLAttributes<HTMLDivElement> {
  /** Progress value (0-100) */
  value: number;
  /** Maximum value (default: 100) */
  max?: number;
  /** Show percentage label */
  showLabel?: boolean;
  /** Custom label text */
  label?: string;
  /** Progress bar size */
  size?: 'sm' | 'md' | 'lg';
  /** Color variant */
  variant?: 'default' | 'success' | 'warning' | 'destructive';
}

/**
 * Progress bar component.
 *
 * @example
 * ```tsx
 * <Progress value={75} showLabel />
 * <Progress value={50} label="Scanning network..." />
 * ```
 */
export function Progress({
  value,
  max = 100,
  showLabel = false,
  label,
  size = 'md',
  variant = 'default',
  className,
  ...props
}: ProgressProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  const displayLabel = label || `${Math.round(percentage)}%`;

  return (
    <div
      className={clsx(styles.container, styles[`size-${size}`], className)}
      {...props}
    >
      {(showLabel || label) && (
        <div className={styles.labelContainer}>
          <span className={styles.label}>{label || 'Progress'}</span>
          <span className={styles.percentage}>{Math.round(percentage)}%</span>
        </div>
      )}
      <div
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={displayLabel}
        className={styles.track}
      >
        <div
          className={clsx(styles.indicator, styles[`variant-${variant}`])}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
