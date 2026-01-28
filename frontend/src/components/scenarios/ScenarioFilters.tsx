/**
 * ScenarioFilters component.
 *
 * Provides filtering controls for the scenario browser.
 */

import type { DifficultyLevel, ContentPack } from '@/types';
import { DIFFICULTY_CONFIG } from '@/types';
import styles from './ScenarioFilters.module.css';

/**
 * Props for ScenarioFilters component.
 */
export interface ScenarioFiltersProps {
  /** Available content packs */
  packs: ContentPack[];
  /** Available tags */
  tags: string[];
  /** Currently selected pack ID */
  selectedPack?: string;
  /** Currently selected difficulty */
  selectedDifficulty?: DifficultyLevel;
  /** Currently selected tag */
  selectedTag?: string;
  /** Handler for pack selection change */
  onPackChange: (packId?: string) => void;
  /** Handler for difficulty selection change */
  onDifficultyChange: (difficulty?: DifficultyLevel) => void;
  /** Handler for tag selection change */
  onTagChange: (tag?: string) => void;
  /** Handler for clearing all filters */
  onClearFilters: () => void;
}

/**
 * ScenarioFilters provides filtering controls for scenarios.
 *
 * @example
 * ```tsx
 * <ScenarioFilters
 *   packs={packs}
 *   tags={tags}
 *   selectedPack={packFilter}
 *   onPackChange={setPackFilter}
 *   ...
 * />
 * ```
 */
export function ScenarioFilters({
  packs,
  tags,
  selectedPack,
  selectedDifficulty,
  selectedTag,
  onPackChange,
  onDifficultyChange,
  onTagChange,
  onClearFilters,
}: ScenarioFiltersProps) {
  const hasFilters = selectedPack || selectedDifficulty || selectedTag;

  return (
    <div className={styles.filters} role="group" aria-label="Scenario filters">
      {/* Pack Filter */}
      <div className={styles.filterGroup}>
        <label htmlFor="pack-filter" className={styles.label}>
          Content Pack
        </label>
        <select
          id="pack-filter"
          className={styles.select}
          value={selectedPack || ''}
          onChange={(e) => onPackChange(e.target.value || undefined)}
        >
          <option value="">All Packs</option>
          {packs.map((pack) => (
            <option key={pack.id} value={pack.id}>
              {pack.name} ({pack.scenario_count})
            </option>
          ))}
        </select>
      </div>

      {/* Difficulty Filter */}
      <div className={styles.filterGroup}>
        <label htmlFor="difficulty-filter" className={styles.label}>
          Difficulty
        </label>
        <select
          id="difficulty-filter"
          className={styles.select}
          value={selectedDifficulty || ''}
          onChange={(e) => onDifficultyChange((e.target.value as DifficultyLevel) || undefined)}
        >
          <option value="">All Difficulties</option>
          {(Object.keys(DIFFICULTY_CONFIG) as DifficultyLevel[]).map((level) => (
            <option key={level} value={level}>
              {DIFFICULTY_CONFIG[level].icon} {DIFFICULTY_CONFIG[level].label}
            </option>
          ))}
        </select>
      </div>

      {/* Tag Filter */}
      <div className={styles.filterGroup}>
        <label htmlFor="tag-filter" className={styles.label}>
          Tag
        </label>
        <select
          id="tag-filter"
          className={styles.select}
          value={selectedTag || ''}
          onChange={(e) => onTagChange(e.target.value || undefined)}
        >
          <option value="">All Tags</option>
          {tags.map((tag) => (
            <option key={tag} value={tag}>
              {tag}
            </option>
          ))}
        </select>
      </div>

      {/* Clear Filters */}
      {hasFilters && (
        <button
          type="button"
          className={styles.clearButton}
          onClick={onClearFilters}
          aria-label="Clear all filters"
        >
          Clear Filters
        </button>
      )}
    </div>
  );
}
