/**
 * NetworkLegend component unit tests.
 */

import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { NetworkLegend } from './NetworkLegend';

describe('NetworkLegend', () => {
  it('renders legend title', () => {
    render(<NetworkLegend />);

    expect(screen.getByText('Legend')).toBeInTheDocument();
  });

  it('renders vulnerability status section', () => {
    render(<NetworkLegend />);

    expect(screen.getByText('Vulnerability Status')).toBeInTheDocument();
  });

  it('renders severity levels', () => {
    render(<NetworkLegend />);

    expect(screen.getByText('Critical')).toBeInTheDocument();
    expect(screen.getByText('High')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
    expect(screen.getByText('Safe')).toBeInTheDocument();
  });

  it('renders severity descriptions', () => {
    render(<NetworkLegend />);

    expect(screen.getByText('5+ vulnerabilities')).toBeInTheDocument();
    expect(screen.getByText('3-4 vulnerabilities')).toBeInTheDocument();
    expect(screen.getByText('1-2 vulnerabilities')).toBeInTheDocument();
    expect(screen.getByText('No vulnerabilities')).toBeInTheDocument();
  });

  it('renders device types section', () => {
    render(<NetworkLegend />);

    expect(screen.getByText('Device Types')).toBeInTheDocument();
  });

  it('renders device type labels', () => {
    render(<NetworkLegend />);

    expect(screen.getByText('Router')).toBeInTheDocument();
    expect(screen.getByText('Switch')).toBeInTheDocument();
    expect(screen.getByText('Server')).toBeInTheDocument();
    expect(screen.getByText('Computer')).toBeInTheDocument();
    expect(screen.getByText('Other')).toBeInTheDocument();
  });

  it('renders status section', () => {
    render(<NetworkLegend />);

    expect(screen.getByText('Status')).toBeInTheDocument();
  });

  it('renders online/offline status indicators', () => {
    render(<NetworkLegend />);

    expect(screen.getByText('Online')).toBeInTheDocument();
    expect(screen.getByText('Offline')).toBeInTheDocument();
  });

  it('has proper region role', () => {
    render(<NetworkLegend />);

    expect(screen.getByRole('region', { name: /graph legend/i })).toBeInTheDocument();
  });

  it('legend is open by default', () => {
    render(<NetworkLegend />);

    const details = screen.getByRole('region').querySelector('details');
    expect(details).toHaveAttribute('open');
  });

  it('renders color swatches with correct styles', () => {
    render(<NetworkLegend />);

    // Find color swatch elements
    const swatches = document.querySelectorAll('[class*="colorSwatch"]');
    expect(swatches.length).toBeGreaterThan(0);
  });

  it('renders shape swatches for device types', () => {
    render(<NetworkLegend />);

    const shapeSwatches = document.querySelectorAll('[class*="shapeSwatch"]');
    expect(shapeSwatches.length).toBeGreaterThan(0);
  });
});
