/**
 * Vulnerability management hooks.
 *
 * Provides React hooks for vulnerability operations including:
 * - Listing and filtering vulnerabilities
 * - Getting vulnerability details
 * - Updating and fixing vulnerabilities
 * - Getting summary statistics
 */

import { useState, useCallback, useMemo } from 'react';
import { vulnerabilityService, type VulnerabilityListOptions } from '@/services';
import type {
  Vulnerability,
  VulnerabilityUpdate,
  VulnerabilityMarkFixed,
  VulnerabilitySummary,
  VulnerabilityFilters,
  SeverityLevel,
} from '@/types';
import { logger } from '@/services';
import { useAsyncEffect } from './useAsync';

const log = logger.create('useVulnerabilities');

/**
 * Hook for listing vulnerabilities with pagination and filtering.
 *
 * @param options - Filter and pagination options
 * @returns Vulnerability list state and controls
 *
 * @example
 * ```tsx
 * function VulnerabilityList() {
 *   const {
 *     vulnerabilities,
 *     isLoading,
 *     total,
 *     setFilters,
 *   } = useVulnerabilityList({ severity: 'critical' });
 *
 *   return (
 *     <div>
 *       {vulnerabilities.map(v => (
 *         <VulnerabilityCard key={v.id} vulnerability={v} />
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useVulnerabilityList(initialOptions?: VulnerabilityListOptions) {
  const [options, setOptions] = useState<VulnerabilityListOptions>({
    page: 1,
    page_size: 20,
    ...initialOptions,
  });

  const { data, isLoading, error, refetch, isInitialized } = useAsyncEffect(
    () => vulnerabilityService.list(options),
    [
      options.page,
      options.page_size,
      options.device_id,
      options.severity,
      options.vuln_type,
      options.is_fixed,
      options.search,
    ]
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
  const setFilters = useCallback((filters: VulnerabilityFilters) => {
    setOptions((prev) => ({ ...prev, ...filters, page: 1 }));
  }, []);

  /**
   * Set severity filter.
   */
  const setSeverity = useCallback((severity?: SeverityLevel) => {
    setOptions((prev) => ({ ...prev, severity, page: 1 }));
  }, []);

  /**
   * Set fixed status filter.
   */
  const setFixedFilter = useCallback((is_fixed?: boolean) => {
    setOptions((prev) => ({ ...prev, is_fixed, page: 1 }));
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
    /** Vulnerability list */
    vulnerabilities: data?.items ?? [],
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
    /** Set severity filter */
    setSeverity,
    /** Set fixed filter */
    setFixedFilter,
    /** Clear filters */
    clearFilters,
    /** Refetch data */
    refetch,
  };
}

/**
 * Hook for getting a single vulnerability by ID.
 *
 * @param vulnId - Vulnerability ID to fetch
 * @returns Vulnerability state
 */
export function useVulnerability(vulnId: string | null) {
  const { data, isLoading, error, refetch } = useAsyncEffect(
    () =>
      vulnId
        ? vulnerabilityService.get(vulnId)
        : Promise.resolve({ success: true, data: null as unknown as Vulnerability }),
    [vulnId]
  );

  return {
    vulnerability: data,
    isLoading,
    error,
    refetch,
  };
}

/**
 * Hook for vulnerability summary statistics.
 *
 * @returns Summary statistics state
 */
export function useVulnerabilitySummary() {
  const { data, isLoading, error, refetch } = useAsyncEffect<VulnerabilitySummary>(
    () => vulnerabilityService.getSummary(),
    []
  );

  return {
    summary: data,
    isLoading,
    error,
    refetch,
  };
}

/**
 * Hook for updating a vulnerability.
 *
 * @returns Update function and state
 */
export function useVulnerabilityUpdate() {
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateVulnerability = useCallback(
    async (vulnId: string, update: VulnerabilityUpdate): Promise<Vulnerability | null> => {
      setIsUpdating(true);
      setError(null);

      log.info('Updating vulnerability', { vulnId, update });

      const result = await vulnerabilityService.update(vulnId, update);

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
    updateVulnerability,
    isUpdating,
    error,
  };
}

/**
 * Hook for marking vulnerabilities as fixed.
 *
 * @returns Mark fixed function and state
 */
export function useMarkVulnerabilityFixed() {
  const [isMarking, setIsMarking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const markFixed = useCallback(
    async (vulnId: string, status: VulnerabilityMarkFixed): Promise<Vulnerability | null> => {
      setIsMarking(true);
      setError(null);

      log.info('Marking vulnerability fixed', { vulnId, ...status });

      const result = await vulnerabilityService.markFixed(vulnId, status);

      setIsMarking(false);

      if (!result.success) {
        setError(result.error.detail);
        return null;
      }

      return result.data;
    },
    []
  );

  return {
    markFixed,
    isMarking,
    error,
  };
}

/**
 * Hook for vulnerability types list.
 *
 * @returns Vulnerability types state
 */
export function useVulnerabilityTypes() {
  const { data, isLoading, error } = useAsyncEffect<string[]>(
    () => vulnerabilityService.getTypes(),
    []
  );

  return {
    types: data ?? [],
    isLoading,
    error,
  };
}

/**
 * Hook for computing vulnerability statistics from a list.
 *
 * @param vulnerabilities - List of vulnerabilities
 * @returns Computed statistics
 */
export function useVulnerabilityStats(vulnerabilities: Vulnerability[]) {
  return useMemo(() => {
    const stats = {
      total: vulnerabilities.length,
      fixed: 0,
      unfixed: 0,
      bySeverity: {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0,
        info: 0,
      } as Record<SeverityLevel, number>,
      byType: {} as Record<string, number>,
    };

    for (const vuln of vulnerabilities) {
      // Fixed/unfixed
      if (vuln.is_fixed) {
        stats.fixed++;
      } else {
        stats.unfixed++;
      }

      // By severity
      stats.bySeverity[vuln.severity]++;

      // By type
      stats.byType[vuln.vuln_type] = (stats.byType[vuln.vuln_type] || 0) + 1;
    }

    return stats;
  }, [vulnerabilities]);
}

/**
 * Hook for grouping vulnerabilities by severity.
 *
 * @param vulnerabilities - List of vulnerabilities
 * @returns Grouped vulnerabilities
 */
export function useVulnerabilitiesBySeverity(vulnerabilities: Vulnerability[]) {
  return useMemo(() => {
    const grouped: Record<SeverityLevel, Vulnerability[]> = {
      critical: [],
      high: [],
      medium: [],
      low: [],
      info: [],
    };

    for (const vuln of vulnerabilities) {
      grouped[vuln.severity].push(vuln);
    }

    return grouped;
  }, [vulnerabilities]);
}

/**
 * Hook for getting critical vulnerabilities that need attention.
 *
 * @param options - Pagination options
 * @returns Critical vulnerabilities state
 */
export function useCriticalVulnerabilities(options?: { page_size?: number }) {
  const { data, isLoading, error, refetch } = useAsyncEffect(
    () =>
      vulnerabilityService.getBySeverity('critical', {
        is_fixed: false,
        ...options,
      }),
    [options?.page_size]
  );

  return {
    vulnerabilities: data?.items ?? [],
    total: data?.total ?? 0,
    isLoading,
    error,
    refetch,
  };
}
