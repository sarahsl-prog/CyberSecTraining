/**
 * Device management hooks.
 *
 * Provides React hooks for device operations including:
 * - Listing and filtering devices
 * - Getting device details
 * - Updating devices
 * - Managing device selection
 */

import { useState, useCallback, useMemo } from 'react';
import { deviceService, type DeviceListOptions } from '@/services';
import type { Device, DeviceUpdate, DeviceFilters } from '@/types';
import { logger } from '@/services';
import { useAsync, useAsyncEffect } from './useAsync';

const log = logger.create('useDevices');

/**
 * Hook for listing devices with pagination and filtering.
 *
 * @param options - Filter and pagination options
 * @returns Device list state and pagination controls
 *
 * @example
 * ```tsx
 * function DeviceList() {
 *   const {
 *     devices,
 *     isLoading,
 *     total,
 *     page,
 *     setPage,
 *     setFilters,
 *   } = useDeviceList({ page_size: 20 });
 *
 *   return (
 *     <div>
 *       {devices.map(d => <DeviceCard key={d.id} device={d} />)}
 *       <Pagination page={page} total={total} onPageChange={setPage} />
 *     </div>
 *   );
 * }
 * ```
 */
export function useDeviceList(initialOptions?: DeviceListOptions) {
  const [options, setOptions] = useState<DeviceListOptions>({
    page: 1,
    page_size: 20,
    ...initialOptions,
  });

  const { data, isLoading, error, refetch, isInitialized } = useAsyncEffect(
    () => deviceService.list(options),
    [options.page, options.page_size, options.scan_id, options.device_type,
     options.os, options.vendor, options.has_vulnerabilities, options.is_up]
  );

  /**
   * Update pagination.
   */
  const setPage = useCallback((page: number) => {
    setOptions((prev) => ({ ...prev, page }));
  }, []);

  /**
   * Update page size.
   */
  const setPageSize = useCallback((page_size: number) => {
    setOptions((prev) => ({ ...prev, page_size, page: 1 }));
  }, []);

  /**
   * Update filters.
   */
  const setFilters = useCallback((filters: DeviceFilters) => {
    setOptions((prev) => ({ ...prev, ...filters, page: 1 }));
  }, []);

  /**
   * Clear all filters.
   */
  const clearFilters = useCallback(() => {
    setOptions((prev) => ({
      page: 1,
      page_size: prev.page_size,
    }));
  }, []);

  return {
    /** Device list */
    devices: data?.items ?? [],
    /** Total count */
    total: data?.total ?? 0,
    /** Total pages */
    pages: data?.pages ?? 0,
    /** Current page */
    page: options.page ?? 1,
    /** Page size */
    pageSize: options.page_size ?? 20,
    /** Loading state */
    isLoading,
    /** Error state */
    error,
    /** Whether data has been fetched */
    isInitialized,
    /** Current filters */
    filters: options,
    /** Update page */
    setPage,
    /** Update page size */
    setPageSize,
    /** Update filters */
    setFilters,
    /** Clear filters */
    clearFilters,
    /** Refetch data */
    refetch,
  };
}

/**
 * Hook for getting a single device by ID.
 *
 * @param deviceId - Device ID to fetch
 * @returns Device state
 */
export function useDevice(deviceId: string | null) {
  const { data, isLoading, error, refetch } = useAsyncEffect(
    () => deviceId ? deviceService.get(deviceId) : Promise.resolve({ success: true, data: null as unknown as Device }),
    [deviceId]
  );

  return {
    device: data,
    isLoading,
    error,
    refetch,
  };
}

/**
 * Hook for updating a device.
 *
 * @returns Update function and state
 */
export function useDeviceUpdate() {
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateDevice = useCallback(
    async (deviceId: string, update: DeviceUpdate): Promise<Device | null> => {
      setIsUpdating(true);
      setError(null);

      log.info('Updating device', { deviceId, update });

      const result = await deviceService.update(deviceId, update);

      setIsUpdating(false);

      if (!result.success) {
        setError(result.error.detail);
        return null;
      }

      return result.data;
    },
    []
  );

  return {
    updateDevice,
    isUpdating,
    error,
  };
}

/**
 * Hook for deleting a device.
 *
 * @returns Delete function and state
 */
export function useDeviceDelete() {
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const deleteDevice = useCallback(async (deviceId: string): Promise<boolean> => {
    setIsDeleting(true);
    setError(null);

    log.info('Deleting device', { deviceId });

    const result = await deviceService.delete(deviceId);

    setIsDeleting(false);

    if (!result.success) {
      setError(result.error.detail);
      return false;
    }

    return true;
  }, []);

  return {
    deleteDevice,
    isDeleting,
    error,
  };
}

/**
 * Hook for device selection management.
 *
 * Useful for batch operations on multiple devices.
 *
 * @param devices - List of all devices
 * @returns Selection state and controls
 */
export function useDeviceSelection(devices: Device[]) {
  const [selected, setSelected] = useState<Set<string>>(new Set());

  /**
   * Toggle selection of a single device.
   */
  const toggle = useCallback((deviceId: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(deviceId)) {
        next.delete(deviceId);
      } else {
        next.add(deviceId);
      }
      return next;
    });
  }, []);

  /**
   * Select all devices.
   */
  const selectAll = useCallback(() => {
    setSelected(new Set(devices.map((d) => d.id)));
  }, [devices]);

  /**
   * Clear selection.
   */
  const clearSelection = useCallback(() => {
    setSelected(new Set());
  }, []);

  /**
   * Check if a device is selected.
   */
  const isSelected = useCallback(
    (deviceId: string) => selected.has(deviceId),
    [selected]
  );

  /**
   * Get selected device objects.
   */
  const selectedDevices = useMemo(
    () => devices.filter((d) => selected.has(d.id)),
    [devices, selected]
  );

  return {
    /** Set of selected device IDs */
    selected,
    /** Array of selected device objects */
    selectedDevices,
    /** Number of selected devices */
    selectedCount: selected.size,
    /** Whether all devices are selected */
    isAllSelected: selected.size === devices.length && devices.length > 0,
    /** Toggle device selection */
    toggle,
    /** Select all devices */
    selectAll,
    /** Clear selection */
    clearSelection,
    /** Check if device is selected */
    isSelected,
  };
}

/**
 * Hook for device statistics.
 *
 * Computes aggregated statistics from device list.
 *
 * @param devices - List of devices
 * @returns Device statistics
 */
export function useDeviceStats(devices: Device[]) {
  return useMemo(() => {
    const stats = {
      total: devices.length,
      online: 0,
      offline: 0,
      withVulnerabilities: 0,
      byType: {} as Record<string, number>,
      byVendor: {} as Record<string, number>,
    };

    for (const device of devices) {
      // Online/offline
      if (device.is_up) {
        stats.online++;
      } else {
        stats.offline++;
      }

      // With vulnerabilities
      if (device.vulnerability_count > 0) {
        stats.withVulnerabilities++;
      }

      // By type
      const type = device.device_type || 'unknown';
      stats.byType[type] = (stats.byType[type] || 0) + 1;

      // By vendor
      const vendor = device.vendor || 'unknown';
      stats.byVendor[vendor] = (stats.byVendor[vendor] || 0) + 1;
    }

    return stats;
  }, [devices]);
}
