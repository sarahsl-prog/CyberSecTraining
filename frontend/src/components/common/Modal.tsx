/**
 * Modal component.
 *
 * An accessible modal dialog component that traps focus and handles
 * keyboard navigation. Uses the native <dialog> element for proper
 * accessibility and stacking context.
 */

import { useEffect, useRef, useCallback, type ReactNode } from 'react';
import { Button } from './Button';
import styles from './Modal.module.css';

/**
 * Props for Modal component.
 */
export interface ModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Handler called when modal should close */
  onClose: () => void;
  /** Modal title displayed in header */
  title: string;
  /** Modal content */
  children: ReactNode;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg' | 'xl';
  /** Whether to show close button in header */
  showCloseButton?: boolean;
  /** Additional class name for the modal */
  className?: string;
  /** ID of the element that describes the modal */
  'aria-describedby'?: string;
}

/**
 * Modal component for displaying focused content.
 *
 * Features:
 * - Focus trap within modal
 * - Escape key to close
 * - Click outside to close
 * - Proper ARIA attributes
 * - Animation on open/close
 *
 * @example
 * ```tsx
 * <Modal
 *   isOpen={showModal}
 *   onClose={() => setShowModal(false)}
 *   title="Device Details"
 * >
 *   <p>Modal content here</p>
 * </Modal>
 * ```
 */
export function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  showCloseButton = true,
  className = '',
  'aria-describedby': ariaDescribedBy,
}: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  /**
   * Handle escape key press.
   */
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
      }
    },
    [onClose]
  );

  /**
   * Handle click on backdrop.
   */
  const handleBackdropClick = useCallback(
    (event: React.MouseEvent<HTMLDialogElement>) => {
      // Only close if clicking the backdrop (dialog element itself)
      if (event.target === dialogRef.current) {
        onClose();
      }
    },
    [onClose]
  );

  /**
   * Open/close the dialog based on isOpen prop.
   */
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen) {
      // Store currently focused element
      previousActiveElement.current = document.activeElement as HTMLElement;

      // Show modal
      dialog.showModal();

      // Focus first focusable element or the dialog itself
      const firstFocusable = dialog.querySelector<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (firstFocusable) {
        firstFocusable.focus();
      }
    } else {
      dialog.close();

      // Restore focus to previously focused element
      if (previousActiveElement.current) {
        previousActiveElement.current.focus();
      }
    }
  }, [isOpen]);

  /**
   * Add keyboard listener.
   */
  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, handleKeyDown]);

  return (
    <dialog
      ref={dialogRef}
      className={`${styles.modal} ${styles[`size-${size}`]} ${className}`}
      onClick={handleBackdropClick}
      aria-labelledby="modal-title"
      aria-describedby={ariaDescribedBy}
      aria-modal="true"
    >
      <div className={styles.container}>
        <header className={styles.header}>
          <h2 id="modal-title" className={styles.title}>
            {title}
          </h2>
          {showCloseButton && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              aria-label="Close modal"
              className={styles.closeButton}
            >
              ✕
            </Button>
          )}
        </header>
        <div className={styles.content}>{children}</div>
      </div>
    </dialog>
  );
}
