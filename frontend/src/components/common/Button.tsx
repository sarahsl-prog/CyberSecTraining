/**
 * Button component.
 *
 * An accessible button component with multiple variants
 * and sizes. Supports loading states and icons.
 */

import { forwardRef } from 'react';
import type { ButtonHTMLAttributes, ReactNode } from 'react';
import clsx from 'clsx';
import { Spinner } from './Spinner';
import styles from './Button.module.css';

/**
 * Button component props.
 */
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Button content */
  children: ReactNode;
  /** Visual variant */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive';
  /** Button size */
  size?: 'sm' | 'md' | 'lg';
  /** Show loading spinner */
  isLoading?: boolean;
  /** Loading text (replaces children when loading) */
  loadingText?: string;
  /** Icon before text */
  leftIcon?: ReactNode;
  /** Icon after text */
  rightIcon?: ReactNode;
  /** Full width button */
  fullWidth?: boolean;
}

/**
 * Button component with variants and loading state.
 *
 * @example
 * ```tsx
 * <Button variant="primary" onClick={handleClick}>
 *   Save Changes
 * </Button>
 *
 * <Button
 *   variant="destructive"
 *   isLoading={isDeleting}
 *   loadingText="Deleting..."
 * >
 *   Delete
 * </Button>
 * ```
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      loadingText,
      leftIcon,
      rightIcon,
      fullWidth = false,
      disabled,
      className,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || isLoading;

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={clsx(
          styles.button,
          styles[`variant-${variant}`],
          styles[`size-${size}`],
          fullWidth && styles.fullWidth,
          isLoading && styles.loading,
          className
        )}
        {...props}
      >
        {isLoading && (
          <span className={styles.spinner}>
            <Spinner size="sm" />
          </span>
        )}
        {!isLoading && leftIcon && (
          <span className={styles.icon} aria-hidden="true">
            {leftIcon}
          </span>
        )}
        <span className={styles.content}>
          {isLoading && loadingText ? loadingText : children}
        </span>
        {!isLoading && rightIcon && (
          <span className={styles.icon} aria-hidden="true">
            {rightIcon}
          </span>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';
