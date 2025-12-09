/**
 * Settings page unit tests.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { Settings } from './Settings';
import { AccessibilityProvider } from '@/context/AccessibilityContext';
import { ThemeProvider } from '@/context/ThemeContext';

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

describe('Settings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders the page title', () => {
    render(
      <TestWrapper>
        <Settings />
      </TestWrapper>
    );

    expect(screen.getByRole('heading', { name: /settings/i })).toBeInTheDocument();
  });

  it('displays accessibility section', () => {
    render(
      <TestWrapper>
        <Settings />
      </TestWrapper>
    );

    expect(screen.getByText('Accessibility')).toBeInTheDocument();
  });

  it('displays color mode options', () => {
    render(
      <TestWrapper>
        <Settings />
      </TestWrapper>
    );

    expect(screen.getByText('Light')).toBeInTheDocument();
    expect(screen.getByText('Dark')).toBeInTheDocument();
    expect(screen.getByText('High Contrast')).toBeInTheDocument();
    expect(screen.getByText('Protanopia')).toBeInTheDocument();
    expect(screen.getByText('Deuteranopia')).toBeInTheDocument();
    expect(screen.getByText('Tritanopia')).toBeInTheDocument();
  });

  it('allows selecting color mode', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Settings />
      </TestWrapper>
    );

    const darkOption = screen.getByText('Dark');
    await user.click(darkOption);

    // The radio should be checked
    const radio = screen.getByDisplayValue('dark');
    expect(radio).toBeChecked();
  });

  it('displays font size options', () => {
    render(
      <TestWrapper>
        <Settings />
      </TestWrapper>
    );

    expect(screen.getByText('Normal')).toBeInTheDocument();
    expect(screen.getByText('Large')).toBeInTheDocument();
    expect(screen.getByText('Extra Large')).toBeInTheDocument();
    expect(screen.getByText('Maximum')).toBeInTheDocument();
  });

  it('allows changing font size with buttons', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Settings />
      </TestWrapper>
    );

    const largeButton = screen.getByRole('button', { name: /large/i });
    await user.click(largeButton);

    expect(largeButton).toHaveAttribute('aria-pressed', 'true');
  });

  it('displays font size slider', () => {
    render(
      <TestWrapper>
        <Settings />
      </TestWrapper>
    );

    const slider = screen.getByRole('slider');
    expect(slider).toBeInTheDocument();
    expect(slider).toHaveAttribute('min', '100');
    expect(slider).toHaveAttribute('max', '200');
  });

  it('displays reduce motion toggle', () => {
    render(
      <TestWrapper>
        <Settings />
      </TestWrapper>
    );

    expect(screen.getByText('Reduce Motion')).toBeInTheDocument();
    const toggles = screen.getAllByRole('switch');
    expect(toggles.length).toBeGreaterThan(0);
  });

  it('displays focus indicators toggle', () => {
    render(
      <TestWrapper>
        <Settings />
      </TestWrapper>
    );

    expect(screen.getByText('Enhanced Focus Indicators')).toBeInTheDocument();
  });

  it('displays screen reader optimization toggle', () => {
    render(
      <TestWrapper>
        <Settings />
      </TestWrapper>
    );

    expect(screen.getByText('Screen Reader Optimized')).toBeInTheDocument();
  });

  it('displays scan preferences section', () => {
    render(
      <TestWrapper>
        <Settings />
      </TestWrapper>
    );

    expect(screen.getByText('Scan Preferences')).toBeInTheDocument();
    expect(screen.getByText('Default Scan Type')).toBeInTheDocument();
  });

  it('displays AI assistant section', () => {
    render(
      <TestWrapper>
        <Settings />
      </TestWrapper>
    );

    expect(screen.getByText('AI Assistant')).toBeInTheDocument();
    expect(screen.getByText('Explanation Detail Level')).toBeInTheDocument();
  });

  it('displays privacy section', () => {
    render(
      <TestWrapper>
        <Settings />
      </TestWrapper>
    );

    expect(screen.getByText('Privacy')).toBeInTheDocument();
    expect(screen.getByText('Store Scan History')).toBeInTheDocument();
    expect(screen.getByText('Clear Data')).toBeInTheDocument();
  });

  it('displays reset settings button', () => {
    render(
      <TestWrapper>
        <Settings />
      </TestWrapper>
    );

    expect(
      screen.getByRole('button', { name: /reset all settings/i })
    ).toBeInTheDocument();
  });

  it('toggles reduce motion when clicked', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <Settings />
      </TestWrapper>
    );

    // Find the reduce motion toggle
    const toggles = screen.getAllByRole('switch');
    const reduceMotionToggle = toggles[0]; // First toggle is reduce motion

    const initialState = reduceMotionToggle.getAttribute('aria-checked');
    await user.click(reduceMotionToggle);

    expect(reduceMotionToggle.getAttribute('aria-checked')).not.toBe(initialState);
  });

  it('has accessible labels for all controls', () => {
    render(
      <TestWrapper>
        <Settings />
      </TestWrapper>
    );

    // All switches should have proper aria attributes
    const switches = screen.getAllByRole('switch');
    switches.forEach((sw) => {
      expect(sw).toHaveAttribute('aria-checked');
    });

    // Slider should have proper attributes
    const slider = screen.getByRole('slider');
    expect(slider).toHaveAttribute('aria-valuenow');
  });
});
