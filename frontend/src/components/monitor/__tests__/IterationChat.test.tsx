import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { IterationChat } from '../IterationChat';
import type { Iteration } from '../../../types/iteration';

// Mock child components
vi.mock('../IterationMessage', () => ({
  IterationMessage: vi.fn(({ iteration, isLatest }) => (
    <div data-testid={`iteration-${iteration.id}`}>
      Iteration {iteration.iteration_number}
      {isLatest && <span data-testid="latest-indicator">Latest</span>}
    </div>
  )),
}));

vi.mock('../RefineControls', () => ({
  RefineControls: vi.fn(({ isRefining }) => (
    <div data-testid="refine-controls">
      Refine Controls {isRefining && <span>Refining...</span>}
    </div>
  )),
}));

describe('IterationChat', () => {
  const createMockIteration = (overrides: Partial<Iteration> = {}): Iteration => ({
    id: 'iter-1',
    execution_id: 'exec-1',
    iteration_number: 1,
    feedback: 'Test feedback',
    mode: 'incremental',
    status: 'completed',
    tokens_used: 1500,
    cost_usd: 0.05,
    created_at: '2024-01-01T10:30:00Z',
    ...overrides,
  });

  const defaultProps = {
    executionId: 'exec-1',
    iterations: [
      createMockIteration({ id: 'iter-1', iteration_number: 1 }),
      createMockIteration({ id: 'iter-2', iteration_number: 2 }),
    ],
    onRefine: vi.fn(),
    isRefining: false,
    executionStatus: 'running',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders conversation title', () => {
    render(<IterationChat {...defaultProps} />);
    expect(screen.getByText('迭代对话')).toBeInTheDocument();
  });

  it('renders iteration count', () => {
    render(<IterationChat {...defaultProps} />);
    expect(screen.getByText('2 次迭代')).toBeInTheDocument();
  });
});
