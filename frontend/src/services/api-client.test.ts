/**
 * API client unit tests.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient, API_URL } from './api-client';
import { mockFetch, mockFetchError, mockNetworkError } from '@/test/mocks';

describe('ApiClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('GET requests', () => {
    it('should make GET request and return data on success', async () => {
      const mockData = { id: 1, name: 'test' };
      mockFetch(mockData);

      const result = await apiClient.get<typeof mockData>('/test');

      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(global.fetch).toHaveBeenCalledWith(
        `${API_URL}/test`,
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(result).toEqual({ success: true, data: mockData });
    });

    it('should include query parameters in URL', async () => {
      const mockData = { items: [] };
      mockFetch(mockData);

      await apiClient.get('/test', { params: { page: 1, limit: 10 } });

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_URL}/test?page=1&limit=10`,
        expect.any(Object)
      );
    });

    it('should exclude undefined params', async () => {
      mockFetch({});

      await apiClient.get('/test', {
        params: { page: 1, filter: undefined },
      });

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_URL}/test?page=1`,
        expect.any(Object)
      );
    });

    it('should return error on HTTP error response', async () => {
      mockFetchError('Not found', 404);

      const result = await apiClient.get('/test');

      expect(result).toEqual({
        success: false,
        error: {
          detail: 'Not found',
          status_code: 404,
        },
      });
    });

    it('should handle network errors', async () => {
      mockNetworkError();

      const result = await apiClient.get('/test');

      expect(result).toEqual({
        success: false,
        error: {
          detail: 'Network error. Please check your connection.',
          status_code: 0,
        },
      });
    });
  });

  describe('POST requests', () => {
    it('should make POST request with body', async () => {
      const mockData = { id: 1 };
      const requestBody = { name: 'test' };
      mockFetch(mockData);

      const result = await apiClient.post<typeof mockData>('/test', requestBody);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_URL}/test`,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(requestBody),
        })
      );
      expect(result).toEqual({ success: true, data: mockData });
    });

    it('should handle POST without body', async () => {
      mockFetch({ success: true });

      await apiClient.post('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_URL}/test`,
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  describe('PUT requests', () => {
    it('should make PUT request with body', async () => {
      const mockData = { id: 1, updated: true };
      const requestBody = { name: 'updated' };
      mockFetch(mockData);

      const result = await apiClient.put<typeof mockData>('/test/1', requestBody);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_URL}/test/1`,
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(requestBody),
        })
      );
      expect(result).toEqual({ success: true, data: mockData });
    });
  });

  describe('DELETE requests', () => {
    it('should make DELETE request', async () => {
      mockFetch({ message: 'Deleted' });

      const result = await apiClient.delete<{ message: string }>('/test/1');

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_URL}/test/1`,
        expect.objectContaining({
          method: 'DELETE',
        })
      );
      expect(result).toEqual({
        success: true,
        data: { message: 'Deleted' },
      });
    });
  });

  describe('Error handling', () => {
    it('should parse error response with detail', async () => {
      mockFetchError('Validation failed', 422);

      const result = await apiClient.post('/test', {});

      expect(result).toEqual({
        success: false,
        error: {
          detail: 'Validation failed',
          status_code: 422,
        },
      });
    });

    it('should handle non-JSON error responses', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: () => Promise.reject(new Error('Invalid JSON')),
      });

      const result = await apiClient.get('/test');

      expect(result).toEqual({
        success: false,
        error: {
          detail: 'HTTP 500: Internal Server Error',
          status_code: 500,
        },
      });
    });

    it('should handle 204 No Content responses', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        status: 204,
        statusText: 'No Content',
      });

      const result = await apiClient.delete('/test/1');

      expect(result).toEqual({ success: true, data: null });
    });
  });
});
