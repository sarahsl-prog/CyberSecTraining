/**
 * Device-related types.
 *
 * These types define the data structures for devices discovered
 * during network scans and stored in the database.
 */

import type { Port } from './network';
import type { PaginatedResponse } from './api';

/**
 * Complete device information from the database.
 * Extends the scan result data with database fields.
 */
export interface Device {
  /** Unique device identifier */
  id: string;
  /** ID of the scan that discovered this device */
  scan_id: string;
  /** IP address */
  ip: string;
  /** MAC address */
  mac?: string;
  /** Hostname */
  hostname?: string;
  /** Device manufacturer */
  vendor?: string;
  /** Device category */
  device_type?: string;
  /** Detected operating system */
  os?: string;
  /** OS detection confidence (0-100) */
  os_accuracy: number;
  /** Whether device is currently up */
  is_up: boolean;
  /** Last seen timestamp (ISO 8601) */
  last_seen?: string;
  /** Open ports on the device */
  open_ports: Port[];
  /** Number of vulnerabilities found */
  vulnerability_count: number;
  /** Record creation timestamp */
  created_at?: string;
  /** Last update timestamp */
  updated_at?: string;
}

/**
 * Payload for updating device information.
 */
export interface DeviceUpdate {
  /** Updated hostname */
  hostname?: string;
  /** Updated device type */
  device_type?: string;
  /** Updated operating system */
  os?: string;
}

/**
 * Paginated device list response.
 */
export type DeviceListResponse = PaginatedResponse<Device>;

/**
 * Filter options for device list queries.
 */
export interface DeviceFilters {
  /** Filter by scan ID */
  scan_id?: string;
  /** Filter by device type */
  device_type?: string;
  /** Filter by OS */
  os?: string;
  /** Filter by vendor */
  vendor?: string;
  /** Only show devices with vulnerabilities */
  has_vulnerabilities?: boolean;
  /** Only show active/up devices */
  is_up?: boolean;
}

/**
 * Common device types for categorization.
 */
export const DEVICE_TYPES = [
  'router',
  'switch',
  'access_point',
  'computer',
  'laptop',
  'server',
  'phone',
  'tablet',
  'printer',
  'camera',
  'iot',
  'storage',
  'other',
] as const;

export type DeviceType = typeof DEVICE_TYPES[number];
