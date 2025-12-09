/**
 * Card component.
 *
 * A container component for grouping related content with
 * consistent styling and accessibility features.
 */

import { forwardRef } from 'react';
import type { HTMLAttributes, ReactNode } from 'react';
import clsx from 'clsx';
import styles from './Card.module.css';

/**
 * Card component props.
 */
export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Card content */
  children: ReactNode;
  /** Optional card title */
  title?: string;
  /** Optional card subtitle/description */
  subtitle?: string;
  /** Visual variant */
  variant?: 'default' | 'outlined' | 'elevated';
  /** Padding size */
  padding?: 'none' | 'sm' | 'md' | 'lg';
  /** Whether the card is interactive (hoverable) */
  interactive?: boolean;
  /** Header action element (e.g., button) */
  action?: ReactNode;
}

/**
 * Card component for grouping related content.
 *
 * @example
 * ```tsx
 * <Card title="Network Status" subtitle="Last scan: 5 min ago">
 *   <DeviceList devices={devices} />
 * </Card>
 * ```
 */
export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      children,
      title,
      subtitle,
      variant = 'default',
      padding = 'md',
      interactive = false,
      action,
      className,
      ...props
    },
    ref
  ) => {
    const hasHeader = title || subtitle || action;

    return (
      <div
        ref={ref}
        className={clsx(
          styles.card,
          styles[`variant-${variant}`],
          styles[`padding-${padding}`],
          interactive && styles.interactive,
          className
        )}
        {...props}
      >
        {hasHeader && (
          <div className={styles.header}>
            <div className={styles.headerText}>
              {title && <h3 className={styles.title}>{title}</h3>}
              {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
            </div>
            {action && <div className={styles.action}>{action}</div>}
          </div>
        )}
        <div className={styles.content}>{children}</div>
      </div>
    );
  }
);

Card.displayName = 'Card';
