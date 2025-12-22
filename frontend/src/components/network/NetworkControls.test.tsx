/**
 * NetworkControls component unit tests.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { NetworkControls } from './NetworkControls';

describe('NetworkControls', () => {
  const defaultProps = {
    onZoomIn: vi.fn(),
    onZoomOut: vi.fn(),
    onFitView: vi.fn(),
    onCenter: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders zoom in button', () => {
    render(<NetworkControls {...defaultProps} />);

    expect(screen.getByRole('button', { name: /zoom in/i })).toBeInTheDocument();
  });

  it('renders zoom out button', () => {
    render(<NetworkControls {...defaultProps} />);

    expect(screen.getByRole('button', { name: /zoom out/i })).toBeInTheDocument();
  });

  it('renders fit to screen button', () => {
    render(<NetworkControls {...defaultProps} />);

    expect(screen.getByRole('button', { name: /fit all nodes/i })).toBeInTheDocument();
  });

  it('renders center view button', () => {
    render(<NetworkControls {...defaultProps} />);

    expect(screen.getByRole('button', { name: /center view/i })).toBeInTheDocument();
  });

  it('calls onZoomIn when zoom in button is clicked', () => {
    render(<NetworkControls {...defaultProps} />);

    fireEvent.click(screen.getByRole('button', { name: /zoom in/i }));

    expect(defaultProps.onZoomIn).toHaveBeenCalledTimes(1);
  });

  it('calls onZoomOut when zoom out button is clicked', () => {
    render(<NetworkControls {...defaultProps} />);

    fireEvent.click(screen.getByRole('button', { name: /zoom out/i }));

    expect(defaultProps.onZoomOut).toHaveBeenCalledTimes(1);
  });

  it('calls onFitView when fit button is clicked', () => {
    render(<NetworkControls {...defaultProps} />);

    fireEvent.click(screen.getByRole('button', { name: /fit all nodes/i }));

    expect(defaultProps.onFitView).toHaveBeenCalledTimes(1);
  });

  it('calls onCenter when center view button is clicked', () => {
    render(<NetworkControls {...defaultProps} />);

    fireEvent.click(screen.getByRole('button', { name: /center view/i }));

    expect(defaultProps.onCenter).toHaveBeenCalledTimes(1);
  });

  it('has proper toolbar role', () => {
    render(<NetworkControls {...defaultProps} />);

    expect(screen.getByRole('toolbar', { name: /graph controls/i })).toBeInTheDocument();
  });

  it('has proper aria-label', () => {
    render(<NetworkControls {...defaultProps} />);

    expect(screen.getByRole('toolbar')).toHaveAttribute('aria-label', 'Graph controls');
  });
});
