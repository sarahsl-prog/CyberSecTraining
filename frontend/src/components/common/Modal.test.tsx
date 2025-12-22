/**
 * Modal component unit tests.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Modal } from './Modal';

describe('Modal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    title: 'Test Modal',
    children: <p>Modal content</p>,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Mock dialog methods - jsdom doesn't fully support native dialog
    HTMLDialogElement.prototype.showModal = vi.fn(function (this: HTMLDialogElement) {
      this.setAttribute('open', '');
    });
    HTMLDialogElement.prototype.close = vi.fn(function (this: HTMLDialogElement) {
      this.removeAttribute('open');
    });
  });

  it('renders modal when open', () => {
    render(<Modal {...defaultProps} />);

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
    expect(screen.getByText('Modal content')).toBeInTheDocument();
  });

  it('calls showModal when isOpen is true', () => {
    render(<Modal {...defaultProps} />);

    expect(HTMLDialogElement.prototype.showModal).toHaveBeenCalled();
  });

  it('calls close when isOpen becomes false', () => {
    const { rerender } = render(<Modal {...defaultProps} />);

    rerender(<Modal {...defaultProps} isOpen={false} />);

    expect(HTMLDialogElement.prototype.close).toHaveBeenCalled();
  });

  it('renders close button by default', () => {
    render(<Modal {...defaultProps} />);

    expect(screen.getByRole('button', { name: /close modal/i })).toBeInTheDocument();
  });

  it('hides close button when showCloseButton is false', () => {
    render(<Modal {...defaultProps} showCloseButton={false} />);

    expect(screen.queryByRole('button', { name: /close modal/i })).not.toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    render(<Modal {...defaultProps} />);

    fireEvent.click(screen.getByRole('button', { name: /close modal/i }));

    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when Escape key is pressed', () => {
    render(<Modal {...defaultProps} />);

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('applies size class correctly', () => {
    const { rerender } = render(<Modal {...defaultProps} size="sm" />);
    // CSS modules add hash to class names, check for partial match
    expect(screen.getByRole('dialog').className).toMatch(/size-sm/);

    rerender(<Modal {...defaultProps} size="lg" />);
    expect(screen.getByRole('dialog').className).toMatch(/size-lg/);

    rerender(<Modal {...defaultProps} size="xl" />);
    expect(screen.getByRole('dialog').className).toMatch(/size-xl/);
  });

  it('applies custom className', () => {
    render(<Modal {...defaultProps} className="custom-class" />);

    expect(screen.getByRole('dialog')).toHaveClass('custom-class');
  });

  it('has proper ARIA attributes', () => {
    render(<Modal {...defaultProps} aria-describedby="description" />);

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-labelledby', 'modal-title');
    expect(dialog).toHaveAttribute('aria-describedby', 'description');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
  });

  it('renders children correctly', () => {
    render(
      <Modal {...defaultProps}>
        <div data-testid="custom-content">Custom content</div>
      </Modal>
    );

    expect(screen.getByTestId('custom-content')).toBeInTheDocument();
    expect(screen.getByText('Custom content')).toBeInTheDocument();
  });
});
