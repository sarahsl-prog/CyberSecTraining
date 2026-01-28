/**
 * ErrorMessage component.
 *
 * Displays error messages with optional retry functionality.
 */

import type { HTMLAttributes, ReactNode } from 'react';
import clsx from 'clsx';
import { Button } from './Button';
import styles from './ErrorMessage.module.css';

/**
 * ErrorMessage component props.
 */
export interface ErrorMessageProps extends HTMLAttributes<HTMLDivElement> {
  /** Error title */
  title?: string;
  /** Error message/description */
  message: string;
  /** Retry callback */
  onRetry?: () => void;
  /** Retry button text */
  retryText?: string;
  /** Visual variant */
  variant?: 'inline' | 'banner' | 'page';
  /** Custom icon */
  icon?: ReactNode;
  /** Compact display mode */
  compact?: boolean;
}

/**
 * Error message display component.
 *
 * @example
 * ```tsx
 * <ErrorMessage
 *   title="Failed to load devices"
 *   message="Network error. Please try again."
 *   onRetry={() => refetch()}
 * />
 * ```
 */
export function ErrorMessage({
  title = 'Error',
  message,
  onRetry,
  retryText = 'Try again',
  variant = 'inline',
  icon,
  compact,
  className,
  ...props
}: ErrorMessageProps) {
  const defaultIcon = (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  );

  return (
    <div
      role="alert"
      className={clsx(
        styles.container,
        styles[`variant-${variant}`],
        compact && styles.compact,
        className
      )}
      {...props}
    >
      <div className={styles.iconWrapper} aria-hidden="true">
        {icon || defaultIcon}
      </div>
      <div className={styles.content}>
        <h4 className={styles.title}>{title}</h4>
        <p className={styles.message}>{message}</p>
      </div>
      {onRetry && (
        <div className={styles.action}>
          <Button
            variant={variant === 'banner' ? 'outline' : 'secondary'}
            size="sm"
            onClick={onRetry}
          >
            {retryText}
          </Button>
        </div>
      )}
    </div>
  );
}
