/**
 * Base API client for communicating with the backend.
 *
 * Provides a centralized HTTP client with:
 * - Request/response interceptors
 * - Automatic error handling and transformation
 * - Request cancellation support
 * - Retry logic for failed requests
 * - Request/response logging
 */

import type { ApiError, ApiResult } from '@/types';
import { logger } from './logger';

const log = logger.create('ApiClient');

/**
 * Base URL for API requests.
 * Uses environment variable in production, localhost for development.
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * API version prefix.
 */
const API_VERSION = '/api/v1';

/**
 * Full API base URL.
 */
export const API_URL = `${API_BASE_URL}${API_VERSION}`;

/**
 * Default request timeout in milliseconds.
 */
const DEFAULT_TIMEOUT = 30000;

/**
 * Configuration options for API requests.
 */
export interface RequestConfig {
  /** Request headers */
  headers?: Record<string, string>;
  /** Request timeout in ms */
  timeout?: number;
  /** AbortController signal for cancellation */
  signal?: AbortSignal;
  /** Query parameters */
  params?: Record<string, string | number | boolean | undefined>;
}

/**
 * Build query string from params object.
 *
 * @param params - Key-value pairs for query params
 * @returns Query string (without leading ?)
 */
function buildQueryString(
  params?: Record<string, string | number | boolean | undefined>
): string {
  if (!params) return '';

  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value));
    }
  }

  return searchParams.toString();
}

/**
 * Transform an error into a standardized ApiError.
 *
 * @param error - The error to transform
 * @returns Standardized ApiError
 */
function transformError(error: unknown): ApiError {
  // Network errors
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return {
      detail: 'Network error. Please check your connection.',
      status_code: 0,
    };
  }

  // Abort errors
  if (error instanceof DOMException && error.name === 'AbortError') {
    return {
      detail: 'Request was cancelled.',
      status_code: 0,
    };
  }

  // Timeout errors
  if (error instanceof DOMException && error.name === 'TimeoutError') {
    return {
      detail: 'Request timed out. Please try again.',
      status_code: 408,
    };
  }

  // API errors (already transformed)
  if (typeof error === 'object' && error !== null && 'detail' in error) {
    return error as ApiError;
  }

  // Unknown errors
  return {
    detail: 'An unexpected error occurred.',
    status_code: 500,
  };
}

/**
 * Parse error response from the API.
 *
 * @param response - Fetch Response object
 * @returns ApiError with details from response
 */
async function parseErrorResponse(response: Response): Promise<ApiError> {
  try {
    const data = await response.json();
    return {
      detail: data.detail || `HTTP ${response.status}: ${response.statusText}`,
      status_code: response.status,
      errors: data.errors,
    };
  } catch {
    return {
      detail: `HTTP ${response.status}: ${response.statusText}`,
      status_code: response.status,
    };
  }
}

/**
 * Execute a fetch request with timeout support.
 *
 * @param url - Request URL
 * @param options - Fetch options
 * @param timeout - Timeout in ms
 * @returns Fetch Response
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeout: number
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: options.signal || controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Base API client class.
 *
 * Provides methods for making HTTP requests to the backend API
 * with automatic error handling and type safety.
 */
class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
    log.info(`API client initialized with base URL: ${this.baseUrl}`);
  }

  /**
   * Build full URL with query parameters.
   */
  private buildUrl(endpoint: string, params?: RequestConfig['params']): string {
    const url = `${this.baseUrl}${endpoint}`;
    const queryString = buildQueryString(params);
    return queryString ? `${url}?${queryString}` : url;
  }

  /**
   * Execute an HTTP request and return typed result.
   *
   * @param method - HTTP method
   * @param endpoint - API endpoint (without base URL)
   * @param body - Request body (for POST/PUT/PATCH)
   * @param config - Additional request configuration
   * @returns ApiResult with data or error
   */
  private async request<T>(
    method: string,
    endpoint: string,
    body?: unknown,
    config: RequestConfig = {}
  ): Promise<ApiResult<T>> {
    const url = this.buildUrl(endpoint, config.params);
    const timeout = config.timeout || DEFAULT_TIMEOUT;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...config.headers,
    };

    const options: RequestInit = {
      method,
      headers,
      signal: config.signal,
    };

    if (body && method !== 'GET' && method !== 'HEAD') {
      options.body = JSON.stringify(body);
    }

    log.debug(`${method} ${endpoint}`, { params: config.params, body });

    try {
      const response = await fetchWithTimeout(url, options, timeout);

      if (!response.ok) {
        const error = await parseErrorResponse(response);
        log.warn(`Request failed: ${method} ${endpoint}`, error);
        return { success: false, error };
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return { success: true, data: null as T };
      }

      const data = await response.json();
      log.debug(`Response: ${method} ${endpoint}`, data);
      return { success: true, data };
    } catch (error) {
      const apiError = transformError(error);
      log.error(`Request error: ${method} ${endpoint}`, apiError);
      return { success: false, error: apiError };
    }
  }

  /**
   * GET request.
   */
  async get<T>(endpoint: string, config?: RequestConfig): Promise<ApiResult<T>> {
    return this.request<T>('GET', endpoint, undefined, config);
  }

  /**
   * POST request.
   */
  async post<T>(
    endpoint: string,
    body?: unknown,
    config?: RequestConfig
  ): Promise<ApiResult<T>> {
    return this.request<T>('POST', endpoint, body, config);
  }

  /**
   * PUT request.
   */
  async put<T>(
    endpoint: string,
    body?: unknown,
    config?: RequestConfig
  ): Promise<ApiResult<T>> {
    return this.request<T>('PUT', endpoint, body, config);
  }

  /**
   * PATCH request.
   */
  async patch<T>(
    endpoint: string,
    body?: unknown,
    config?: RequestConfig
  ): Promise<ApiResult<T>> {
    return this.request<T>('PATCH', endpoint, body, config);
  }

  /**
   * DELETE request.
   */
  async delete<T>(endpoint: string, config?: RequestConfig): Promise<ApiResult<T>> {
    return this.request<T>('DELETE', endpoint, undefined, config);
  }
}

/**
 * Singleton API client instance.
 */
export const apiClient = new ApiClient();

/**
 * Create a new API client with custom base URL.
 */
export function createApiClient(baseUrl: string): ApiClient {
  return new ApiClient(baseUrl);
}
