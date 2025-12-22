/**
 * Tests for scenario service.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { scenarioService } from './scenario-service';
import { apiClient } from './api-client';

// Mock the API client
vi.mock('./api-client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

describe('scenarioService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getScenarios', () => {
    it('should fetch scenarios successfully', async () => {
      const mockScenarios = [
        {
          id: 'test-scenario',
          title: 'Test Scenario',
          description: 'A test scenario',
          difficulty: 'beginner',
          estimated_time: 15,
          tags: ['test'],
        },
      ];

      const mockResponse = { success: true, data: mockScenarios };
      (apiClient.get as any).mockResolvedValue(mockResponse);

      const result = await scenarioService.getScenarios();

      expect(apiClient.get).toHaveBeenCalledWith('/scenarios');
      expect(result).toEqual(mockResponse);
    });

    it('should handle API errors', async () => {
      const mockError = { success: false, error: { message: 'API Error' } };
      (apiClient.get as any).mockResolvedValue(mockError);

      const result = await scenarioService.getScenarios();

      expect(result.success).toBe(false);
      expect(result.error.message).toBe('API Error');
    });
  });

  describe('getScenario', () => {
    it('should fetch a single scenario successfully', async () => {
      const mockScenario = {
        id: 'test-scenario',
        title: 'Test Scenario',
        description: 'A test scenario',
        difficulty: 'beginner',
        estimated_time: 15,
        steps: [],
      };

      const mockResponse = { success: true, data: mockScenario };
      (apiClient.get as any).mockResolvedValue(mockResponse);

      const result = await scenarioService.getScenario('test-scenario');

      expect(apiClient.get).toHaveBeenCalledWith('/scenarios/test-scenario');
      expect(result).toEqual(mockResponse);
    });

    it('should handle API errors', async () => {
      const mockError = { success: false, error: { message: 'API Error' } };
      (apiClient.get as any).mockResolvedValue(mockError);

      const result = await scenarioService.getScenario('test-scenario');

      expect(result).toEqual(mockError);
    });
  });
});
