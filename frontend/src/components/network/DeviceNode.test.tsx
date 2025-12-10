/**
 * DeviceNode component unit tests.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DeviceNode } from './DeviceNode';
import type { Device } from '@/types';

describe('DeviceNode', () => {
  const mockDevice: Device = {
    id: 'device-1',
    scan_id: 'scan-1',
    ip: '192.168.1.1',
    mac: '00:1A:2B:3C:4D:5E',
    hostname: 'router.local',
    vendor: 'Linksys',
    device_type: 'router',
    os: 'Linux',
    os_accuracy: 95,
    is_up: true,
    last_seen: '2024-12-08T12:00:00Z',
    open_ports: [],
    vulnerability_count: 3,
    created_at: '2024-12-08T12:00:00Z',
    updated_at: '2024-12-08T12:00:00Z',
  };

  it('renders device hostname when available', () => {
    render(<DeviceNode device={mockDevice} />);

    expect(screen.getByText('router.local')).toBeInTheDocument();
    expect(screen.getByText('192.168.1.1')).toBeInTheDocument();
  });

  it('renders IP address when hostname is not available', () => {
    const deviceWithoutHostname = { ...mockDevice, hostname: undefined };
    render(<DeviceNode device={deviceWithoutHostname} />);

    expect(screen.getByText('192.168.1.1')).toBeInTheDocument();
  });

  it('displays vulnerability count badge when device has vulnerabilities', () => {
    render(<DeviceNode device={mockDevice} />);

    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('does not display vulnerability badge when count is 0', () => {
    const safeDevice = { ...mockDevice, vulnerability_count: 0 };
    render(<DeviceNode device={safeDevice} />);

    expect(screen.queryByText('0')).not.toBeInTheDocument();
  });

  it('displays offline indicator when device is not up', () => {
    const offlineDevice = { ...mockDevice, is_up: false };
    render(<DeviceNode device={offlineDevice} />);

    expect(screen.getByText('●')).toBeInTheDocument();
  });

  it('applies selected class when isSelected is true', () => {
    render(<DeviceNode device={mockDevice} isSelected={true} />);

    // CSS modules add hash to class names, check for partial match
    expect(screen.getByRole('button').className).toMatch(/selected/);
    expect(screen.getByRole('button')).toHaveAttribute('aria-pressed', 'true');
  });

  it('applies offline class when device is not up', () => {
    const offlineDevice = { ...mockDevice, is_up: false };
    render(<DeviceNode device={offlineDevice} />);

    // CSS modules add hash to class names, check for partial match
    expect(screen.getByRole('button').className).toMatch(/offline/);
  });

  it('applies severity classes based on vulnerability count', () => {
    // Critical: 5+
    const criticalDevice = { ...mockDevice, vulnerability_count: 5 };
    const { rerender } = render(<DeviceNode device={criticalDevice} />);
    // CSS modules add hash to class names, check for partial match
    expect(screen.getByRole('button').className).toMatch(/severity-critical/);

    // High: 3-4
    const highDevice = { ...mockDevice, vulnerability_count: 3 };
    rerender(<DeviceNode device={highDevice} />);
    expect(screen.getByRole('button').className).toMatch(/severity-high/);

    // Medium: 1-2
    const mediumDevice = { ...mockDevice, vulnerability_count: 1 };
    rerender(<DeviceNode device={mediumDevice} />);
    expect(screen.getByRole('button').className).toMatch(/severity-medium/);
  });

  it('applies size classes correctly', () => {
    const { rerender } = render(<DeviceNode device={mockDevice} size="sm" />);
    // CSS modules add hash to class names, check for partial match
    expect(screen.getByRole('button').className).toMatch(/size-sm/);

    rerender(<DeviceNode device={mockDevice} size="md" />);
    expect(screen.getByRole('button').className).toMatch(/size-md/);

    rerender(<DeviceNode device={mockDevice} size="lg" />);
    expect(screen.getByRole('button').className).toMatch(/size-lg/);
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<DeviceNode device={mockDevice} onClick={handleClick} />);

    fireEvent.click(screen.getByRole('button'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('displays correct icon for different device types', () => {
    const routerDevice = { ...mockDevice, device_type: 'router' };
    const { rerender } = render(<DeviceNode device={routerDevice} />);
    expect(screen.getByText('🌐')).toBeInTheDocument();

    const serverDevice = { ...mockDevice, device_type: 'server' };
    rerender(<DeviceNode device={serverDevice} />);
    expect(screen.getByText('🖥️')).toBeInTheDocument();

    const printerDevice = { ...mockDevice, device_type: 'printer' };
    rerender(<DeviceNode device={printerDevice} />);
    expect(screen.getByText('🖨️')).toBeInTheDocument();
  });

  it('has accessible aria-label with full device information', () => {
    render(<DeviceNode device={mockDevice} />);

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute(
      'aria-label',
      'router.local, router, 3 vulnerabilities, online'
    );
  });

  it('includes offline status in aria-label for offline devices', () => {
    const offlineDevice = { ...mockDevice, is_up: false };
    render(<DeviceNode device={offlineDevice} />);

    const button = screen.getByRole('button');
    expect(button.getAttribute('aria-label')).toContain('offline');
  });
});
