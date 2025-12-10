/**
 * ExplanationPanel component.
 *
 * Displays AI-generated explanations for vulnerabilities and security concepts.
 * Includes loading states, provider indicators, and related topics.
 */

import { useState, useEffect } from 'react';
import type {
  ExplanationResponse,
  ExplanationType,
  DifficultyLevel,
} from '@/types';
import { PROVIDER_NAMES } from '@/types';
import { llmService } from '@/services/llm-service';
import { logger } from '@/services/logger';
import { Spinner, Badge, Button, ErrorMessage } from '@/components/common';
import { DifficultySelector } from './DifficultySelector';
import { RelatedTopics } from './RelatedTopics';
import styles from './ExplanationPanel.module.css';

const log = logger.create('ExplanationPanel');

/**
 * Props for ExplanationPanel component.
 */
export interface ExplanationPanelProps {
  /** The topic to explain */
  topic: string;
  /** Type of explanation */
  explanationType: ExplanationType;
  /** Optional additional context */
  context?: string;
  /** Whether to auto-load explanation on mount */
  autoLoad?: boolean;
  /** Callback when a related topic is clicked */
  onRelatedTopicClick?: (topic: string) => void;
  /** Optional class name */
  className?: string;
}

/**
 * ExplanationPanel displays AI-generated security explanations.
 *
 * Features:
 * - Difficulty level selector
 * - Loading and error states
 * - Provider indicator (Ollama/Cloud/Static)
 * - Related topics for further learning
 * - Refresh button to regenerate
 *
 * @example
 * ```tsx
 * <ExplanationPanel
 *   topic="default_credentials"
 *   explanationType="vulnerability"
 *   autoLoad={true}
 *   onRelatedTopicClick={(topic) => navigate(`/learn/${topic}`)}
 * />
 * ```
 */
export function ExplanationPanel({
  topic,
  explanationType,
  context,
  autoLoad = true,
  onRelatedTopicClick,
  className = '',
}: ExplanationPanelProps) {
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState<DifficultyLevel>('beginner');

  /**
   * Fetch explanation from the API.
   */
  const fetchExplanation = async (skipCache = false) => {
    setLoading(true);
    setError(null);

    log.debug('Fetching explanation', { topic, explanationType, difficulty });

    try {
      const response = await llmService.getExplanation(
        {
          explanation_type: explanationType,
          topic,
          context,
          difficulty_level: difficulty,
        },
        skipCache
      );

      setExplanation(response);
      log.info('Explanation loaded', { provider: response.provider, cached: response.cached });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load explanation';
      setError(message);
      log.error('Failed to fetch explanation', { error: message });
    } finally {
      setLoading(false);
    }
  };

  // Auto-load on mount or when topic/difficulty changes
  useEffect(() => {
    if (autoLoad && topic) {
      fetchExplanation();
    }
  }, [topic, explanationType, difficulty, autoLoad]);

  /**
   * Handle difficulty change.
   */
  const handleDifficultyChange = (newDifficulty: DifficultyLevel) => {
    setDifficulty(newDifficulty);
  };

  /**
   * Handle refresh click.
   */
  const handleRefresh = () => {
    fetchExplanation(true); // Skip cache
  };

  /**
   * Get icon for explanation type.
   */
  const getTypeIcon = (): string => {
    const icons: Record<ExplanationType, string> = {
      vulnerability: '🔒',
      remediation: '🔧',
      concept: '📚',
      service: '🔌',
      risk: '⚠️',
    };
    return icons[explanationType] || '📖';
  };

  return (
    <div
      className={`${styles.panel} ${className}`}
      role="region"
      aria-label="AI Explanation"
    >
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.titleRow}>
          <span className={styles.icon} aria-hidden="true">
            {getTypeIcon()}
          </span>
          <h3 className={styles.title}>
            {explanationType === 'vulnerability' && 'Understanding This Vulnerability'}
            {explanationType === 'remediation' && 'How to Fix'}
            {explanationType === 'concept' && 'Learn About'}
            {explanationType === 'service' && 'Service Information'}
            {explanationType === 'risk' && 'Risk Assessment'}
          </h3>
        </div>
        <DifficultySelector
          value={difficulty}
          onChange={handleDifficultyChange}
          disabled={loading}
        />
      </header>

      {/* Content */}
      <div className={styles.content}>
        {loading ? (
          <div className={styles.loadingState}>
            <Spinner size="md" />
            <span>Generating explanation...</span>
          </div>
        ) : error ? (
          <ErrorMessage
            title="Unable to load explanation"
            message={error}
            onRetry={handleRefresh}
            compact
          />
        ) : explanation ? (
          <>
            <div
              className={styles.explanation}
              dangerouslySetInnerHTML={{
                __html: formatExplanation(explanation.explanation),
              }}
            />

            {/* Provider info */}
            <div className={styles.providerInfo}>
              <Badge size="sm" className={styles.providerBadge}>
                {PROVIDER_NAMES[explanation.provider]}
              </Badge>
              {explanation.cached && (
                <span className={styles.cachedIndicator}>
                  (cached)
                </span>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRefresh}
                aria-label="Regenerate explanation"
                className={styles.refreshButton}
              >
                🔄 Refresh
              </Button>
            </div>

            {/* Related topics */}
            {explanation.related_topics.length > 0 && (
              <RelatedTopics
                topics={explanation.related_topics}
                onTopicClick={onRelatedTopicClick}
              />
            )}
          </>
        ) : (
          <div className={styles.emptyState}>
            <Button variant="primary" onClick={() => fetchExplanation()}>
              Load Explanation
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Format explanation text with basic markdown-like formatting.
 */
function formatExplanation(text: string): string {
  return text
    // Escape HTML
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // Bold (**text**)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic (*text*)
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Headings (## Heading)
    .replace(/^## (.+)$/gm, '<h4>$1</h4>')
    .replace(/^### (.+)$/gm, '<h5>$1</h5>')
    // Lists (- item)
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    // Numbered lists (1. item)
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    // Wrap consecutive <li> in <ul>
    .replace(/(<li>.+<\/li>\n?)+/g, (match) => `<ul>${match}</ul>`)
    // Paragraphs (double newline)
    .replace(/\n\n/g, '</p><p>')
    // Single newlines become <br> within paragraphs
    .replace(/\n/g, '<br>')
    // Wrap in paragraphs
    .replace(/^/, '<p>')
    .replace(/$/, '</p>')
    // Clean up empty paragraphs
    .replace(/<p><\/p>/g, '')
    .replace(/<p><br><\/p>/g, '');
}
