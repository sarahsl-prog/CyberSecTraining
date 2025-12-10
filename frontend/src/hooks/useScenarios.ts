/**
 * Scenario management hooks.
 *
 * Provides React hooks for scenario operations including:
 * - Listing and filtering scenarios
 * - Getting scenario details
 * - Fetching content packs and tags
 */

import { useState, useCallback } from 'react';
import {
  listScenarios,
  getScenario,
  listPacks,
  getTags,
  startScenario,
  type ScenarioListOptions,
} from '@/services/scenario-service';
import type { DifficultyLevel, ScenarioSummary, ContentPack, Scenario, ScenarioSession } from '@/types';
import { logger } from '@/services';
import { useAsyncEffect } from './useAsync';

const log = logger.create('useScenarios');

/**
 * Hook for listing scenarios with filtering.
 *
 * @param initialOptions - Initial filter options
 * @returns Scenario list state and filter controls
 *
 * @example
 * ```tsx
 * function ScenarioBrowser() {
 *   const {
 *     scenarios,
 *     isLoading,
 *     packFilter,
 *     setPackFilter,
 *   } = useScenarioList();
 *
 *   return (
 *     <div>
 *       {scenarios.map(s => <ScenarioCard key={s.id} scenario={s} />)}
 *     </div>
 *   );
 * }
 * ```
 */
export function useScenarioList(initialOptions?: ScenarioListOptions) {
  const [options, setOptions] = useState<ScenarioListOptions>({
    ...initialOptions,
  });

  const { data, isLoading, error, refetch, isInitialized } = useAsyncEffect(
    () => listScenarios(options),
    [options.packId, options.difficulty, options.tag]
  );

  /**
   * Update pack filter.
   */
  const setPackFilter = useCallback((packId?: string) => {
    log.debug('Setting pack filter', { packId });
    setOptions((prev) => ({ ...prev, packId }));
  }, []);

  /**
   * Update difficulty filter.
   */
  const setDifficultyFilter = useCallback((difficulty?: DifficultyLevel) => {
    log.debug('Setting difficulty filter', { difficulty });
    setOptions((prev) => ({ ...prev, difficulty }));
  }, []);

  /**
   * Update tag filter.
   */
  const setTagFilter = useCallback((tag?: string) => {
    log.debug('Setting tag filter', { tag });
    setOptions((prev) => ({ ...prev, tag }));
  }, []);

  /**
   * Clear all filters.
   */
  const clearFilters = useCallback(() => {
    log.debug('Clearing all filters');
    setOptions({});
  }, []);

  return {
    /** Scenario list */
    scenarios: data ?? [],
    /** Loading state */
    isLoading,
    /** Error state */
    error,
    /** Whether data has been fetched */
    isInitialized,
    /** Current pack filter */
    packFilter: options.packId,
    /** Current difficulty filter */
    difficultyFilter: options.difficulty,
    /** Current tag filter */
    tagFilter: options.tag,
    /** Update pack filter */
    setPackFilter,
    /** Update difficulty filter */
    setDifficultyFilter,
    /** Update tag filter */
    setTagFilter,
    /** Clear all filters */
    clearFilters,
    /** Refetch scenarios */
    refetch,
  };
}

/**
 * Hook for fetching content packs.
 *
 * @returns Content packs state
 */
export function useContentPacks() {
  const { data, isLoading, error, refetch } = useAsyncEffect(
    () => listPacks(),
    []
  );

  return {
    packs: data ?? [],
    isLoading,
    error,
    refetch,
  };
}

/**
 * Hook for fetching scenario tags.
 *
 * @returns Tags state
 */
export function useScenarioTags() {
  const { data, isLoading, error, refetch } = useAsyncEffect(
    () => getTags(),
    []
  );

  return {
    tags: data ?? [],
    isLoading,
    error,
    refetch,
  };
}

/**
 * Hook for getting a single scenario by ID.
 *
 * @param scenarioId - Scenario ID to fetch
 * @returns Scenario state
 */
export function useScenario(scenarioId: string | null) {
  const { data, isLoading, error, refetch } = useAsyncEffect(
    () =>
      scenarioId
        ? getScenario(scenarioId)
        : Promise.resolve({ success: true, data: null as unknown as Scenario }),
    [scenarioId]
  );

  return {
    scenario: data,
    isLoading,
    error,
    refetch,
  };
}

/**
 * Hook for starting a scenario session.
 *
 * @returns Start function and state
 */
export function useScenarioStart() {
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = useCallback(
    async (scenarioId: string): Promise<ScenarioSession | null> => {
      setIsStarting(true);
      setError(null);

      log.info('Starting scenario', { scenarioId });

      const result = await startScenario(scenarioId);

      setIsStarting(false);

      if (!result.success) {
        setError(result.error.detail);
        log.warn('Failed to start scenario', result.error);
        return null;
      }

      log.info('Scenario started successfully', { scenarioId });
      return result.data;
    },
    []
  );

  return {
    start,
    isStarting,
    error,
  };
}

/**
 * Hook that combines scenario list with packs and tags for filtering.
 *
 * Provides all data needed for a scenario browser component.
 *
 * @returns Combined scenario browser state
 */
export function useScenarioBrowser() {
  const scenarioList = useScenarioList();
  const { packs, isLoading: packsLoading } = useContentPacks();
  const { tags, isLoading: tagsLoading } = useScenarioTags();

  return {
    ...scenarioList,
    packs,
    tags,
    isFilterDataLoading: packsLoading || tagsLoading,
  };
}
