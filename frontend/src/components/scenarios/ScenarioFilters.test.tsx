/**
 * ScenarioFilters component unit tests.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ScenarioFilters } from './ScenarioFilters';
import { mockContentPacks, mockScenarioTags } from '@/test/mocks';
import type { DifficultyLevel } from '@/types';

describe('ScenarioFilters', () => {
  const defaultProps = {
    packs: mockContentPacks,
    tags: mockScenarioTags,
    onPackChange: vi.fn(),
    onDifficultyChange: vi.fn(),
    onTagChange: vi.fn(),
    onClearFilters: vi.fn(),
  };

  it('renders all filter dropdowns', () => {
    render(<ScenarioFilters {...defaultProps} />);

    expect(screen.getByLabelText('Content Pack')).toBeInTheDocument();
    expect(screen.getByLabelText('Difficulty')).toBeInTheDocument();
    expect(screen.getByLabelText('Tag')).toBeInTheDocument();
  });

  it('displays content packs in dropdown', () => {
    render(<ScenarioFilters {...defaultProps} />);

    const packSelect = screen.getByLabelText('Content Pack');

    mockContentPacks.forEach((pack) => {
      expect(packSelect).toContainHTML(pack.name);
    });
  });

  it('displays scenario count in pack options', () => {
    render(<ScenarioFilters {...defaultProps} />);

    const packSelect = screen.getByLabelText('Content Pack');

    // Should show "(3)" for the first pack
    expect(packSelect).toContainHTML('Core Pack (3)');
  });

  it('displays all difficulty levels', () => {
    render(<ScenarioFilters {...defaultProps} />);

    const difficultySelect = screen.getByLabelText('Difficulty');

    expect(difficultySelect).toContainHTML('Beginner');
    expect(difficultySelect).toContainHTML('Intermediate');
    expect(difficultySelect).toContainHTML('Advanced');
    expect(difficultySelect).toContainHTML('Expert');
  });

  it('displays tags in dropdown', () => {
    render(<ScenarioFilters {...defaultProps} />);

    const tagSelect = screen.getByLabelText('Tag');

    mockScenarioTags.forEach((tag) => {
      expect(tagSelect).toContainHTML(tag);
    });
  });

  it('calls onPackChange when pack is selected', () => {
    const onPackChange = vi.fn();
    render(<ScenarioFilters {...defaultProps} onPackChange={onPackChange} />);

    fireEvent.change(screen.getByLabelText('Content Pack'), {
      target: { value: 'core' },
    });

    expect(onPackChange).toHaveBeenCalledWith('core');
  });

  it('calls onPackChange with undefined when "All Packs" is selected', () => {
    const onPackChange = vi.fn();
    render(
      <ScenarioFilters
        {...defaultProps}
        selectedPack="core"
        onPackChange={onPackChange}
      />
    );

    fireEvent.change(screen.getByLabelText('Content Pack'), {
      target: { value: '' },
    });

    expect(onPackChange).toHaveBeenCalledWith(undefined);
  });

  it('calls onDifficultyChange when difficulty is selected', () => {
    const onDifficultyChange = vi.fn();
    render(
      <ScenarioFilters {...defaultProps} onDifficultyChange={onDifficultyChange} />
    );

    fireEvent.change(screen.getByLabelText('Difficulty'), {
      target: { value: 'intermediate' },
    });

    expect(onDifficultyChange).toHaveBeenCalledWith('intermediate');
  });

  it('calls onTagChange when tag is selected', () => {
    const onTagChange = vi.fn();
    render(<ScenarioFilters {...defaultProps} onTagChange={onTagChange} />);

    fireEvent.change(screen.getByLabelText('Tag'), {
      target: { value: 'router' },
    });

    expect(onTagChange).toHaveBeenCalledWith('router');
  });

  it('shows Clear Filters button when filters are active', () => {
    render(<ScenarioFilters {...defaultProps} selectedPack="core" />);

    expect(
      screen.getByRole('button', { name: /clear all filters/i })
    ).toBeInTheDocument();
  });

  it('hides Clear Filters button when no filters are active', () => {
    render(<ScenarioFilters {...defaultProps} />);

    expect(
      screen.queryByRole('button', { name: /clear all filters/i })
    ).not.toBeInTheDocument();
  });

  it('calls onClearFilters when Clear Filters is clicked', () => {
    const onClearFilters = vi.fn();
    render(
      <ScenarioFilters
        {...defaultProps}
        selectedDifficulty={'beginner' as DifficultyLevel}
        onClearFilters={onClearFilters}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /clear all filters/i }));

    expect(onClearFilters).toHaveBeenCalled();
  });

  it('shows selected values in dropdowns', () => {
    render(
      <ScenarioFilters
        {...defaultProps}
        selectedPack="core"
        selectedDifficulty={'intermediate' as DifficultyLevel}
        selectedTag="router"
      />
    );

    expect(screen.getByLabelText('Content Pack')).toHaveValue('core');
    expect(screen.getByLabelText('Difficulty')).toHaveValue('intermediate');
    expect(screen.getByLabelText('Tag')).toHaveValue('router');
  });

  it('has proper accessibility role', () => {
    render(<ScenarioFilters {...defaultProps} />);

    expect(
      screen.getByRole('group', { name: /scenario filters/i })
    ).toBeInTheDocument();
  });

  it('renders with empty packs and tags arrays', () => {
    render(<ScenarioFilters {...defaultProps} packs={[]} tags={[]} />);

    // Should still render with "All" options
    expect(screen.getByLabelText('Content Pack')).toBeInTheDocument();
    expect(screen.getByLabelText('Tag')).toBeInTheDocument();
  });
});
