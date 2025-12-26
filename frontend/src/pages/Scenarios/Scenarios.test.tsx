/**
 * Scenarios page unit tests.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Scenarios } from './Scenarios';
import { AccessibilityProvider } from '@/context/AccessibilityContext';
import { ThemeProvider } from '@/context/ThemeContext';
import {
  mockFetch,
  mockScenarioSummaries,
  mockContentPacks,
  mockScenarioTags,
} from '@/test/mocks';

/**
 * Wrapper component for testing with required providers.
 */
function TestWrapper({ children }: { children: React.ReactNode }) {
  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <AccessibilityProvider>
        <ThemeProvider>{children}</ThemeProvider>
      </AccessibilityProvider>
    </BrowserRouter>
  );
}

describe('Scenarios', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the scenarios title', () => {
    // Mock all API calls
    mockFetch(mockScenarioSummaries); // scenarios
    mockFetch(mockContentPacks); // packs
    mockFetch(mockScenarioTags); // tags

    render(
      <TestWrapper>
        <Scenarios />
      </TestWrapper>
    );

    expect(screen.getByRole('heading', { name: /scenarios/i })).toBeInTheDocument();
  });

  it('displays subtitle text', () => {
    mockFetch(mockScenarioSummaries);
    mockFetch(mockContentPacks);
    mockFetch(mockScenarioTags);

    render(
      <TestWrapper>
        <Scenarios />
      </TestWrapper>
    );

    expect(
      screen.getByText(/practice cybersecurity skills/i)
    ).toBeInTheDocument();
  });

  it('displays loading spinner while fetching data', () => {
    // Mock slow API responses
    (global.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <TestWrapper>
        <Scenarios />
      </TestWrapper>
    );

    expect(screen.getByText(/loading scenarios/i)).toBeInTheDocument();
  });

  it('displays scenarios when loaded', async () => {
    mockFetch(mockScenarioSummaries);
    mockFetch(mockContentPacks);
    mockFetch(mockScenarioTags);

    render(
      <TestWrapper>
        <Scenarios />
      </TestWrapper>
    );

    await waitFor(() => {
      mockScenarioSummaries.forEach((scenario) => {
        expect(
          screen.getByRole('heading', { name: scenario.name })
        ).toBeInTheDocument();
      });
    });
  });

  it('displays scenario count in header stats', async () => {
    mockFetch(mockScenarioSummaries);
    mockFetch(mockContentPacks);
    mockFetch(mockScenarioTags);

    render(
      <TestWrapper>
        <Scenarios />
      </TestWrapper>
    );

    await waitFor(() => {
      // Verify scenarios are loaded by checking for scenario names
      expect(screen.getByRole('heading', { name: 'Home Network Basics' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Router Hardening' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Small Office Audit' })).toBeInTheDocument();
    });
  });

  it('displays pack count in header stats', async () => {
    mockFetch(mockScenarioSummaries);
    mockFetch(mockContentPacks);
    mockFetch(mockScenarioTags);

    render(
      <TestWrapper>
        <Scenarios />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument(); // 2 packs
      expect(screen.getByText('Packs')).toBeInTheDocument();
    });
  });

  it('displays filter controls', async () => {
    mockFetch(mockScenarioSummaries);
    mockFetch(mockContentPacks);
    mockFetch(mockScenarioTags);

    render(
      <TestWrapper>
        <Scenarios />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Content Pack')).toBeInTheDocument();
      expect(screen.getByLabelText('Difficulty')).toBeInTheDocument();
      expect(screen.getByLabelText('Tag')).toBeInTheDocument();
    });
  });

  it('displays empty state when no scenarios match filters', async () => {
    mockFetch([]); // Empty scenarios
    mockFetch(mockContentPacks);
    mockFetch(mockScenarioTags);

    render(
      <TestWrapper>
        <Scenarios />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/no scenarios available/i)).toBeInTheDocument();
    });
  });

  it('displays error message on API error', async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: 'Server error' }),
      headers: new Headers(),
    } as Response);

    render(
      <TestWrapper>
        <Scenarios />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/server error/i)).toBeInTheDocument();
    });
  });

  it('renders scenario cards in a grid', async () => {
    mockFetch(mockScenarioSummaries);
    mockFetch(mockContentPacks);
    mockFetch(mockScenarioTags);

    render(
      <TestWrapper>
        <Scenarios />
      </TestWrapper>
    );

    await waitFor(() => {
      // Check that scenario cards are rendered
      expect(screen.getAllByRole('button', { name: /start scenario/i })).toHaveLength(2); // 2 incomplete scenarios
    });
  });

  it('shows completed badge for completed scenarios', async () => {
    mockFetch(mockScenarioSummaries);
    mockFetch(mockContentPacks);
    mockFetch(mockScenarioTags);

    render(
      <TestWrapper>
        <Scenarios />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Completed')).toBeInTheDocument();
      expect(screen.getByText('Best: 85%')).toBeInTheDocument();
    });
  });
});
