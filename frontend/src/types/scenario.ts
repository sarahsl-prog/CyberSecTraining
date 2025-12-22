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
