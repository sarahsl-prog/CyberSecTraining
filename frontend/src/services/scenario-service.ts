/**
 * Service for interacting with scenario API endpoints.
 */

import { apiClient } from './api-client';
import { Scenario, ScenarioSummary } from '../types/scenario';
import type { ApiResult } from '@/types';

/**
 * Service for scenario operations.
 */
export const scenarioService = {
  /**
   * Get all available scenarios.
   */
  async getScenarios(): Promise<ApiResult<ScenarioSummary[]>> {
    return apiClient.get('/scenarios');
  },

  /**
   * Get a specific scenario by ID.
   */
  async getScenario(id: string): Promise<ApiResult<Scenario>> {
    return apiClient.get(`/scenarios/${id}`);
  },
};
