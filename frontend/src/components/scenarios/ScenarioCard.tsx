/**
 * ScenarioCard component.
 *
 * Displays a scenario summary in a card format for the scenario browser.
 */

import type { ScenarioSummary, DifficultyLevel } from '@/types';
import { DIFFICULTY_CONFIG } from '@/types';
import { Badge, Button } from '@/components/common';
import styles from './ScenarioCard.module.css';

/**
 * Props for ScenarioCard component.
 */
export interface ScenarioCardProps {
  /** Scenario summary data */
  scenario: ScenarioSummary;
  /** Handler called when Start button is clicked */
  onStart?: (scenarioId: string) => void;
  /** Handler called when card is clicked */
  onClick?: (scenarioId: string) => void;
}

/**
 * Get severity badge variant based on difficulty.
 */
function getDifficultySeverity(
  difficulty: DifficultyLevel
): 'low' | 'medium' | 'high' | 'critical' | undefined {
  const mapping: Record<DifficultyLevel, 'low' | 'medium' | 'high' | 'critical'> = {
    beginner: 'low',
    intermediate: 'medium',
    advanced: 'high',
    expert: 'critical',
  };
  return mapping[difficulty];
}

/**
 * Format estimated time for display.
 */
function formatTime(minutes?: number): string {
  if (!minutes) return '';
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
}

/**
 * ScenarioCard displays a scenario summary for browsing.
 *
 * @example
 * ```tsx
 * <ScenarioCard
 *   scenario={scenario}
 *   onStart={(id) => startScenario(id)}
 *   onClick={(id) => viewDetails(id)}
 * />
 * ```
 */
export function ScenarioCard({ scenario, onStart, onClick }: ScenarioCardProps) {
  const difficultyConfig = DIFFICULTY_CONFIG[scenario.difficulty];

  const handleCardClick = () => {
    onClick?.(scenario.id);
  };

  const handleStartClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click
    onStart?.(scenario.id);
  };

  return (
    <article
      className={`${styles.card} ${scenario.is_completed ? styles.completed : ''}`}
      onClick={handleCardClick}
      role="button"
      tabIndex={0}
      aria-label={`${scenario.name}, ${difficultyConfig.label} difficulty, ${scenario.vulnerability_count} vulnerabilities`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleCardClick();
        }
      }}
    >
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.titleRow}>
          <span className={styles.icon} aria-hidden="true">
            {difficultyConfig.icon}
          </span>
          <h3 className={styles.title}>{scenario.name}</h3>
        </div>
        <Badge severity={getDifficultySeverity(scenario.difficulty)} size="sm">
          {difficultyConfig.label}
        </Badge>
      </header>

      {/* Description */}
      <p className={styles.description}>{scenario.description}</p>

      {/* Stats */}
      <div className={styles.stats}>
        <div className={styles.stat}>
          <span className={styles.statIcon} aria-hidden="true">📱</span>
          <span className={styles.statValue}>{scenario.device_count}</span>
          <span className={styles.statLabel}>devices</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statIcon} aria-hidden="true">🔓</span>
          <span className={styles.statValue}>{scenario.vulnerability_count}</span>
          <span className={styles.statLabel}>vulnerabilities</span>
        </div>
        {scenario.estimated_time && (
          <div className={styles.stat}>
            <span className={styles.statIcon} aria-hidden="true">⏱️</span>
            <span className={styles.statValue}>{formatTime(scenario.estimated_time)}</span>
          </div>
        )}
      </div>

      {/* Tags */}
      {scenario.tags.length > 0 && (
        <div className={styles.tags}>
          {scenario.tags.slice(0, 3).map((tag) => (
            <span key={tag} className={styles.tag}>
              {tag}
            </span>
          ))}
          {scenario.tags.length > 3 && (
            <span className={styles.tagMore}>+{scenario.tags.length - 3}</span>
          )}
        </div>
      )}

      {/* Footer */}
      <footer className={styles.footer}>
        {scenario.is_completed ? (
          <div className={styles.completedBadge}>
            <span aria-hidden="true">✓</span>
            Completed
            {scenario.best_score && (
              <span className={styles.score}>Best: {scenario.best_score}%</span>
            )}
          </div>
        ) : (
          <Button
            variant="primary"
            size="sm"
            onClick={handleStartClick}
            className={styles.startButton}
          >
            Start Scenario
          </Button>
        )}
      </footer>
    </article>
  );
}
