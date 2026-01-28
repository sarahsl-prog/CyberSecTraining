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

  describe('listScenarios', () => {
    it('should fetch scenarios successfully', async () => {
      const mockScenarios = [
        {
          id: 'test-scenario',
          pack_id: 'core',
          name: 'Test Scenario',
          description: 'A test scenario',
          difficulty: 'beginner',
          device_count: 5,
          vulnerability_count: 3,
          estimated_time: 15,
          tags: ['test'],
          is_completed: false,
        },
      ];

      const mockResponse = { success: true, data: mockScenarios };
      (apiClient.get as any).mockResolvedValue(mockResponse);

      const result = await scenarioService.listScenarios();

      expect(apiClient.get).toHaveBeenCalledWith('/scenarios');
      expect(result).toEqual(mockResponse);
    });

    it('should handle API errors', async () => {
      const mockError = { success: false, error: { detail: 'API Error' } };
      (apiClient.get as any).mockResolvedValue(mockError);

      const result = await scenarioService.listScenarios();

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.detail).toBe('API Error');
      }
    });
  });

  describe('getScenario', () => {
    it('should fetch a single scenario successfully', async () => {
      const mockScenario = {
        id: 'test-scenario',
        pack_id: 'core',
        name: 'Test Scenario',
        description: 'A test scenario',
        difficulty: 'beginner',
        learning_objectives: ['Objective 1'],
        devices: [],
        metadata: {
          author: 'Test',
          version: '1.0',
          tags: [],
          prerequisites: [],
        },
        success_criteria: {},
      };

      const mockResponse = { success: true, data: mockScenario };
      (apiClient.get as any).mockResolvedValue(mockResponse);

      const result = await scenarioService.getScenario('test-scenario');

      expect(apiClient.get).toHaveBeenCalledWith('/scenarios/test-scenario');
      expect(result).toEqual(mockResponse);
    });

    it('should handle API errors', async () => {
      const mockError = { success: false, error: { detail: 'API Error' } };
      (apiClient.get as any).mockResolvedValue(mockError);

      const result = await scenarioService.getScenario('test-scenario');

      expect(result).toEqual(mockError);
    });
  });
});
