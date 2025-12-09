/**
 * Test mocks and fixtures.
 *
 * Provides reusable mock data and helper functions for testing.
 */

import type {
  Device,
  Vulnerability,
  ScanResponse,
  VulnerabilitySummary,
  NetworkInterface,
  ScanStatusResponse,
} from '@/types';

/**
 * Mock device fixture.
 */
export const mockDevice: Device = {
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

/**
 * Mock device list.
 */
export const mockDevices: Device[] = [
  mockDevice,
  {
    ...mockDevice,
    id: 'device-2',
    ip: '192.168.1.100',
    hostname: 'laptop.local',
    device_type: 'computer',
    vendor: 'Dell',
    vulnerability_count: 0,
  },
  {
    ...mockDevice,
    id: 'device-3',
    ip: '192.168.1.150',
    hostname: 'phone.local',
    device_type: 'phone',
    vendor: 'Apple',
    is_up: false,
    vulnerability_count: 1,
  },
];

/**
 * Mock vulnerability fixture.
 */
export const mockVulnerability: Vulnerability = {
  id: 'vuln-1',
  device_id: 'device-1',
  vuln_type: 'default_credentials',
  severity: 'high',
  title: 'Default Credentials Detected',
  description: 'The device is using default login credentials.',
  cve_id: null,
  affected_service: 'http',
  affected_port: '80',
  remediation: 'Change the default username and password immediately.',
  is_fixed: false,
  verified_fixed: false,
  discovered_at: '2024-12-08T12:00:00Z',
  created_at: '2024-12-08T12:00:00Z',
  updated_at: '2024-12-08T12:00:00Z',
};

/**
 * Mock vulnerability list.
 */
export const mockVulnerabilities: Vulnerability[] = [
  mockVulnerability,
  {
    ...mockVulnerability,
    id: 'vuln-2',
    vuln_type: 'open_telnet',
    severity: 'critical',
    title: 'Telnet Service Exposed',
    affected_service: 'telnet',
    affected_port: '23',
  },
  {
    ...mockVulnerability,
    id: 'vuln-3',
    vuln_type: 'unencrypted_http',
    severity: 'medium',
    title: 'Unencrypted HTTP',
    is_fixed: true,
    fixed_at: '2024-12-08T14:00:00Z',
  },
];

/**
 * Mock vulnerability summary.
 */
export const mockVulnerabilitySummary: VulnerabilitySummary = {
  total: 15,
  critical: 2,
  high: 5,
  medium: 4,
  low: 3,
  info: 1,
  fixed: 3,
  unfixed: 12,
};

/**
 * Mock scan response.
 */
export const mockScanResponse: ScanResponse = {
  scan_id: 'scan-1',
  target_range: '192.168.1.0/24',
  scan_type: 'quick',
  status: 'completed',
  devices: mockDevices.map((d) => ({
    ip: d.ip,
    mac: d.mac,
    hostname: d.hostname,
    vendor: d.vendor,
    os: d.os,
    os_accuracy: d.os_accuracy,
    device_type: d.device_type,
    open_ports: d.open_ports,
    last_seen: d.last_seen || '2024-12-08T12:00:00Z',
    is_up: d.is_up,
  })),
  started_at: '2024-12-08T12:00:00Z',
  completed_at: '2024-12-08T12:02:30Z',
  progress: 100,
  scanned_hosts: 254,
  total_hosts: 254,
  device_count: 3,
};

/**
 * Mock scan status.
 */
export const mockScanStatus: ScanStatusResponse = {
  scan_id: 'scan-1',
  status: 'running',
  progress: 50,
  device_count: 1,
};

/**
 * Mock network interface.
 */
export const mockNetworkInterface: NetworkInterface = {
  name: 'eth0',
  ip: '192.168.1.100',
  netmask: '255.255.255.0',
  network: '192.168.1.0/24',
  is_private: true,
};

/**
 * Create a mock fetch response.
 */
export function createMockResponse<T>(data: T, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    json: () => Promise.resolve(data),
    headers: new Headers(),
    redirected: false,
    type: 'basic',
    url: '',
    clone: () => createMockResponse(data, status),
    body: null,
    bodyUsed: false,
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
    blob: () => Promise.resolve(new Blob()),
    formData: () => Promise.resolve(new FormData()),
    text: () => Promise.resolve(JSON.stringify(data)),
  } as Response;
}

/**
 * Setup fetch mock with response.
 */
export function mockFetch<T>(data: T, status = 200): void {
  (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
    createMockResponse(data, status)
  );
}

/**
 * Setup fetch mock with error.
 */
export function mockFetchError(message: string, status = 500): void {
  (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
    createMockResponse({ detail: message }, status)
  );
}

/**
 * Setup fetch mock with network error.
 */
export function mockNetworkError(): void {
  (global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
    new TypeError('Failed to fetch')
  );
}

// Need to import vi
import { vi } from 'vitest';
