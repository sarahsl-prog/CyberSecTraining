/**
 * LLM service client.
 *
 * Provides functions for interacting with the LLM explanation API.
 */

import { apiClient } from './api-client';
import { logger } from './logger';
import type {
  ExplanationRequest,
  ExplanationResponse,
  ExplanationType,
  DifficultyLevel,
  LLMHealthStatus,
} from '@/types';

const log = logger.create('LLMService');

/**
 * Get an explanation for a topic.
 *
 * @param request - The explanation request
 * @param skipCache - Whether to skip cache lookup
 * @returns The generated explanation
 */
export async function getExplanation(
  request: ExplanationRequest,
  skipCache = false
): Promise<ExplanationResponse> {
  log.debug('Requesting explanation', { topic: request.topic, type: request.explanation_type });

  const response = await apiClient.post<ExplanationResponse>(
    `/llm/explain?skip_cache=${skipCache}`,
    request
  );

  log.info('Explanation received', {
    topic: response.topic,
    provider: response.provider,
    cached: response.cached,
  });

  return response;
}

/**
 * Get a vulnerability explanation using the shortcut endpoint.
 *
 * @param vulnType - The vulnerability type
 * @param difficulty - The difficulty level
 * @param context - Optional additional context
 * @returns The generated explanation
 */
export async function explainVulnerability(
  vulnType: string,
  difficulty: DifficultyLevel = 'beginner',
  context?: string
): Promise<ExplanationResponse> {
  log.debug('Requesting vulnerability explanation', { vulnType, difficulty });

  const params = new URLSearchParams({ difficulty });
  if (context) {
    params.append('context', context);
  }

  return apiClient.get<ExplanationResponse>(
    `/llm/explain/vulnerability/${encodeURIComponent(vulnType)}?${params}`
  );
}

/**
 * Get remediation instructions using the shortcut endpoint.
 *
 * @param vulnType - The vulnerability type
 * @param difficulty - The difficulty level
 * @param context - Optional additional context
 * @returns The remediation explanation
 */
export async function explainRemediation(
  vulnType: string,
  difficulty: DifficultyLevel = 'beginner',
  context?: string
): Promise<ExplanationResponse> {
  log.debug('Requesting remediation explanation', { vulnType, difficulty });

  const params = new URLSearchParams({ difficulty });
  if (context) {
    params.append('context', context);
  }

  return apiClient.get<ExplanationResponse>(
    `/llm/explain/remediation/${encodeURIComponent(vulnType)}?${params}`
  );
}

/**
 * Get a concept explanation using the shortcut endpoint.
 *
 * @param concept - The concept to explain
 * @param difficulty - The difficulty level
 * @returns The concept explanation
 */
export async function explainConcept(
  concept: string,
  difficulty: DifficultyLevel = 'beginner'
): Promise<ExplanationResponse> {
  log.debug('Requesting concept explanation', { concept, difficulty });

  const params = new URLSearchParams({ difficulty });

  return apiClient.get<ExplanationResponse>(
    `/llm/explain/concept/${encodeURIComponent(concept)}?${params}`
  );
}

/**
 * Check the health status of LLM providers.
 *
 * @returns The health status
 */
export async function getLLMHealth(): Promise<LLMHealthStatus> {
  return apiClient.get<LLMHealthStatus>('/llm/health');
}

/**
 * Get cache statistics.
 *
 * @returns Cache statistics
 */
export async function getCacheStats(): Promise<{
  hits: number;
  misses: number;
  size: number;
  hit_rate: number;
  evictions: number;
}> {
  return apiClient.get('/llm/cache/stats');
}

/**
 * Clear the explanation cache.
 *
 * @returns Clear result with count of entries cleared
 */
export async function clearCache(): Promise<{
  message: string;
  entries_cleared: number;
}> {
  log.info('Clearing LLM cache');
  return apiClient.post('/llm/cache/clear', {});
}

/**
 * LLM service object for convenient importing.
 */
export const llmService = {
  getExplanation,
  explainVulnerability,
  explainRemediation,
  explainConcept,
  getLLMHealth,
  getCacheStats,
  clearCache,
};
