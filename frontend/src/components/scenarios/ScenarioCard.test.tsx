/**
 * ScenarioCard component unit tests.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ScenarioCard } from './ScenarioCard';
import { mockScenarioSummary, mockScenarioSummaries } from '@/test/mocks';
import type { ScenarioSummary, DifficultyLevel } from '@/types';

describe('ScenarioCard', () => {
  it('renders scenario name and description', () => {
    render(<ScenarioCard scenario={mockScenarioSummary} />);

    expect(screen.getByRole('heading', { name: mockScenarioSummary.name })).toBeInTheDocument();
    expect(screen.getByText(mockScenarioSummary.description)).toBeInTheDocument();
  });

  it('displays difficulty badge', () => {
    render(<ScenarioCard scenario={mockScenarioSummary} />);

    expect(screen.getByText('Beginner')).toBeInTheDocument();
  });

  it('displays device count', () => {
    render(<ScenarioCard scenario={mockScenarioSummary} />);

    expect(screen.getByText(mockScenarioSummary.device_count.toString())).toBeInTheDocument();
    expect(screen.getByText('devices')).toBeInTheDocument();
  });

  it('displays vulnerability count', () => {
    render(<ScenarioCard scenario={mockScenarioSummary} />);

    expect(screen.getByText(mockScenarioSummary.vulnerability_count.toString())).toBeInTheDocument();
    expect(screen.getByText('vulnerabilities')).toBeInTheDocument();
  });

  it('displays estimated time when provided', () => {
    render(<ScenarioCard scenario={mockScenarioSummary} />);

    expect(screen.getByText('30 min')).toBeInTheDocument();
  });

  it('displays tags (up to 3)', () => {
    render(<ScenarioCard scenario={mockScenarioSummary} />);

    mockScenarioSummary.tags.forEach((tag) => {
      expect(screen.getByText(tag)).toBeInTheDocument();
    });
  });

  it('shows "+N" indicator when more than 3 tags', () => {
    const scenarioWithManyTags: ScenarioSummary = {
      ...mockScenarioSummary,
      tags: ['tag1', 'tag2', 'tag3', 'tag4', 'tag5'],
    };

    render(<ScenarioCard scenario={scenarioWithManyTags} />);

    expect(screen.getByText('+2')).toBeInTheDocument();
  });

  it('shows Start Scenario button for incomplete scenarios', () => {
    render(<ScenarioCard scenario={mockScenarioSummary} />);

    expect(screen.getByRole('button', { name: /start scenario/i })).toBeInTheDocument();
  });

  it('shows completed badge for completed scenarios', () => {
    const completedScenario = mockScenarioSummaries.find(s => s.is_completed);

    render(<ScenarioCard scenario={completedScenario!} />);

    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /start scenario/i })).not.toBeInTheDocument();
  });

  it('shows best score for completed scenarios', () => {
    const completedScenario = mockScenarioSummaries.find(s => s.is_completed);

    render(<ScenarioCard scenario={completedScenario!} />);

    expect(screen.getByText('Best: 85%')).toBeInTheDocument();
  });

  it('calls onStart when Start button is clicked', () => {
    const onStart = vi.fn();
    render(<ScenarioCard scenario={mockScenarioSummary} onStart={onStart} />);

    fireEvent.click(screen.getByRole('button', { name: /start scenario/i }));

    expect(onStart).toHaveBeenCalledWith(mockScenarioSummary.id);
  });

  it('calls onClick when card is clicked', () => {
    const onClick = vi.fn();
    render(<ScenarioCard scenario={mockScenarioSummary} onClick={onClick} />);

    fireEvent.click(screen.getByRole('button', { name: new RegExp(mockScenarioSummary.name) }));

    expect(onClick).toHaveBeenCalledWith(mockScenarioSummary.id);
  });

  it('does not call onClick when Start button is clicked', () => {
    const onClick = vi.fn();
    const onStart = vi.fn();
    render(<ScenarioCard scenario={mockScenarioSummary} onClick={onClick} onStart={onStart} />);

    fireEvent.click(screen.getByRole('button', { name: /start scenario/i }));

    expect(onStart).toHaveBeenCalled();
    expect(onClick).not.toHaveBeenCalled();
  });

  it('is keyboard accessible', () => {
    const onClick = vi.fn();
    render(<ScenarioCard scenario={mockScenarioSummary} onClick={onClick} />);

    const card = screen.getByRole('button', { name: new RegExp(mockScenarioSummary.name) });

    fireEvent.keyDown(card, { key: 'Enter' });
    expect(onClick).toHaveBeenCalledTimes(1);

    fireEvent.keyDown(card, { key: ' ' });
    expect(onClick).toHaveBeenCalledTimes(2);
  });

  it('has proper accessibility attributes', () => {
    render(<ScenarioCard scenario={mockScenarioSummary} />);

    const card = screen.getByRole('button', { name: new RegExp(mockScenarioSummary.name) });

    expect(card).toHaveAttribute('tabIndex', '0');
    expect(card).toHaveAttribute(
      'aria-label',
      expect.stringContaining(mockScenarioSummary.name)
    );
  });

  it.each([
    ['beginner', 'Beginner'],
    ['intermediate', 'Intermediate'],
    ['advanced', 'Advanced'],
    ['expert', 'Expert'],
  ])('displays correct label for %s difficulty', (difficulty, expectedLabel) => {
    const scenario: ScenarioSummary = {
      ...mockScenarioSummary,
      difficulty: difficulty as DifficultyLevel,
    };

    render(<ScenarioCard scenario={scenario} />);

    expect(screen.getByText(expectedLabel)).toBeInTheDocument();
  });

  it('formats time correctly for hours', () => {
    const scenario: ScenarioSummary = {
      ...mockScenarioSummary,
      estimated_time: 90,
    };

    render(<ScenarioCard scenario={scenario} />);

    expect(screen.getByText('1h 30m')).toBeInTheDocument();
  });

  it('formats time correctly for full hours', () => {
    const scenario: ScenarioSummary = {
      ...mockScenarioSummary,
      estimated_time: 120,
    };

    render(<ScenarioCard scenario={scenario} />);

    expect(screen.getByText('2h')).toBeInTheDocument();
  });
});
