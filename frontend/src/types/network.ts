/**
 * Network scanning types.
 *
 * These types define the data structures for network scanning operations,
 * including scan requests, responses, and status tracking.
 */

/**
 * Type of scan to perform on the network.
 */
export type ScanType = 'quick' | 'deep' | 'vulnerability';

/**
 * Current status of a scan operation.
 */
export type ScanStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled';

/**
 * Request payload for starting a new network scan.
 */
export interface ScanRequest {
  /** IP address or CIDR range to scan (e.g., '192.168.1.0/24') */
  target: string;
  /** Type of scan to perform */
  scan_type: ScanType;
  /** Custom port range (e.g., '22,80,443' or '1-1000') */
  port_range?: string;
  /** User confirmation of network ownership */
  user_consent: boolean;
}

/**
 * Port information discovered during a scan.
 */
export interface Port {
  /** Port number (1-65535) */
  port: number;
  /** Transport protocol (tcp/udp) */
  protocol: string;
  /** Port state (open, closed, filtered) */
  state: string;
  /** Detected service name (e.g., 'http', 'ssh') */
  service?: string;
  /** Service version information */
  version?: string;
  /** Service banner if available */
  banner?: string;
}

/**
 * Device discovered during a network scan.
 * This is a simplified version used in scan results.
 */
export interface ScannedDevice {
  /** IP address */
  ip: string;
  /** MAC address */
  mac?: string;
  /** Resolved hostname */
  hostname?: string;
  /** Device manufacturer */
  vendor?: string;
  /** Detected operating system */
  os?: string;
  /** OS detection confidence (0-100) */
  os_accuracy: number;
  /** Device category (router, computer, phone, etc.) */
  device_type?: string;
  /** Open ports discovered */
  open_ports: Port[];
  /** When device was last seen */
  last_seen: string;
  /** Whether device is currently responding */
  is_up: boolean;
}

/**
 * Complete scan response with results.
 */
export interface ScanResponse {
  /** Unique identifier for this scan */
  scan_id: string;
  /** Network range that was scanned */
  target_range: string;
  /** Type of scan performed */
  scan_type: string;
  /** Current scan status */
  status: ScanStatus;
  /** Discovered devices */
  devices: ScannedDevice[];
  /** Scan start time (ISO 8601) */
  started_at?: string;
  /** Scan completion time (ISO 8601) */
  completed_at?: string;
  /** Error message if scan failed */
  error_message?: string;
  /** Scan progress (0-100) */
  progress: number;
  /** Number of hosts scanned so far */
  scanned_hosts: number;
  /** Total hosts to scan */
  total_hosts: number;
  /** Number of devices found */
  device_count: number;
}

/**
 * Lightweight scan status response for polling.
 */
export interface ScanStatusResponse {
  /** Scan identifier */
  scan_id: string;
  /** Current status */
  status: ScanStatus;
  /** Progress percentage (0-100) */
  progress: number;
  /** Devices found so far */
  device_count: number;
  /** Error message if failed */
  error_message?: string;
}

/**
 * Network interface information from the host system.
 */
export interface NetworkInterface {
  /** Interface name (e.g., 'eth0', 'wlan0') */
  name: string;
  /** IP address assigned to the interface */
  ip: string;
  /** Network mask */
  netmask: string;
  /** Network range in CIDR notation */
  network: string;
  /** Whether this is a private network */
  is_private: boolean;
}

/**
 * Request for validating a network target.
 */
export interface NetworkValidationRequest {
  /** IP or network range to validate */
  target: string;
}

/**
 * Response from network target validation.
 */
export interface NetworkValidationResponse {
  /** Whether the target is valid for scanning */
  valid: boolean;
  /** The validated/normalized target */
  target: string;
  /** Whether it's a private network */
  is_private: boolean;
  /** Number of hosts in the range */
  num_hosts: number;
  /** Type: 'single_ip' or 'network' */
  type: 'single_ip' | 'network' | 'unknown';
  /** Validation error message if invalid */
  error?: string;
}
