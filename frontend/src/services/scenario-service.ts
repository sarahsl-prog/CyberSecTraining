/**
 * Scenario service client.
 *
 * Provides functions for interacting with the scenario API.
 * All functions return ApiResult<T> for consistent error handling.
 */

import { apiClient } from './api-client';
import { logger } from './logger';
import type {
  Scenario,
  ScenarioSummary,
  ScenarioSession,
  ContentPack,
  DifficultyLevel,
  DifficultyInfo,
  ApiResult,
} from '@/types';

const log = logger.create('ScenarioService');

/**
 * Options for listing scenarios.
 */
export interface ScenarioListOptions {
  /** Filter by content pack ID */
  packId?: string;
  /** Filter by difficulty level */
  difficulty?: DifficultyLevel;
  /** Filter by tag */
  tag?: string;
}

/**
 * List all scenarios with optional filtering.
 *
 * @param options - Filter options
 * @returns ApiResult with list of scenario summaries
 */
export async function listScenarios(
  options: ScenarioListOptions = {}
): Promise<ApiResult<ScenarioSummary[]>> {
  const { packId, difficulty, tag } = options;
  log.debug('Listing scenarios', { packId, difficulty, tag });

  const params = new URLSearchParams();
  if (packId) params.append('pack_id', packId);
  if (difficulty) params.append('difficulty', difficulty);
  if (tag) params.append('tag', tag);

  const queryString = params.toString();
  const url = queryString ? `/scenarios?${queryString}` : '/scenarios';

  return apiClient.get<ScenarioSummary[]>(url);
}

/**
 * Get a single scenario by ID.
 *
 * @param scenarioId - The scenario identifier
 * @returns ApiResult with full scenario details
 */
export async function getScenario(scenarioId: string): Promise<ApiResult<Scenario>> {
  log.debug('Getting scenario', { scenarioId });
  return apiClient.get<Scenario>(`/scenarios/${encodeURIComponent(scenarioId)}`);
}

/**
 * Start a scenario session.
 *
 * @param scenarioId - The scenario to start
 * @returns ApiResult with session data (vulnerabilities hidden)
 */
export async function startScenario(scenarioId: string): Promise<ApiResult<ScenarioSession>> {
  log.info('Starting scenario', { scenarioId });
  return apiClient.get<ScenarioSession>(
    `/scenarios/${encodeURIComponent(scenarioId)}/start`
  );
}

/**
 * List all content packs.
 *
 * @returns ApiResult with list of content packs with scenario counts
 */
export async function listPacks(): Promise<ApiResult<ContentPack[]>> {
  log.debug('Listing content packs');
  return apiClient.get<ContentPack[]>('/scenarios/packs');
}

/**
 * Get all available tags.
 *
 * @returns ApiResult with sorted list of unique tags
 */
export async function getTags(): Promise<ApiResult<string[]>> {
  log.debug('Getting scenario tags');
  return apiClient.get<string[]>('/scenarios/tags');
}

/**
 * Get difficulty level information.
 *
 * @returns ApiResult with list of difficulty levels with descriptions
 */
export async function getDifficulties(): Promise<ApiResult<DifficultyInfo[]>> {
  log.debug('Getting difficulty levels');
  return apiClient.get<DifficultyInfo[]>('/scenarios/difficulties');
}

/**
 * Reload scenarios from disk.
 *
 * @returns ApiResult with reload result and count
 */
export async function reloadScenarios(): Promise<ApiResult<{
  message: string;
  scenario_count: number;
}>> {
  log.info('Reloading scenarios');
  return apiClient.post('/scenarios/reload', {});
}

/**
 * Scenario service object for convenient importing.
 */
export const scenarioService = {
  listScenarios,
  getScenario,
  startScenario,
  listPacks,
  getTags,
  getDifficulties,
  reloadScenarios,
};
