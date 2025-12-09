/**
 * Network scanning service.
 *
 * Provides methods for network scanning operations including:
 * - Starting and managing network scans
 * - Polling scan status
 * - Network interface detection
 * - Target validation
 */

import type {
  ScanRequest,
  ScanResponse,
  ScanStatusResponse,
  NetworkInterface,
  NetworkValidationRequest,
  NetworkValidationResponse,
} from '@/types';
import type { ApiResult, PaginatedResponse } from '@/types';
import { apiClient, type RequestConfig } from './api-client';
import { logger } from './logger';

const log = logger.create('NetworkService');

/**
 * Network scan list filters.
 */
export interface ScanListFilters {
  /** Filter by scan status */
  status?: string;
  /** Page number (1-indexed) */
  page?: number;
  /** Items per page */
  page_size?: number;
}

/**
 * Network scanning service.
 *
 * Provides all network-related API operations.
 */
export const networkService = {
  /**
   * Start a new network scan.
   *
   * @param request - Scan configuration
   * @param config - Optional request configuration
   * @returns Scan response with ID for tracking
   *
   * @example
   * ```ts
   * const result = await networkService.startScan({
   *   target: '192.168.1.0/24',
   *   scan_type: 'quick',
   *   user_consent: true,
   * });
   * if (result.success) {
   *   console.log('Scan started:', result.data.scan_id);
   * }
   * ```
   */
  async startScan(
    request: ScanRequest,
    config?: RequestConfig
  ): Promise<ApiResult<ScanResponse>> {
    log.info('Starting network scan', { target: request.target, type: request.scan_type });
    return apiClient.post<ScanResponse>('/network/scan', request, config);
  },

  /**
   * Get full scan results by ID.
   *
   * @param scanId - The scan identifier
   * @param config - Optional request configuration
   * @returns Complete scan response with devices
   */
  async getScan(
    scanId: string,
    config?: RequestConfig
  ): Promise<ApiResult<ScanResponse>> {
    log.debug('Fetching scan results', { scanId });
    return apiClient.get<ScanResponse>(`/network/scan/${scanId}`, config);
  },

  /**
   * Get lightweight scan status for polling.
   *
   * Use this for efficient status polling during active scans.
   *
   * @param scanId - The scan identifier
   * @param config - Optional request configuration
   * @returns Scan status with progress
   */
  async getScanStatus(
    scanId: string,
    config?: RequestConfig
  ): Promise<ApiResult<ScanStatusResponse>> {
    log.debug('Polling scan status', { scanId });
    return apiClient.get<ScanStatusResponse>(`/network/scan/${scanId}/status`, config);
  },

  /**
   * Get devices discovered in a scan.
   *
   * @param scanId - The scan identifier
   * @param config - Optional request configuration
   * @returns List of scanned devices
   */
  async getScanDevices(
    scanId: string,
    config?: RequestConfig
  ): Promise<ApiResult<ScanResponse['devices']>> {
    log.debug('Fetching scan devices', { scanId });
    return apiClient.get<ScanResponse['devices']>(`/network/scan/${scanId}/devices`, config);
  },

  /**
   * Cancel a running scan.
   *
   * @param scanId - The scan identifier
   * @param config - Optional request configuration
   * @returns Success message
   */
  async cancelScan(
    scanId: string,
    config?: RequestConfig
  ): Promise<ApiResult<{ message: string }>> {
    log.info('Cancelling scan', { scanId });
    return apiClient.post<{ message: string }>(`/network/scan/${scanId}/cancel`, undefined, config);
  },

  /**
   * List available network interfaces.
   *
   * Returns all network interfaces that can be used for scanning.
   *
   * @param config - Optional request configuration
   * @returns List of network interfaces
   */
  async getInterfaces(
    config?: RequestConfig
  ): Promise<ApiResult<NetworkInterface[]>> {
    log.debug('Fetching network interfaces');
    return apiClient.get<NetworkInterface[]>('/network/interfaces', config);
  },

  /**
   * Auto-detect the local network.
   *
   * Attempts to detect the most suitable network for scanning.
   *
   * @param config - Optional request configuration
   * @returns Detected network interface
   */
  async detectNetwork(
    config?: RequestConfig
  ): Promise<ApiResult<NetworkInterface>> {
    log.debug('Auto-detecting network');
    return apiClient.get<NetworkInterface>('/network/detect', config);
  },

  /**
   * Validate a scan target.
   *
   * Checks if a target IP or CIDR range is valid for scanning.
   *
   * @param request - Target to validate
   * @param config - Optional request configuration
   * @returns Validation result with details
   */
  async validateTarget(
    request: NetworkValidationRequest,
    config?: RequestConfig
  ): Promise<ApiResult<NetworkValidationResponse>> {
    log.debug('Validating scan target', { target: request.target });
    return apiClient.post<NetworkValidationResponse>('/network/validate', request, config);
  },

  /**
   * List all scans with pagination and filtering.
   *
   * @param filters - Optional filters
   * @param config - Optional request configuration
   * @returns Paginated list of scans
   */
  async listScans(
    filters?: ScanListFilters,
    config?: RequestConfig
  ): Promise<ApiResult<PaginatedResponse<ScanResponse>>> {
    log.debug('Listing scans', filters);
    return apiClient.get<PaginatedResponse<ScanResponse>>('/network/scans', {
      ...config,
      params: filters as Record<string, string | number | boolean | undefined>,
    });
  },

  /**
   * Poll scan status until completion.
   *
   * Utility function for polling scan status at regular intervals.
   *
   * @param scanId - The scan identifier
   * @param options - Polling options
   * @returns AsyncGenerator yielding status updates
   *
   * @example
   * ```ts
   * for await (const status of networkService.pollScanStatus(scanId)) {
   *   console.log(`Progress: ${status.progress}%`);
   *   if (status.status === 'completed' || status.status === 'failed') {
   *     break;
   *   }
   * }
   * ```
   */
  async *pollScanStatus(
    scanId: string,
    options: {
      /** Polling interval in ms (default: 2000) */
      interval?: number;
      /** Maximum polling attempts (default: 300) */
      maxAttempts?: number;
      /** AbortSignal for cancellation */
      signal?: AbortSignal;
    } = {}
  ): AsyncGenerator<ScanStatusResponse, void, unknown> {
    const { interval = 2000, maxAttempts = 300, signal } = options;
    let attempts = 0;

    log.info('Starting scan status polling', { scanId, interval, maxAttempts });

    while (attempts < maxAttempts) {
      if (signal?.aborted) {
        log.info('Polling cancelled', { scanId });
        return;
      }

      const result = await this.getScanStatus(scanId, { signal });

      if (!result.success) {
        log.error('Failed to poll scan status', result.error);
        throw new Error(result.error.detail);
      }

      yield result.data;

      // Stop polling on terminal states
      if (
        result.data.status === 'completed' ||
        result.data.status === 'failed' ||
        result.data.status === 'cancelled'
      ) {
        log.info('Polling complete', { scanId, status: result.data.status });
        return;
      }

      attempts++;
      await new Promise((resolve) => setTimeout(resolve, interval));
    }

    log.warn('Polling max attempts reached', { scanId, maxAttempts });
    throw new Error('Polling timed out');
  },
};
