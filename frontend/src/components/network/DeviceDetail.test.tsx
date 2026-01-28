/**
 * DeviceDetail component unit tests.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DeviceDetail } from './DeviceDetail';
import type { Device, Vulnerability } from '@/types';

// Mock the hooks module
vi.mock('@/hooks', () => ({
  useVulnerabilityList: vi.fn(() => ({
    vulnerabilities: [],
    isLoading: false,
    error: null,
  })),
}));

// Import after mocking
import { useVulnerabilityList } from '@/hooks';

describe('DeviceDetail', () => {
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
    open_ports: [
      { port: 80, protocol: 'tcp', state: 'open', service: 'http' },
      { port: 443, protocol: 'tcp', state: 'open', service: 'https' },
    ],
    vulnerability_count: 2,
    created_at: '2024-12-08T12:00:00Z',
    updated_at: '2024-12-08T12:00:00Z',
  };

  const mockVulnerabilities: Vulnerability[] = [
    {
      id: 'vuln-1',
      device_id: 'device-1',
      vuln_type: 'default_credentials',
      severity: 'high',
      title: 'Default Credentials Detected',
      description: 'Device using default credentials',
      is_fixed: false,
      verified_fixed: false,
    },
    {
      id: 'vuln-2',
      device_id: 'device-1',
      vuln_type: 'open_telnet',
      severity: 'critical',
      title: 'Telnet Service Exposed',
      is_fixed: true,
      verified_fixed: false,
    },
  ];

  const defaultProps = {
    device: mockDevice,
    isOpen: true,
    onClose: vi.fn(),
    onVulnerabilitySelect: vi.fn(),
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

    // Reset hook mock
    (useVulnerabilityList as ReturnType<typeof vi.fn>).mockReturnValue({
      vulnerabilities: [],
      isLoading: false,
      error: null,
    });
  });

  it('renders nothing when device is null', () => {
    const { container } = render(<DeviceDetail {...defaultProps} device={null} />);

    expect(container.firstChild).toBeNull();
  });

  it('renders device hostname in header', () => {
    render(<DeviceDetail {...defaultProps} />);

    expect(screen.getByRole('heading', { name: 'router.local' })).toBeInTheDocument();
  });

  it('renders device type', () => {
    render(<DeviceDetail {...defaultProps} />);

    expect(screen.getByText('router')).toBeInTheDocument();
  });

  it('renders online status badge for online device', () => {
    render(<DeviceDetail {...defaultProps} />);

    expect(screen.getByText('Online')).toBeInTheDocument();
  });

  it('renders offline status badge for offline device', () => {
    const offlineDevice = { ...mockDevice, is_up: false };
    render(<DeviceDetail {...defaultProps} device={offlineDevice} />);

    expect(screen.getByText('Offline')).toBeInTheDocument();
  });

  it('renders vulnerability count badge', () => {
    render(<DeviceDetail {...defaultProps} />);

    expect(screen.getByText('2 vulnerabilities')).toBeInTheDocument();
  });

  it('renders device IP address', () => {
    render(<DeviceDetail {...defaultProps} />);

    expect(screen.getByText('192.168.1.1')).toBeInTheDocument();
  });

  it('renders device MAC address', () => {
    render(<DeviceDetail {...defaultProps} />);

    expect(screen.getByText('00:1A:2B:3C:4D:5E')).toBeInTheDocument();
  });

  it('renders device vendor', () => {
    render(<DeviceDetail {...defaultProps} />);

    expect(screen.getByText('Linksys')).toBeInTheDocument();
  });

  it('renders operating system with confidence', () => {
    render(<DeviceDetail {...defaultProps} />);

    expect(screen.getByText(/Linux/)).toBeInTheDocument();
    expect(screen.getByText(/95% confidence/)).toBeInTheDocument();
  });

  it('renders open ports', () => {
    render(<DeviceDetail {...defaultProps} />);

    expect(screen.getByText('Open Ports (2)')).toBeInTheDocument();
    expect(screen.getByText('80')).toBeInTheDocument();
    expect(screen.getByText('443')).toBeInTheDocument();
  });

  it('renders loading state while fetching vulnerabilities', () => {
    (useVulnerabilityList as ReturnType<typeof vi.fn>).mockReturnValue({
      vulnerabilities: [],
      isLoading: true,
      error: null,
    });

    render(<DeviceDetail {...defaultProps} />);

    expect(screen.getByText('Loading vulnerabilities...')).toBeInTheDocument();
  });

  it('renders error state when vulnerability fetch fails', () => {
    (useVulnerabilityList as ReturnType<typeof vi.fn>).mockReturnValue({
      vulnerabilities: [],
      isLoading: false,
      error: { detail: 'Failed to fetch' },
    });

    render(<DeviceDetail {...defaultProps} />);

    expect(screen.getByText('Failed to load vulnerabilities')).toBeInTheDocument();
  });

  it('renders vulnerability list when loaded', () => {
    (useVulnerabilityList as ReturnType<typeof vi.fn>).mockReturnValue({
      vulnerabilities: mockVulnerabilities,
      isLoading: false,
      error: null,
    });

    render(<DeviceDetail {...defaultProps} />);

    expect(screen.getByText('Default Credentials Detected')).toBeInTheDocument();
    expect(screen.getByText('Telnet Service Exposed')).toBeInTheDocument();
  });

  it('shows "Fixed" badge for fixed vulnerabilities', () => {
    (useVulnerabilityList as ReturnType<typeof vi.fn>).mockReturnValue({
      vulnerabilities: mockVulnerabilities,
      isLoading: false,
      error: null,
    });

    render(<DeviceDetail {...defaultProps} />);

    expect(screen.getByText('Fixed')).toBeInTheDocument();
  });

  it('renders no vulnerabilities message when list is empty', () => {
    (useVulnerabilityList as ReturnType<typeof vi.fn>).mockReturnValue({
      vulnerabilities: [],
      isLoading: false,
      error: null,
    });

    render(<DeviceDetail {...defaultProps} />);

    expect(screen.getByText('No vulnerabilities detected on this device.')).toBeInTheDocument();
  });

  it('calls onVulnerabilitySelect when vulnerability is clicked', () => {
    (useVulnerabilityList as ReturnType<typeof vi.fn>).mockReturnValue({
      vulnerabilities: mockVulnerabilities,
      isLoading: false,
      error: null,
    });

    render(<DeviceDetail {...defaultProps} />);

    fireEvent.click(screen.getByText('Default Credentials Detected'));

    expect(defaultProps.onVulnerabilitySelect).toHaveBeenCalledWith(mockVulnerabilities[0]);
  });

  it('calls onClose when close button is clicked', () => {
    render(<DeviceDetail {...defaultProps} />);

    // Click the Close button in the footer (not the modal's X button)
    fireEvent.click(screen.getByRole('button', { name: /^Close$/i }));

    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('displays device icon based on type', () => {
    render(<DeviceDetail {...defaultProps} />);

    // Router icon
    expect(screen.getByText('🌐')).toBeInTheDocument();
  });
});
