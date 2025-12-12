/**
 * ModeBanner component unit tests.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ModeBanner } from './ModeBanner';
import { ModeProvider } from '@/context/ModeContext';
import { mockFetch } from '@/test/mocks';

describe('ModeBanner', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  describe('Training Mode', () => {
    it('renders training mode banner', async () => {
      mockFetch({ mode: 'training', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <ModeBanner />
        </ModeProvider>
      );

      // Wait for context to initialize
      await screen.findByText(/Training Mode Active/i);

      expect(screen.getByText(/Training Mode Active/i)).toBeInTheDocument();
      expect(screen.getByText(/Safe Practice Environment/i)).toBeInTheDocument();
    });

    it('displays graduation cap icon for training mode', async () => {
      mockFetch({ mode: 'training', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <ModeBanner />
        </ModeProvider>
      );

      await screen.findByText(/Training Mode Active/i);

      const icon = screen.getByText('🎓');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveAttribute('aria-hidden', 'true');
    });

    it('applies training mode styling', async () => {
      mockFetch({ mode: 'training', require_confirmation_for_live: true });

      const { container } = render(
        <ModeProvider>
          <ModeBanner />
        </ModeProvider>
      );

      await screen.findByText(/Training Mode Active/i);

      const banner = container.querySelector('[role="banner"]');
      expect(banner?.className).toMatch(/training/);
    });
  });

  describe('Live Mode', () => {
    it('renders live mode banner', async () => {
      mockFetch({ mode: 'live', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <ModeBanner />
        </ModeProvider>
      );

      await screen.findByText(/Live Scanning Mode Active/i);

      expect(screen.getByText(/Live Scanning Mode Active/i)).toBeInTheDocument();
      expect(screen.getByText(/Real Network Scanning/i)).toBeInTheDocument();
    });

    it('displays lightning bolt icon for live mode', async () => {
      mockFetch({ mode: 'live', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <ModeBanner />
        </ModeProvider>
      );

      await screen.findByText(/Live Scanning Mode Active/i);

      const icon = screen.getByText('⚡');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveAttribute('aria-hidden', 'true');
    });

    it('applies live mode styling', async () => {
      mockFetch({ mode: 'live', require_confirmation_for_live: true });

      const { container } = render(
        <ModeProvider>
          <ModeBanner />
        </ModeProvider>
      );

      await screen.findByText(/Live Scanning Mode Active/i);

      const banner = container.querySelector('[role="banner"]');
      expect(banner?.className).toMatch(/live/);
    });
  });

  describe('Accessibility', () => {
    it('has banner role', async () => {
      mockFetch({ mode: 'training', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <ModeBanner />
        </ModeProvider>
      );

      await screen.findByText(/Training Mode Active/i);

      const banner = screen.getByRole('banner');
      expect(banner).toBeInTheDocument();
    });

    it('has aria-live="polite" for screen reader announcements', async () => {
      mockFetch({ mode: 'training', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <ModeBanner />
        </ModeProvider>
      );

      await screen.findByText(/Training Mode Active/i);

      const banner = screen.getByRole('banner');
      expect(banner).toHaveAttribute('aria-live', 'polite');
      expect(banner).toHaveAttribute('aria-atomic', 'true');
    });

    it('hides decorative icon from screen readers', async () => {
      mockFetch({ mode: 'training', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <ModeBanner />
        </ModeProvider>
      );

      await screen.findByText(/Training Mode Active/i);

      const icon = screen.getByText('🎓');
      expect(icon).toHaveAttribute('aria-hidden', 'true');
    });

    it('provides descriptive text for screen readers', async () => {
      mockFetch({ mode: 'training', require_confirmation_for_live: true });

      render(
        <ModeProvider>
          <ModeBanner />
        </ModeProvider>
      );

      await screen.findByText(/Training Mode Active/i);

      expect(screen.getByText(/Training Mode Active/i)).toBeInTheDocument();
      expect(screen.getByText(/Safe Practice Environment/i)).toBeInTheDocument();
      expect(screen.getByText(/Using Simulated Data/i)).toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
    it('accepts custom className', async () => {
      mockFetch({ mode: 'training', require_confirmation_for_live: true });

      const { container } = render(
        <ModeProvider>
          <ModeBanner className="custom-class" />
        </ModeProvider>
      );

      await screen.findByText(/Training Mode Active/i);

      const banner = container.querySelector('[role="banner"]');
      expect(banner).toHaveClass('custom-class');
    });
  });
});
