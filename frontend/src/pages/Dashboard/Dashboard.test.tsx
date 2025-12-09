/**
 * Dashboard page unit tests.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Dashboard } from './Dashboard';
import { AccessibilityProvider } from '@/context/AccessibilityContext';
import { ThemeProvider } from '@/context/ThemeContext';
import {
  mockFetch,
  mockDevices,
  mockVulnerabilitySummary,
  mockScanResponse,
} from '@/test/mocks';

/**
 * Wrapper component for testing with required providers.
 */
function TestWrapper({ children }: { children: React.ReactNode }) {
  return (
    <BrowserRouter>
      <AccessibilityProvider>
        <ThemeProvider>{children}</ThemeProvider>
      </AccessibilityProvider>
    </BrowserRouter>
  );
}

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the dashboard title', () => {
    // Mock all API calls
    mockFetch({ items: [], total: 0, page: 1, page_size: 5, pages: 0 }); // scans
    mockFetch(mockVulnerabilitySummary); // summary
    mockFetch({ items: [], total: 0, page: 1, page_size: 1, pages: 0 }); // devices

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument();
  });

  it('displays loading spinners while fetching data', () => {
    // Mock slow API responses
    (global.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    // Should show loading state
    expect(screen.getAllByRole('status').length).toBeGreaterThan(0);
  });

  it('displays start new scan button', () => {
    mockFetch({ items: [], total: 0, page: 1, page_size: 5, pages: 0 });
    mockFetch(mockVulnerabilitySummary);
    mockFetch({ items: [], total: 0, page: 1, page_size: 1, pages: 0 });

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    expect(screen.getByRole('button', { name: /start new scan/i })).toBeInTheDocument();
  });

  it('displays vulnerability summary when loaded', async () => {
    mockFetch({ items: [], total: 0, page: 1, page_size: 5, pages: 0 }); // scans
    mockFetch(mockVulnerabilitySummary); // summary
    mockFetch({ items: mockDevices, total: 3, page: 1, page_size: 1, pages: 3 }); // devices

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Critical')).toBeInTheDocument();
      expect(screen.getByText('High')).toBeInTheDocument();
      expect(screen.getByText('Medium')).toBeInTheDocument();
    });
  });

  it('displays recent scans when loaded', async () => {
    const scanResponse = {
      items: [mockScanResponse],
      total: 1,
      page: 1,
      page_size: 5,
      pages: 1,
    };

    mockFetch(scanResponse); // scans
    mockFetch(mockVulnerabilitySummary); // summary
    mockFetch({ items: mockDevices, total: 3, page: 1, page_size: 1, pages: 3 }); // devices

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(mockScanResponse.target_range)).toBeInTheDocument();
    });
  });

  it('displays empty state when no scans exist', async () => {
    mockFetch({ items: [], total: 0, page: 1, page_size: 5, pages: 0 }); // scans
    mockFetch(mockVulnerabilitySummary); // summary
    mockFetch({ items: [], total: 0, page: 1, page_size: 1, pages: 0 }); // devices

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/no scans yet/i)).toBeInTheDocument();
    });
  });

  it('displays stat cards with data', async () => {
    mockFetch({ items: [], total: 0, page: 1, page_size: 5, pages: 0 }); // scans
    mockFetch(mockVulnerabilitySummary); // summary
    mockFetch({ items: mockDevices, total: 3, page: 1, page_size: 1, pages: 3 }); // devices

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Total Devices')).toBeInTheDocument();
      expect(screen.getByText('Vulnerabilities')).toBeInTheDocument();
      expect(screen.getByText('Critical Issues')).toBeInTheDocument();
      expect(screen.getByText('Fixed')).toBeInTheDocument();
    });
  });

  it('displays quick actions section', () => {
    mockFetch({ items: [], total: 0, page: 1, page_size: 5, pages: 0 });
    mockFetch(mockVulnerabilitySummary);
    mockFetch({ items: [], total: 0, page: 1, page_size: 1, pages: 0 });

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    expect(screen.getByText('Quick Actions')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /network scan/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /view scenarios/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /settings/i })).toBeInTheDocument();
  });
});
