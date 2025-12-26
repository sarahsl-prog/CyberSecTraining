/**
 * LLM service client.
 *
 * Provides functions for interacting with the LLM explanation API.
 */

import { apiClient } from './api-client';
import { logger } from './logger';
import type {
  ApiResult,
  ExplanationRequest,
  ExplanationResponse,
  DifficultyLevel,
  LLMHealthStatus,
} from '@/types';

const log = logger.create('LLMService');

/**
 * Get the "use local AI" preference from localStorage.
 */
function getPreferLocalAI(): boolean {
  const saved = localStorage.getItem('cybersec-use-local-ai');
  // Default to true if not set
  return saved === null || saved === 'true';
}

/**
 * Get an explanation for a topic.
 *
 * @param request - The explanation request
 * @param skipCache - Whether to skip cache lookup
 * @returns The generated explanation wrapped in ApiResult
 */
export async function getExplanation(
  request: ExplanationRequest,
  skipCache = false
): Promise<ApiResult<ExplanationResponse>> {
  log.debug('Requesting explanation', { topic: request.topic, type: request.explanation_type });

  const preferLocal = getPreferLocalAI();
  const response = await apiClient.post<ExplanationResponse>(
    `/llm/explain?skip_cache=${skipCache}&prefer_local=${preferLocal}`,
    request
  );

  if (response.success) {
    log.info('Explanation received', {
      topic: response.data.topic,
      provider: response.data.provider,
      cached: response.data.cached,
    });
  }

  return response;
}

/**
 * Get a vulnerability explanation using the shortcut endpoint.
 *
 * @param vulnType - The vulnerability type
 * @param difficulty - The difficulty level
 * @param context - Optional additional context
 * @returns The generated explanation wrapped in ApiResult
 */
export async function explainVulnerability(
  vulnType: string,
  difficulty: DifficultyLevel = 'beginner',
  context?: string
): Promise<ApiResult<ExplanationResponse>> {
  log.debug('Requesting vulnerability explanation', { vulnType, difficulty });

  const preferLocal = getPreferLocalAI();
  const params = new URLSearchParams({ difficulty, prefer_local: String(preferLocal) });
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
 * @returns The remediation explanation wrapped in ApiResult
 */
export async function explainRemediation(
  vulnType: string,
  difficulty: DifficultyLevel = 'beginner',
  context?: string
): Promise<ApiResult<ExplanationResponse>> {
  log.debug('Requesting remediation explanation', { vulnType, difficulty });

  const preferLocal = getPreferLocalAI();
  const params = new URLSearchParams({ difficulty, prefer_local: String(preferLocal) });
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
 * @returns The concept explanation wrapped in ApiResult
 */
export async function explainConcept(
  concept: string,
  difficulty: DifficultyLevel = 'beginner'
): Promise<ApiResult<ExplanationResponse>> {
  log.debug('Requesting concept explanation', { concept, difficulty });

  const preferLocal = getPreferLocalAI();
  const params = new URLSearchParams({ difficulty, prefer_local: String(preferLocal) });

  return apiClient.get<ExplanationResponse>(
    `/llm/explain/concept/${encodeURIComponent(concept)}?${params}`
  );
}

/**
 * Check the health status of LLM providers.
 *
 * @returns The health status wrapped in ApiResult
 */
export async function getLLMHealth(): Promise<ApiResult<LLMHealthStatus>> {
  return apiClient.get<LLMHealthStatus>('/llm/health');
}

/**
 * Get cache statistics.
 *
 * @returns Cache statistics wrapped in ApiResult
 */
export async function getCacheStats(): Promise<ApiResult<{
  hits: number;
  misses: number;
  size: number;
  hit_rate: number;
  evictions: number;
}>> {
  return apiClient.get('/llm/cache/stats');
}

/**
 * Clear the explanation cache.
 *
 * @returns Clear result with count of entries cleared wrapped in ApiResult
 */
export async function clearCache(): Promise<ApiResult<{
  message: string;
  entries_cleared: number;
}>> {
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
