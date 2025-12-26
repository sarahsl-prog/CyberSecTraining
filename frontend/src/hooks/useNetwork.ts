/**
 * Network scanning hooks.
 *
 * Provides React hooks for network scanning operations including:
 * - Starting scans
 * - Polling scan status
 * - Managing scan state
 * - Network detection
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { networkService } from '@/services';
import type {
  ScanRequest,
  ScanResponse,
  ScanStatusResponse,
  NetworkInterface,
  NetworkValidationResponse,
  ScanStatus,
} from '@/types';
import { logger } from '@/services';
import { useAsync, useAsyncEffect } from './useAsync';

const log = logger.create('useNetwork');

/**
 * Hook for starting and managing a network scan.
 *
 * Handles the full scan lifecycle including:
 * - Starting the scan
 * - Polling for status updates
 * - Fetching final results
 *
 * @returns Scan state and control functions
 *
 * @example
 * ```tsx
 * function ScanPage() {
 *   const {
 *     scan,
 *     status,
 *     isScanning,
 *     progress,
 *     startScan,
 *     cancelScan,
 *   } = useScan();
 *
 *   const handleStart = async () => {
 *     await startScan({
 *       target: '192.168.1.0/24',
 *       scan_type: 'quick',
 *       user_consent: true,
 *     });
 *   };
 *
 *   return (
 *     <div>
 *       <button onClick={handleStart} disabled={isScanning}>
 *         {isScanning ? `Scanning... ${progress}%` : 'Start Scan'}
 *       </button>
 *       {scan?.devices.map(d => <Device key={d.ip} device={d} />)}
 *     </div>
 *   );
 * }
 * ```
 */
export function useScan() {
  // Scan state
  const [scan, setScan] = useState<ScanResponse | null>(null);
  const [status, setStatus] = useState<ScanStatusResponse | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Polling control
  const pollingRef = useRef<AbortController | null>(null);

  /**
   * Start a new network scan.
   */
  const startScan = useCallback(async (request: ScanRequest): Promise<ScanResponse | null> => {
    // Reset state
    setError(null);
    setScan(null);
    setStatus(null);
    setIsScanning(true);

    log.info('Starting scan', { target: request.target, type: request.scan_type });

    // Start the scan
    const result = await networkService.startScan(request);

    if (!result.success) {
      setError(result.error.detail);
      setIsScanning(false);
      log.error('Failed to start scan', result.error);
      return null;
    }

    setScan(result.data);
    setStatus({
      scan_id: result.data.scan_id,
      status: result.data.status as ScanStatus,
      progress: result.data.progress,
      device_count: result.data.device_count,
    });

    // Start polling for updates
    pollingRef.current = new AbortController();

    try {
      for await (const statusUpdate of networkService.pollScanStatus(
        result.data.scan_id,
        { signal: pollingRef.current.signal }
      )) {
        setStatus(statusUpdate);

        // On completion, fetch full results
        if (statusUpdate.status === 'completed') {
          const fullResult = await networkService.getScan(result.data.scan_id);
          if (fullResult.success) {
            setScan(fullResult.data);
          }
          setIsScanning(false);
          log.info('Scan completed', { deviceCount: statusUpdate.device_count });
          break;
        }

        // On failure
        if (statusUpdate.status === 'failed' || statusUpdate.status === 'cancelled') {
          const errorMsg = statusUpdate.error_message || 'Scan failed';
          setError(errorMsg);

          // Also update the scan object with error message for persistence
          setScan(prev => prev ? { ...prev, error_message: errorMsg, status: statusUpdate.status } : null);

          setIsScanning(false);
          log.error('Scan failed/cancelled', {
            status: statusUpdate.status,
            error: errorMsg,
            scanId: statusUpdate.scan_id
          });
          break;
        }
      }
    } catch (err) {
      if (err instanceof Error && err.message !== 'Request was cancelled.') {
        setError(err.message);
        setIsScanning(false);
        log.error('Polling error', err);
      }
    }

    return result.data;
  }, []);

  /**
   * Cancel the current scan.
   */
  const cancelScan = useCallback(async () => {
    if (!scan?.scan_id) return;

    log.info('Cancelling scan', { scanId: scan.scan_id });

    // Stop polling
    pollingRef.current?.abort();

    // Cancel on backend
    const result = await networkService.cancelScan(scan.scan_id);

    if (!result.success) {
      setError(result.error.detail);
      return;
    }

    setStatus((prev) => prev ? { ...prev, status: 'cancelled' } : null);
    setIsScanning(false);
  }, [scan?.scan_id]);

  /**
   * Reset scan state.
   */
  const reset = useCallback(() => {
    pollingRef.current?.abort();
    setScan(null);
    setStatus(null);
    setError(null);
    setIsScanning(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      pollingRef.current?.abort();
    };
  }, []);

  return {
    /** Full scan results */
    scan,
    /** Current scan status */
    status,
    /** Whether a scan is in progress */
    isScanning,
    /** Scan progress (0-100) */
    progress: status?.progress ?? 0,
    /** Error message if scan failed */
    error,
    /** Start a new scan */
    startScan,
    /** Cancel current scan */
    cancelScan,
    /** Reset state */
    reset,
  };
}

/**
 * Hook for fetching scan history.
 *
 * @param options - List options
 * @returns Scan list state
 */
export function useScanHistory(options?: {
  page?: number;
  page_size?: number;
  status?: string;
}) {
  return useAsyncEffect(
    () => networkService.listScans(options),
    [options?.page, options?.page_size, options?.status]
  );
}

/**
 * Hook for network interface detection.
 *
 * Fetches available network interfaces that can be scanned.
 *
 * @returns Interface list state
 */
export function useNetworkInterfaces() {
  return useAsyncEffect<NetworkInterface[]>(() => networkService.getInterfaces(), []);
}

/**
 * Hook for auto-detecting the local network.
 *
 * @returns Detected network state
 */
export function useNetworkDetect() {
  const { data, isLoading, error, refetch } = useAsyncEffect<NetworkInterface>(
    () => networkService.detectNetwork(),
    []
  );

  return {
    network: data,
    isLoading,
    error,
    refetch,
  };
}

/**
 * Hook for validating scan targets.
 *
 * @returns Validation function and state
 */
export function useNetworkValidation() {
  const [isValidating, setIsValidating] = useState(false);
  const [validation, setValidation] = useState<NetworkValidationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validate = useCallback(async (target: string): Promise<NetworkValidationResponse | null> => {
    setIsValidating(true);
    setError(null);

    const result = await networkService.validateTarget({ target });

    setIsValidating(false);

    if (!result.success) {
      setError(result.error.detail);
      setValidation(null);
      return null;
    }

    setValidation(result.data);
    return result.data;
  }, []);

  const reset = useCallback(() => {
    setValidation(null);
    setError(null);
    setIsValidating(false);
  }, []);

  return {
    /** Validate a target */
    validate,
    /** Current validation result */
    validation,
    /** Whether validation is in progress */
    isValidating,
    /** Validation error */
    error,
    /** Reset validation state */
    reset,
  };
}
