/**
 * Scenarios page component.
 *
 * Provides a browser interface for discovering and starting educational
 * cybersecurity scenarios. Includes filtering by content pack, difficulty,
 * and tags.
 */

import { useNavigate } from 'react-router-dom';
import { Spinner, EmptyState, ErrorMessage } from '@/components/common';
import { ScenarioCard, ScenarioFilters } from '@/components/scenarios';
import { useScenarioBrowser, useScenarioStart } from '@/hooks';
import { logger } from '@/services';
import styles from './Scenarios.module.css';

const log = logger.create('Scenarios');

/**
 * Scenarios page.
 *
 * Displays a grid of scenario cards that users can browse, filter,
 * and start. Each scenario represents a cybersecurity learning exercise.
 */
export function Scenarios() {
  const navigate = useNavigate();

  // Fetch scenario data with filtering support
  const {
    scenarios,
    isLoading,
    error,
    packs,
    tags,
    packFilter,
    difficultyFilter,
    tagFilter,
    setPackFilter,
    setDifficultyFilter,
    setTagFilter,
    clearFilters,
    refetch,
  } = useScenarioBrowser();

  // Scenario start handler
  const { start, isStarting } = useScenarioStart();

  log.debug('Scenarios page rendering', {
    scenarioCount: scenarios.length,
    isLoading,
    packFilter,
    difficultyFilter,
    tagFilter,
  });

  /**
   * Handle starting a scenario.
   */
  const handleStartScenario = async (scenarioId: string) => {
    log.info('Starting scenario', { scenarioId });
    const session = await start(scenarioId);
    if (session) {
      // Navigate to the scenario player page (to be implemented)
      navigate(`/scenarios/${scenarioId}/play`);
    }
  };

  /**
   * Handle viewing scenario details.
   */
  const handleViewDetails = (scenarioId: string) => {
    log.debug('Viewing scenario details', { scenarioId });
    navigate(`/scenarios/${scenarioId}`);
  };

  // Check if any filters are active
  const hasFilters = packFilter || difficultyFilter || tagFilter;

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>Scenarios</h1>
          <p className={styles.subtitle}>
            Practice cybersecurity skills with guided learning scenarios
          </p>
        </div>
        <div className={styles.headerStats}>
          <div className={styles.stat}>
            <span className={styles.statValue}>{scenarios.length}</span>
            <span className={styles.statLabel}>
              {scenarios.length === 1 ? 'Scenario' : 'Scenarios'}
            </span>
          </div>
          <div className={styles.stat}>
            <span className={styles.statValue}>{packs.length}</span>
            <span className={styles.statLabel}>
              {packs.length === 1 ? 'Pack' : 'Packs'}
            </span>
          </div>
        </div>
      </header>

      {/* Filters */}
      <section className={styles.filtersSection} aria-label="Filter scenarios">
        <ScenarioFilters
          packs={packs}
          tags={tags}
          selectedPack={packFilter}
          selectedDifficulty={difficultyFilter}
          selectedTag={tagFilter}
          onPackChange={setPackFilter}
          onDifficultyChange={setDifficultyFilter}
          onTagChange={setTagFilter}
          onClearFilters={clearFilters}
        />
      </section>

      {/* Content */}
      <main className={styles.content}>
        {isLoading ? (
          <div className={styles.loadingContainer}>
            <Spinner label="Loading scenarios..." size="lg" />
          </div>
        ) : error ? (
          <div className={styles.errorContainer}>
            <ErrorMessage
              message={error.detail}
              onRetry={refetch}
            />
          </div>
        ) : scenarios.length === 0 ? (
          <EmptyState
            title={hasFilters ? 'No matching scenarios' : 'No scenarios available'}
            description={
              hasFilters
                ? 'Try adjusting your filters to find more scenarios.'
                : 'Scenarios will appear here once content packs are loaded.'
            }
            action={
              hasFilters ? (
                <button
                  className={styles.clearButton}
                  onClick={clearFilters}
                >
                  Clear Filters
                </button>
              ) : undefined
            }
          />
        ) : (
          <>
            {/* Results count */}
            {hasFilters && (
              <p className={styles.resultsCount}>
                Showing {scenarios.length}{' '}
                {scenarios.length === 1 ? 'scenario' : 'scenarios'}
              </p>
            )}

            {/* Scenario grid */}
            <div className={styles.grid}>
              {scenarios.map((scenario) => (
                <ScenarioCard
                  key={scenario.id}
                  scenario={scenario}
                  onStart={handleStartScenario}
                  onClick={handleViewDetails}
                />
              ))}
            </div>
          </>
        )}
      </main>

      {/* Loading overlay for starting scenario */}
      {isStarting && (
        <div className={styles.startingOverlay} role="status" aria-live="polite">
          <Spinner label="Starting scenario..." size="lg" />
        </div>
      )}
    </div>
  );
}
