/**
 * Base hook for async operations.
 *
 * Provides a reusable pattern for handling async operations
 * with loading states, error handling, and cancellation support.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import type { ApiError, RequestState, ApiResult } from '@/types';
import { logger } from '@/services';

const log = logger.create('useAsync');

/**
 * Options for async hook operations.
 */
export interface AsyncOptions {
  /** Reset data when starting a new request */
  resetOnExecute?: boolean;
  /** Callback on success */
  onSuccess?: (data: unknown) => void;
  /** Callback on error */
  onError?: (error: ApiError) => void;
}

/**
 * Return type for useAsync hook.
 */
export interface UseAsyncReturn<T> extends RequestState<T> {
  /** Execute the async operation */
  execute: (...args: unknown[]) => Promise<T | null>;
  /** Reset state to initial values */
  reset: () => void;
  /** Set data manually */
  setData: (data: T | null) => void;
}

/**
 * Generic hook for handling async operations.
 *
 * Provides a consistent pattern for managing async state including:
 * - Loading state tracking
 * - Error handling
 * - Request cancellation
 * - Data caching
 *
 * @param asyncFn - Async function to execute
 * @param options - Hook options
 * @returns State and controls for the async operation
 *
 * @example
 * ```tsx
 * function DeviceList() {
 *   const { data, isLoading, error, execute } = useAsync(
 *     () => deviceService.list(),
 *     { onError: (e) => toast.error(e.detail) }
 *   );
 *
 *   useEffect(() => { execute(); }, [execute]);
 *
 *   if (isLoading) return <Spinner />;
 *   if (error) return <Error message={error.detail} />;
 *   return <List items={data?.items} />;
 * }
 * ```
 */
export function useAsync<T>(
  asyncFn: (...args: unknown[]) => Promise<ApiResult<T>>,
  options: AsyncOptions = {}
): UseAsyncReturn<T> {
  const { resetOnExecute = true, onSuccess, onError } = options;

  // State
  const [state, setState] = useState<RequestState<T>>({
    data: null,
    isLoading: false,
    error: null,
    isInitialized: false,
  });

  // Track mounted state to prevent updates after unmount
  const isMounted = useRef(true);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
      // Cancel any pending request on unmount
      abortControllerRef.current?.abort();
    };
  }, []);

  /**
   * Execute the async operation.
   */
  const execute = useCallback(
    async (...args: unknown[]): Promise<T | null> => {
      // Cancel previous request
      abortControllerRef.current?.abort();
      abortControllerRef.current = new AbortController();

      setState((prev) => ({
        ...prev,
        isLoading: true,
        error: null,
        data: resetOnExecute ? null : prev.data,
      }));

      try {
        const result = await asyncFn(...args);

        if (!isMounted.current) return null;

        if (result.success) {
          setState({
            data: result.data,
            isLoading: false,
            error: null,
            isInitialized: true,
          });
          onSuccess?.(result.data);
          return result.data;
        } else {
          setState((prev) => ({
            ...prev,
            isLoading: false,
            error: result.error,
            isInitialized: true,
          }));
          onError?.(result.error);
          log.warn('Async operation failed', result.error);
          return null;
        }
      } catch (err) {
        if (!isMounted.current) return null;

        const error: ApiError = {
          detail: err instanceof Error ? err.message : 'Unknown error',
          status_code: 500,
        };

        setState((prev) => ({
          ...prev,
          isLoading: false,
          error,
          isInitialized: true,
        }));
        onError?.(error);
        log.error('Async operation threw', error);
        return null;
      }
    },
    [asyncFn, resetOnExecute, onSuccess, onError]
  );

  /**
   * Reset state to initial values.
   */
  const reset = useCallback(() => {
    abortControllerRef.current?.abort();
    setState({
      data: null,
      isLoading: false,
      error: null,
      isInitialized: false,
    });
  }, []);

  /**
   * Set data manually.
   */
  const setData = useCallback((data: T | null) => {
    setState((prev) => ({
      ...prev,
      data,
    }));
  }, []);

  return {
    ...state,
    execute,
    reset,
    setData,
  };
}

/**
 * Hook for immediate async execution.
 *
 * Executes the async function immediately on mount and when dependencies change.
 *
 * @param asyncFn - Async function to execute
 * @param deps - Dependency array for re-execution
 * @param options - Hook options
 * @returns State for the async operation
 */
export function useAsyncEffect<T>(
  asyncFn: () => Promise<ApiResult<T>>,
  deps: React.DependencyList = [],
  options: AsyncOptions = {}
): Omit<UseAsyncReturn<T>, 'execute'> & { refetch: () => Promise<T | null> } {
  const { execute, ...rest } = useAsync(asyncFn, options);

  useEffect(() => {
    execute();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { ...rest, refetch: execute };
}

/**
 * Hook for polling async operations.
 *
 * Polls at a specified interval until stopped or a condition is met.
 *
 * @param asyncFn - Async function to poll
 * @param interval - Polling interval in ms
 * @param options - Hook options including stop condition
 * @returns State and controls for polling
 */
export function usePolling<T>(
  asyncFn: () => Promise<ApiResult<T>>,
  interval: number,
  options: AsyncOptions & {
    /** Condition to stop polling */
    stopWhen?: (data: T | null) => boolean;
    /** Start polling immediately */
    immediate?: boolean;
  } = {}
): UseAsyncReturn<T> & { isPolling: boolean; startPolling: () => void; stopPolling: () => void } {
  const { stopWhen, immediate = false, ...asyncOptions } = options;
  const asyncState = useAsync(asyncFn, asyncOptions);
  const [isPolling, setIsPolling] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const startPolling = useCallback(() => {
    stopPolling();
    setIsPolling(true);

    // Execute immediately
    asyncState.execute();

    // Then set up interval
    intervalRef.current = setInterval(async () => {
      const result = await asyncState.execute();
      if (stopWhen?.(result)) {
        stopPolling();
      }
    }, interval);
  }, [asyncState, interval, stopPolling, stopWhen]);

  // Start immediately if configured
  useEffect(() => {
    if (immediate) {
      startPolling();
    }
    return () => {
      stopPolling();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [immediate]);

  // Check stop condition on data change
  useEffect(() => {
    if (isPolling && stopWhen?.(asyncState.data)) {
      stopPolling();
    }
  }, [asyncState.data, isPolling, stopPolling, stopWhen]);

  return {
    ...asyncState,
    isPolling,
    startPolling,
    stopPolling,
  };
}
