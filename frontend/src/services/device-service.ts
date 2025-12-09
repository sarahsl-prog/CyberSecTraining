/**
 * Device management service.
 *
 * Provides methods for device CRUD operations including:
 * - Listing and filtering devices
 * - Getting device details
 * - Updating device information
 * - Deleting devices
 * - Getting device vulnerabilities
 */

import type {
  Device,
  DeviceUpdate,
  DeviceListResponse,
  DeviceFilters,
  Vulnerability,
} from '@/types';
import type { ApiResult, PaginationParams } from '@/types';
import { apiClient, type RequestConfig } from './api-client';
import { logger } from './logger';

const log = logger.create('DeviceService');

/**
 * Combined device list options.
 */
export interface DeviceListOptions extends DeviceFilters, PaginationParams {}

/**
 * Device management service.
 *
 * Provides all device-related API operations.
 */
export const deviceService = {
  /**
   * List devices with pagination and filtering.
   *
   * @param options - Filter and pagination options
   * @param config - Optional request configuration
   * @returns Paginated device list
   *
   * @example
   * ```ts
   * const result = await deviceService.list({
   *   scan_id: 'abc123',
   *   has_vulnerabilities: true,
   *   page: 1,
   *   page_size: 20,
   * });
   * ```
   */
  async list(
    options?: DeviceListOptions,
    config?: RequestConfig
  ): Promise<ApiResult<DeviceListResponse>> {
    log.debug('Listing devices', options);
    return apiClient.get<DeviceListResponse>('/devices', {
      ...config,
      params: options as Record<string, string | number | boolean | undefined>,
    });
  },

  /**
   * Get a single device by ID.
   *
   * @param deviceId - The device identifier
   * @param config - Optional request configuration
   * @returns Device details
   */
  async get(
    deviceId: string,
    config?: RequestConfig
  ): Promise<ApiResult<Device>> {
    log.debug('Fetching device', { deviceId });
    return apiClient.get<Device>(`/devices/${deviceId}`, config);
  },

  /**
   * Update device information.
   *
   * Only the provided fields will be updated.
   *
   * @param deviceId - The device identifier
   * @param update - Fields to update
   * @param config - Optional request configuration
   * @returns Updated device
   */
  async update(
    deviceId: string,
    update: DeviceUpdate,
    config?: RequestConfig
  ): Promise<ApiResult<Device>> {
    log.info('Updating device', { deviceId, update });
    return apiClient.put<Device>(`/devices/${deviceId}`, update, config);
  },

  /**
   * Delete a device.
   *
   * This will also delete all associated vulnerabilities.
   *
   * @param deviceId - The device identifier
   * @param config - Optional request configuration
   * @returns Success message
   */
  async delete(
    deviceId: string,
    config?: RequestConfig
  ): Promise<ApiResult<{ message: string }>> {
    log.info('Deleting device', { deviceId });
    return apiClient.delete<{ message: string }>(`/devices/${deviceId}`, config);
  },

  /**
   * Get vulnerabilities for a specific device.
   *
   * @param deviceId - The device identifier
   * @param options - Pagination options
   * @param config - Optional request configuration
   * @returns List of device vulnerabilities
   */
  async getVulnerabilities(
    deviceId: string,
    options?: PaginationParams,
    config?: RequestConfig
  ): Promise<ApiResult<Vulnerability[]>> {
    log.debug('Fetching device vulnerabilities', { deviceId });
    return apiClient.get<Vulnerability[]>(`/devices/${deviceId}/vulnerabilities`, {
      ...config,
      params: options as Record<string, string | number | boolean | undefined>,
    });
  },

  /**
   * Get all devices from a specific scan.
   *
   * Convenience method for filtering by scan ID.
   *
   * @param scanId - The scan identifier
   * @param options - Additional filter options
   * @param config - Optional request configuration
   * @returns Paginated device list
   */
  async getByScan(
    scanId: string,
    options?: Omit<DeviceListOptions, 'scan_id'>,
    config?: RequestConfig
  ): Promise<ApiResult<DeviceListResponse>> {
    return this.list({ ...options, scan_id: scanId }, config);
  },

  /**
   * Get devices with vulnerabilities.
   *
   * Convenience method for finding devices that have security issues.
   *
   * @param options - Additional filter options
   * @param config - Optional request configuration
   * @returns Paginated device list
   */
  async getVulnerable(
    options?: Omit<DeviceListOptions, 'has_vulnerabilities'>,
    config?: RequestConfig
  ): Promise<ApiResult<DeviceListResponse>> {
    return this.list({ ...options, has_vulnerabilities: true }, config);
  },

  /**
   * Count devices matching filters.
   *
   * Uses pagination metadata to get total count without fetching all data.
   *
   * @param filters - Filter options
   * @param config - Optional request configuration
   * @returns Total count
   */
  async count(
    filters?: DeviceFilters,
    config?: RequestConfig
  ): Promise<ApiResult<number>> {
    const result = await this.list(
      { ...filters, page: 1, page_size: 1 },
      config
    );

    if (!result.success) {
      return result;
    }

    return { success: true, data: result.data.total };
  },
};
