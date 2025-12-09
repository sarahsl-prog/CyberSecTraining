/**
 * DifficultySelector component.
 *
 * A segmented control for selecting explanation difficulty level.
 */

import type { DifficultyLevel } from '@/types';
import { DIFFICULTY_DESCRIPTIONS } from '@/types';
import styles from './DifficultySelector.module.css';

/**
 * Props for DifficultySelector component.
 */
export interface DifficultySelectorProps {
  /** Currently selected difficulty */
  value: DifficultyLevel;
  /** Handler called when difficulty changes */
  onChange: (difficulty: DifficultyLevel) => void;
  /** Whether the selector is disabled */
  disabled?: boolean;
}

/**
 * Difficulty levels with labels.
 */
const DIFFICULTY_OPTIONS: { value: DifficultyLevel; label: string; icon: string }[] = [
  { value: 'beginner', label: 'Beginner', icon: '🌱' },
  { value: 'intermediate', label: 'Intermediate', icon: '📖' },
  { value: 'advanced', label: 'Advanced', icon: '🎓' },
];

/**
 * DifficultySelector component for choosing explanation complexity.
 *
 * @example
 * ```tsx
 * <DifficultySelector
 *   value={difficulty}
 *   onChange={(d) => setDifficulty(d)}
 * />
 * ```
 */
export function DifficultySelector({
  value,
  onChange,
  disabled = false,
}: DifficultySelectorProps) {
  return (
    <div
      className={styles.selector}
      role="radiogroup"
      aria-label="Difficulty level"
    >
      {DIFFICULTY_OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          role="radio"
          aria-checked={value === option.value}
          className={`${styles.option} ${value === option.value ? styles.selected : ''}`}
          onClick={() => onChange(option.value)}
          disabled={disabled}
          title={DIFFICULTY_DESCRIPTIONS[option.value]}
        >
          <span className={styles.icon} aria-hidden="true">
            {option.icon}
          </span>
          <span className={styles.label}>{option.label}</span>
        </button>
      ))}
    </div>
  );
}
