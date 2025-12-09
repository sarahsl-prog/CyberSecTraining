/**
 * RelatedTopics component.
 *
 * Displays a list of related topics for further learning.
 */

import { Button } from '@/components/common';
import styles from './RelatedTopics.module.css';

/**
 * Props for RelatedTopics component.
 */
export interface RelatedTopicsProps {
  /** List of related topic names */
  topics: string[];
  /** Handler called when a topic is clicked */
  onTopicClick?: (topic: string) => void;
}

/**
 * Format topic name for display.
 */
function formatTopicName(topic: string): string {
  return topic
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * RelatedTopics component for suggesting further learning.
 *
 * @example
 * ```tsx
 * <RelatedTopics
 *   topics={['password_security', 'authentication']}
 *   onTopicClick={(topic) => loadTopic(topic)}
 * />
 * ```
 */
export function RelatedTopics({ topics, onTopicClick }: RelatedTopicsProps) {
  if (topics.length === 0) {
    return null;
  }

  return (
    <div className={styles.container}>
      <h4 className={styles.title}>Learn More</h4>
      <div className={styles.topics}>
        {topics.map((topic) => (
          <Button
            key={topic}
            variant="secondary"
            size="sm"
            onClick={() => onTopicClick?.(topic)}
            className={styles.topicButton}
            disabled={!onTopicClick}
          >
            {formatTopicName(topic)}
          </Button>
        ))}
      </div>
    </div>
  );
}
