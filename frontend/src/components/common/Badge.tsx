/**
 * Badge component.
 *
 * A small label component for status indicators, counts, and tags.
 */

import type { HTMLAttributes, ReactNode } from 'react';
import clsx from 'clsx';
import styles from './Badge.module.css';

/**
 * Badge component props.
 */
export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  /** Badge content */
  children: ReactNode;
  /** Visual variant */
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'destructive' | 'info';
  /** Severity-based variant (overrides variant) */
  severity?: 'critical' | 'high' | 'medium' | 'low' | 'info';
  /** Badge size */
  size?: 'sm' | 'md';
}

/**
 * Badge component for status indicators.
 *
 * @example
 * ```tsx
 * <Badge variant="success">Active</Badge>
 * <Badge severity="critical">2 Critical</Badge>
 * ```
 */
export function Badge({
  children,
  variant = 'default',
  severity,
  size = 'md',
  className,
  ...props
}: BadgeProps) {
  // Map severity to variant if provided
  const effectiveVariant = severity
    ? {
        critical: 'destructive',
        high: 'warning',
        medium: 'warning',
        low: 'success',
        info: 'info',
      }[severity]
    : variant;

  return (
    <span
      className={clsx(
        styles.badge,
        styles[`variant-${effectiveVariant}`],
        styles[`size-${size}`],
        severity && styles[`severity-${severity}`],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
