/**
 * ModeContext unit tests.
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { ModeProvider, useMode } from './ModeContext';
import { mockFetch, mockFetchError } from '@/test/mocks';

// Error boundary for testing error cases
class TestErrorBoundary extends React.Component<
  { children: React.ReactNode; onError?: (error: Error) => void },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode; onError?: (error: Error) => void }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error) {
    this.props.onError?.(error);
  }

  render() {
    if (this.state.hasError) {
      return <div data-testid="error-boundary">{this.state.error?.message}</div>;
    }
    return this.props.children;
  }
}

// Test component that uses the hook
function TestComponent() {
  const { mode, isLoading, error, setMode, toggleMode } = useMode();

  return (
    <div>
      <div data-testid="mode">{mode}</div>
      <div data-testid="loading">{isLoading ? 'loading' : 'not-loading'}</div>
      <div data-testid="error">{error || 'no-error'}</div>
      <button data-testid="set-training" onClick={() => setMode('training')}>
        Set Training
      </button>
      <button data-testid="set-live" onClick={() => setMode('live')}>
        Set Live
      </button>
      <button data-testid="toggle" onClick={() => toggleMode()}>
        Toggle
      </button>
    </div>
  );
}

describe('ModeContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock fetch globally
    global.fetch = vi.fn();
  });

  describe('Initialization', () => {
    it('defaults to training mode', async () => {
      mockFetch({ mode: 'training', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <TestComponent />
        </ModeProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('mode')).toHaveTextContent('training');
      });
    });

    it('loads mode from backend on mount', async () => {
      mockFetch({ mode: 'live', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <TestComponent />
        </ModeProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('mode')).toHaveTextContent('live');
      });
    });

    it('uses localStorage as fallback when backend fails', async () => {
      // Mock localStorage to return 'live'
      (localStorage.getItem as ReturnType<typeof vi.fn>).mockReturnValue('live');
      mockFetchError('Network error', 500);

      render(
        <ModeProvider>
          <TestComponent />
        </ModeProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('mode')).toHaveTextContent('live');
      });
    });

    it('defaults to training when both backend and localStorage fail', async () => {
      mockFetchError('Network error', 500);

      render(
        <ModeProvider>
          <TestComponent />
        </ModeProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('mode')).toHaveTextContent('training');
      });
    });

    it('shows loading state during initialization', async () => {
      mockFetch({ mode: 'training', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <TestComponent />
        </ModeProvider>
      );

      // Should start with loading
      expect(screen.getByTestId('loading')).toHaveTextContent('loading');

      // Should finish loading
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
      });
    });
  });

  describe('setMode', () => {
    it('updates mode to live', async () => {
      // Initial fetch
      mockFetch({ mode: 'training', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <TestComponent />
        </ModeProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('mode')).toHaveTextContent('training');
      });

      // Mock the POST request
      mockFetch({ mode: 'live', require_confirmation_for_live: true });

      // Click to set live mode
      await act(async () => {
        screen.getByTestId('set-live').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('mode')).toHaveTextContent('live');
      });
    });

    it('updates mode to training', async () => {
      // Initial fetch (live mode)
      mockFetch({ mode: 'live', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <TestComponent />
        </ModeProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('mode')).toHaveTextContent('live');
      });

      // Mock the POST request
      mockFetch({ mode: 'training', require_confirmation_for_live: true });

      // Click to set training mode
      await act(async () => {
        screen.getByTestId('set-training').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('mode')).toHaveTextContent('training');
      });
    });

    it('calls localStorage.setItem when mode changes', async () => {
      // Initial fetch
      mockFetch({ mode: 'training', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <TestComponent />
        </ModeProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('mode')).toHaveTextContent('training');
      });

      // Mock the POST request
      mockFetch({ mode: 'live', require_confirmation_for_live: true });

      // Click to set live mode
      await act(async () => {
        screen.getByTestId('set-live').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('mode')).toHaveTextContent('live');
        // Verify setItem was called with the new mode
        expect(localStorage.setItem).toHaveBeenCalledWith('cybersec-app-mode', 'live');
      });
    });

    it('handles backend save error', async () => {
      // Initial fetch
      mockFetch({ mode: 'training', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <TestComponent />
        </ModeProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('mode')).toHaveTextContent('training');
      });

      // Mock the POST request failure
      mockFetchError('Failed to save', 500);

      // Click to set live mode
      await act(async () => {
        screen.getByTestId('set-live').click();
      });

      await waitFor(() => {
        // Mode should not change
        expect(screen.getByTestId('mode')).toHaveTextContent('training');
        // Error should be displayed
        expect(screen.getByTestId('error')).toHaveTextContent('Failed to save');
      });
    });

    it('skips update if mode is already set', async () => {
      // Initial fetch
      mockFetch({ mode: 'training', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <TestComponent />
        </ModeProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('mode')).toHaveTextContent('training');
      });

      const initialFetchCount = (global.fetch as ReturnType<typeof vi.fn>).mock.calls.length;

      // Click to set training mode (already training)
      await act(async () => {
        screen.getByTestId('set-training').click();
      });

      // Should not make additional fetch calls
      expect((global.fetch as ReturnType<typeof vi.fn>).mock.calls.length).toBe(initialFetchCount);
    });
  });

  describe('toggleMode', () => {
    it('toggles from training to live', async () => {
      // Initial fetch (training)
      mockFetch({ mode: 'training', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <TestComponent />
        </ModeProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('mode')).toHaveTextContent('training');
      });

      // Mock the POST request
      mockFetch({ mode: 'live', require_confirmation_for_live: true });

      // Click toggle
      await act(async () => {
        screen.getByTestId('toggle').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('mode')).toHaveTextContent('live');
      });
    });

    it('toggles from live to training', async () => {
      // Initial fetch (live)
      mockFetch({ mode: 'live', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <TestComponent />
        </ModeProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('mode')).toHaveTextContent('live');
      });

      // Mock the POST request
      mockFetch({ mode: 'training', require_confirmation_for_live: true });

      // Click toggle
      await act(async () => {
        screen.getByTestId('toggle').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('mode')).toHaveTextContent('training');
      });
    });
  });

  describe('Screen reader announcements', () => {
    it('renders hidden live region for announcements', async () => {
      mockFetch({ mode: 'training', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <TestComponent />
        </ModeProvider>
      );

      await waitFor(() => {
        const liveRegion = screen.getByRole('status');
        expect(liveRegion).toBeInTheDocument();
        expect(liveRegion).toHaveAttribute('aria-live', 'polite');
        expect(liveRegion).toHaveClass('sr-only');
      });
    });
  });

  describe('useMode hook', () => {
    it('throws error when used outside provider', async () => {
      // Suppress all error output for this intentional error test
      const originalError = console.error;
      const originalWarn = console.warn;
      console.error = vi.fn();
      console.warn = vi.fn();

      // Also suppress jsdom's unhandled error reporting
      const originalAddEventListener = window.addEventListener;
      window.addEventListener = vi.fn((event, handler) => {
        if (event === 'error') return; // Suppress error events
        return originalAddEventListener.call(window, event, handler);
      });

      let caughtError: Error | null = null;

      render(
        <TestErrorBoundary onError={(err) => { caughtError = err; }}>
          <TestComponent />
        </TestErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByTestId('error-boundary')).toHaveTextContent(
          'useMode must be used within a ModeProvider'
        );
      });

      expect((caughtError as Error | null)?.message).toBe('useMode must be used within a ModeProvider');

      // Restore all handlers
      console.error = originalError;
      console.warn = originalWarn;
      window.addEventListener = originalAddEventListener;
    });
  });
});
