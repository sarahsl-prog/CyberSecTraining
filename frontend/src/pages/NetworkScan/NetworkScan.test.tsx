/**
 * Network Scan page unit tests.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { NetworkScan } from './NetworkScan';
import { AccessibilityProvider } from '@/context/AccessibilityContext';
import { ThemeProvider } from '@/context/ThemeContext';
import { ModeProvider } from '@/context/ModeContext';
import { mockFetch, mockNetworkInterface, mockScanResponse } from '@/test/mocks';

/**
 * Wrapper component for testing with required providers.
 */
function TestWrapper({ children }: { children: React.ReactNode }) {
  return (
    <BrowserRouter>
      <AccessibilityProvider>
        <ThemeProvider>
          <ModeProvider>{children}</ModeProvider>
        </ThemeProvider>
      </AccessibilityProvider>
    </BrowserRouter>
  );
}

describe('NetworkScan', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('renders the page title', () => {
    // Mock API calls in the order they occur
    mockFetch(mockNetworkInterface); // network detect
    mockFetch({ items: [], total: 0, page: 1, page_size: 10, pages: 0 }); // scan history
    mockFetch({ mode: 'training', require_confirmation_for_live: true }); // mode API

    render(
      <TestWrapper>
        <NetworkScan />
      </TestWrapper>
    );

    expect(screen.getByRole('heading', { name: /network scan/i })).toBeInTheDocument();
  });

  it('displays the scan form', () => {
    mockFetch(mockNetworkInterface);
    mockFetch({ items: [], total: 0, page: 1, page_size: 10, pages: 0 });
    mockFetch({ mode: 'training', require_confirmation_for_live: true });

    render(
      <TestWrapper>
        <NetworkScan />
      </TestWrapper>
    );

    expect(screen.getByLabelText(/network target/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /start scan/i })).toBeInTheDocument();
  });

  it('auto-populates detected network', async () => {
    mockFetch(mockNetworkInterface);
    mockFetch({ items: [], total: 0, page: 1, page_size: 10, pages: 0 });
    mockFetch({ mode: 'training', require_confirmation_for_live: true });

    render(
      <TestWrapper>
        <NetworkScan />
      </TestWrapper>
    );

    await waitFor(() => {
      const input = screen.getByLabelText(/network target/i) as HTMLInputElement;
      expect(input.value).toBe(mockNetworkInterface.network);
    });
  });

  it('displays scan type options', () => {
    mockFetch(mockNetworkInterface);
    mockFetch({ items: [], total: 0, page: 1, page_size: 10, pages: 0 });
    mockFetch({ mode: 'training', require_confirmation_for_live: true });

    render(
      <TestWrapper>
        <NetworkScan />
      </TestWrapper>
    );

    expect(screen.getByText('Quick Scan')).toBeInTheDocument();
    expect(screen.getByText('Deep Scan')).toBeInTheDocument();
    expect(screen.getByText('Vulnerability Scan')).toBeInTheDocument();
  });

  it('requires consent checkbox to start scan', () => {
    mockFetch(mockNetworkInterface);
    mockFetch({ items: [], total: 0, page: 1, page_size: 10, pages: 0 });
    mockFetch({ mode: 'training', require_confirmation_for_live: true });

    render(
      <TestWrapper>
        <NetworkScan />
      </TestWrapper>
    );

    const submitButton = screen.getByRole('button', { name: /start scan/i });
    expect(submitButton).toBeDisabled();
  });

  it('enables submit button when consent is given', async () => {
    mockFetch(mockNetworkInterface);
    mockFetch({ items: [], total: 0, page: 1, page_size: 10, pages: 0 });
    mockFetch({ mode: 'training', require_confirmation_for_live: true });

    const user = userEvent.setup();

    render(
      <TestWrapper>
        <NetworkScan />
      </TestWrapper>
    );

    // Wait for network detection
    await waitFor(() => {
      const input = screen.getByLabelText(/network target/i) as HTMLInputElement;
      expect(input.value).toBeTruthy();
    });

    // Check consent checkbox
    const checkbox = screen.getByRole('checkbox');
    await user.click(checkbox);

    // Wait for state update
    await waitFor(() => {
      const submitButton = screen.getByRole('button', { name: /start scan/i });
      expect(submitButton).not.toBeDisabled();
    });
  });

  it('displays consent text (training mode)', () => {
    mockFetch(mockNetworkInterface);
    mockFetch({ items: [], total: 0, page: 1, page_size: 10, pages: 0 });
    mockFetch({ mode: 'training', require_confirmation_for_live: true });

    render(
      <TestWrapper>
        <NetworkScan />
      </TestWrapper>
    );

    expect(
      screen.getByText(/i understand this is a training scan/i)
    ).toBeInTheDocument();
  });

  it('displays scan history section', () => {
    mockFetch(mockNetworkInterface);
    mockFetch({
      items: [mockScanResponse],
      total: 1,
      page: 1,
      page_size: 10,
      pages: 1,
    });
    mockFetch({ mode: 'training', require_confirmation_for_live: true });

    render(
      <TestWrapper>
        <NetworkScan />
      </TestWrapper>
    );

    expect(screen.getByText('Scan History')).toBeInTheDocument();
  });

  it('shows empty state for scan history when no scans', async () => {
    mockFetch(mockNetworkInterface);
    mockFetch({ items: [], total: 0, page: 1, page_size: 10, pages: 0 });
    mockFetch({ mode: 'training', require_confirmation_for_live: true });

    render(
      <TestWrapper>
        <NetworkScan />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/no scan history/i)).toBeInTheDocument();
    });
  });

  it('displays scan history items', async () => {
    mockFetch(mockNetworkInterface);
    mockFetch({
      items: [mockScanResponse],
      total: 1,
      page: 1,
      page_size: 10,
      pages: 1,
    });
    mockFetch({ mode: 'training', require_confirmation_for_live: true });

    render(
      <TestWrapper>
        <NetworkScan />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(mockScanResponse.target_range)).toBeInTheDocument();
    });
  });

  it('allows changing target input', async () => {
    mockFetch(mockNetworkInterface);
    mockFetch({ items: [], total: 0, page: 1, page_size: 10, pages: 0 });
    mockFetch({ mode: 'training', require_confirmation_for_live: true });

    const user = userEvent.setup();

    render(
      <TestWrapper>
        <NetworkScan />
      </TestWrapper>
    );

    const input = screen.getByLabelText(/network target/i) as HTMLInputElement;

    // Wait for network detection to complete and input to be populated
    await waitFor(() => {
      expect(input.value).toBeTruthy();
      expect(input).not.toBeDisabled();
    });

    // Change input value directly using fireEvent
    fireEvent.change(input, { target: { value: '10.0.0.0/24' } });

    // Wait for state update to complete
    await waitFor(() => {
      expect(input).toHaveValue('10.0.0.0/24');
    });
  });

  it('allows selecting different scan types', async () => {
    mockFetch(mockNetworkInterface);
    mockFetch({ items: [], total: 0, page: 1, page_size: 10, pages: 0 });
    mockFetch({ mode: 'training', require_confirmation_for_live: true });

    const user = userEvent.setup();

    render(
      <TestWrapper>
        <NetworkScan />
      </TestWrapper>
    );

    const deepScanOption = screen.getByText('Deep Scan');
    await user.click(deepScanOption);

    // Wait for state update
    await waitFor(() => {
      const radio = screen.getByDisplayValue('deep');
      expect(radio).toBeChecked();
    });
  });
});
