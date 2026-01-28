/**
 * LLM-related types.
 *
 * These types define the data structures for LLM explanations
 * and AI-powered educational content.
 */

import type { DifficultyLevel } from './scenario';

/**
 * Types of explanations available from the LLM service.
 */
export type ExplanationType =
  | 'vulnerability'
  | 'remediation'
  | 'concept'
  | 'service'
  | 'risk';

/**
 * LLM provider types.
 */
export type LLMProvider = 'ollama' | 'hosted' | 'static';

/**
 * Request for an LLM explanation.
 */
export interface ExplanationRequest {
  /** Type of explanation requested */
  explanation_type: ExplanationType;
  /** The topic to explain */
  topic: string;
  /** Additional context for better explanation */
  context?: string;
  /** Target difficulty level */
  difficulty_level: DifficultyLevel;
}

/**
 * Response containing an LLM-generated explanation.
 */
export interface ExplanationResponse {
  /** The generated explanation text */
  explanation: string;
  /** Which LLM provider generated this explanation */
  provider: LLMProvider;
  /** The topic that was explained */
  topic: string;
  /** Whether this response was served from cache */
  cached: boolean;
  /** The difficulty level of the explanation */
  difficulty_level: DifficultyLevel;
  /** Suggested related topics to explore */
  related_topics: string[];
}

/**
 * Health status of LLM providers.
 */
export interface LLMHealthStatus {
  /** Whether local Ollama instance is available */
  ollama_available: boolean;
  /** Whether hosted LLM API is available */
  hosted_available: boolean;
  /** Currently active LLM provider */
  active_provider: LLMProvider;
  /** Number of explanations in cache */
  cache_size: number;
}

/**
 * Display-friendly provider names.
 */
export const PROVIDER_NAMES: Record<LLMProvider, string> = {
  ollama: 'Local AI (Ollama)',
  hosted: 'Cloud AI',
  static: 'Knowledge Base',
};

/**
 * Display-friendly difficulty descriptions.
 */
export const DIFFICULTY_DESCRIPTIONS: Record<DifficultyLevel, string> = {
  beginner: 'Simple explanations for newcomers',
  intermediate: 'Technical details for learners',
  advanced: 'In-depth analysis for professionals',
  expert: 'Expert-level technical deep dives',
};
