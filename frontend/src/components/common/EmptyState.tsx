/**
 * EmptyState component.
 *
 * A placeholder component for empty lists and states.
 */

import type { HTMLAttributes, ReactNode } from 'react';
import clsx from 'clsx';
import styles from './EmptyState.module.css';

/**
 * EmptyState component props.
 */
export interface EmptyStateProps extends HTMLAttributes<HTMLDivElement> {
  /** Main title/heading */
  title: string;
  /** Description text */
  description?: string;
  /** Icon to display */
  icon?: ReactNode;
  /** Action button/link */
  action?: ReactNode;
}

/**
 * Empty state placeholder component.
 *
 * @example
 * ```tsx
 * <EmptyState
 *   icon={<SearchIcon />}
 *   title="No devices found"
 *   description="Start a network scan to discover devices."
 *   action={<Button onClick={handleScan}>Start Scan</Button>}
 * />
 * ```
 */
export function EmptyState({
  title,
  description,
  icon,
  action,
  className,
  ...props
}: EmptyStateProps) {
  return (
    <div className={clsx(styles.container, className)} {...props}>
      {icon && <div className={styles.icon} aria-hidden="true">{icon}</div>}
      <h3 className={styles.title}>{title}</h3>
      {description && <p className={styles.description}>{description}</p>}
      {action && <div className={styles.action}>{action}</div>}
    </div>
  );
}
