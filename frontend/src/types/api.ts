/**
 * API-related types for request/response handling.
 *
 * These types define the structure of API responses, error handling,
 * and common pagination patterns used throughout the application.
 */

/**
 * Standard paginated response wrapper.
 * Used for all list endpoints that return paginated results.
 */
export interface PaginatedResponse<T> {
  /** Array of items for the current page */
  items: T[];
  /** Total number of items across all pages */
  total: number;
  /** Current page number (1-indexed) */
  page: number;
  /** Number of items per page */
  page_size: number;
  /** Total number of pages */
  pages: number;
}

/**
 * Standard API error response structure.
 * Matches the error format returned by the FastAPI backend.
 */
export interface ApiError {
  /** Error detail message */
  detail: string;
  /** HTTP status code */
  status_code?: number;
  /** Optional field-specific errors for validation failures */
  errors?: Record<string, string[]>;
}

/**
 * Result type for API operations.
 * Provides a discriminated union for success/failure states.
 */
export type ApiResult<T> =
  | { success: true; data: T }
  | { success: false; error: ApiError };

/**
 * Request state for tracking async operations.
 */
export interface RequestState<T> {
  /** Data returned from the request */
  data: T | null;
  /** Whether the request is currently loading */
  isLoading: boolean;
  /** Error that occurred during the request */
  error: ApiError | null;
  /** Whether the request has completed at least once */
  isInitialized: boolean;
}

/**
 * Pagination parameters for list requests.
 */
export interface PaginationParams {
  /** Page number to fetch (1-indexed) */
  page?: number;
  /** Number of items per page */
  page_size?: number;
}

/**
 * Common filter options for list endpoints.
 */
export interface FilterParams {
  /** Search query string */
  search?: string;
  /** Sort field */
  sort_by?: string;
  /** Sort direction */
  sort_order?: 'asc' | 'desc';
}
