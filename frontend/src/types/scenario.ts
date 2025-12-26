/**
 * Type definitions for scenarios.
 */

export interface ScenarioStep {
  id: string;
  title: string;
  description: string;
  type: 'instruction' | 'question' | 'verification';
  content: string;
  hints: string[];
  expected_answer?: string;
  points: number;
}

export interface ScenarioSummary {
  id: string;
  title: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  estimated_time: number;
  tags: string[];
  author: string;
  version: string;
}

export interface Scenario extends ScenarioSummary {
  prerequisites: string[];
  learning_objectives: string[];
  steps: ScenarioStep[];
  related_vulnerabilities: string[];
}

/**
 * Scenario-related types.
 *
 * These types define the data structures for educational
 * cybersecurity scenarios.
 */

/**
 * Difficulty levels for scenarios.
 */
export type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert';

/**
 * A vulnerability within a scenario.
 */
export interface ScenarioVulnerability {
  /** Vulnerability type identifier */
  vuln_type: string;
  /** Severity level */
  severity: string;
  /** Affected service name */
  service?: string;
  /** Affected port number */
  port?: number;
  /** Hint for finding this vulnerability */
  hint?: string;
}

/**
 * A simulated device within a scenario.
 */
export interface ScenarioDevice {
  /** Device identifier */
  id: string;
  /** Device hostname */
  hostname: string;
  /** IP address */
  ip: string;
  /** Device type */
  device_type: string;
  /** Operating system */
  os?: string;
  /** Open ports */
  open_ports: number[];
  /** Device vulnerabilities */
  vulnerabilities: ScenarioVulnerability[];
  /** Is network gateway */
  is_gateway: boolean;
}

/**
 * Scenario metadata.
 */
export interface ScenarioMetadata {
  /** Scenario author */
  author: string;
  /** Creation date */
  created_at?: string;
  /** Last update date */
  updated_at?: string;
  /** Scenario version */
  version: string;
  /** Tags for filtering */
  tags: string[];
  /** Estimated completion time in minutes */
  estimated_time?: number;
  /** Prerequisite scenario IDs */
  prerequisites: string[];
}

/**
 * Complete scenario data.
 */
export interface Scenario {
  /** Unique scenario identifier */
  id: string;
  /** Parent pack ID */
  pack_id: string;
  /** Display name */
  name: string;
  /** Detailed description */
  description: string;
  /** Difficulty level */
  difficulty: DifficultyLevel;
  /** Learning objectives */
  learning_objectives: string[];
  /** Network devices */
  devices: ScenarioDevice[];
  /** Scenario metadata */
  metadata: ScenarioMetadata;
  /** Success criteria */
  success_criteria: {
    vulnerabilities_to_find?: number;
    minimum_score?: number;
  };
}

/**
 * Summary information for scenario listing.
 */
export interface ScenarioSummary {
  /** Scenario ID */
  id: string;
  /** Pack ID */
  pack_id: string;
  /** Display name */
  name: string;
  /** Description */
  description: string;

  /** Number of devices */
  device_count: number;
  /** Number of vulnerabilities */
  vulnerability_count: number;
  /** Estimated time in minutes */
  estimated_time: number;
  /** Tags */
  tags: string[];
  /** Whether completed by user */
  is_completed: boolean;
  /** Best score achieved */
  best_score?: number;
}

/**
 * Content pack information.
 */
export interface ContentPack {
  /** Pack ID */
  id: string;
  /** Pack name */
  name: string;
  /** Pack description */
  description: string;
  /** Pack version */
  version: string;
  /** Number of scenarios in pack */
  scenario_count: number;
}

/**
 * Difficulty level configuration.
 */
export interface DifficultyInfo {
  /** Value used in API */
  value: DifficultyLevel;
  /** Display label */
  label: string;
  /** Description */
  description: string;
}

/**
 * Session data when starting a scenario.
 */
export interface ScenarioSession {
  /** Scenario ID */
  scenario_id: string;
  /** Scenario name */
  name: string;
  /** Difficulty level */
  difficulty: DifficultyLevel;
  /** Number of devices */
  device_count: number;
  /** Number of vulnerabilities to find */
  vulnerability_count: number;
  /** Learning objectives */
  learning_objectives: string[];
  /** Devices (without vulnerability details) */
  devices: Array<{
    id: string;
    hostname: string;
    ip: string;
    device_type: string;
    is_gateway: boolean;
  }>;
  /** Success criteria */
  success_criteria: {
    vulnerabilities_to_find?: number;
    minimum_score?: number;
  };
}

/**
 * Difficulty level display configuration.
 */
export const DIFFICULTY_CONFIG: Record<DifficultyLevel, {
  label: string;
  color: string;
  icon: string;
}> = {
  beginner: {
    label: 'Beginner',
    color: 'var(--color-severity-low)',
    icon: '🌱',
  },
  intermediate: {
    label: 'Intermediate',
    color: 'var(--color-severity-medium)',
    icon: '📖',
  },
  advanced: {
    label: 'Advanced',
    color: 'var(--color-severity-high)',
    icon: '🎓',
  },
  expert: {
    label: 'Expert',
    color: 'var(--color-severity-critical)',
    icon: '🏆',
  },
};
