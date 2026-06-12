import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { IterationMessage } from '../IterationMessage';
import type { Iteration } from '../../../types/iteration';

// Mock the parseUTC utility
vi.mock('../../../lib/utils', () => ({
  parseUTC: (timestamp: string) => new Date(timestamp),
}));

describe('IterationMessage', () => {
  const createMockIteration = (overrides: Partial<Iteration> = {}): Iteration => ({
    id: 'iter-1',
    execution_id: 'exec-1',
    iteration_number: 1,
    feedback: 'Test feedback',
    mode: 'incremental',
    status: 'pending',
    tokens_used: 1500,
    cost_usd: 0.05,
    created_at: '2024-01-01T10:30:00Z',
    ...overrides,
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders iteration number', () => {
    const iteration = createMockIteration({ iteration_number: 3 });
    render(<IterationMessage iteration={iteration} isLatest={false} />);

    expect(screen.getByText('迭代 #3')).toBeInTheDocument();
  });

  it('renders feedback text', () => {
    const iteration = createMockIteration({
      feedback: 'Please improve the output quality',
    });
    render(<IterationMessage iteration={iteration} isLatest={false} />);

    expect(screen.getByText('Please improve the output quality')).toBeInTheDocument();
  });

  it('displays refined output when completed', () => {
    const iteration = createMockIteration({
      status: 'completed',
      refined_output: 'Optimized version of the output',
    });
    render(<IterationMessage iteration={iteration} isLatest={false} />);

    expect(screen.getByText('优化结果')).toBeInTheDocument();
    expect(screen.getByText('Optimized version of the output')).toBeInTheDocument();
  });

  it('displays token usage', () => {
    const iteration = createMockIteration({ tokens_used: 2500 });
    render(<IterationMessage iteration={iteration} isLatest={false} />);

    expect(screen.getByText('2.5k tokens')).toBeInTheDocument();
  });

  it('displays cost information', () => {
    const iteration = createMockIteration({ cost_usd: 0.1234 });
    render(<IterationMessage iteration={iteration} isLatest={false} />);

    expect(screen.getByText('$0.1234')).toBeInTheDocument();
  });

  it('shows mode label correctly', () => {
    const incremental = createMockIteration({ mode: 'incremental' });
    render(<IterationMessage iteration={incremental} isLatest={false} />);

    expect(screen.getByText('增量优化')).toBeInTheDocument();
  });

  it('shows reexecute mode label', () => {
    const reexecute = createMockIteration({ mode: 'reexecute' });
    render(<IterationMessage iteration={reexecute} isLatest={false} />);

    expect(screen.getByText('重新执行')).toBeInTheDocument();
  });

  it('applies different styling when isLatest is true', () => {
    const iteration = createMockIteration({ iteration_number: 5 });
    const { container } = render(
      <IterationMessage iteration={iteration} isLatest={true} />
    );

    const element = container.firstChild as HTMLElement;
    expect(element.className).toContain('border-blue-500/50');
    expect(element.className).toContain('shadow-lg');
  });

  it('renders without error when feedback is empty', () => {
    const iteration = createMockIteration({ feedback: '' });
    render(<IterationMessage iteration={iteration} isLatest={false} />);

    expect(screen.getByText('(无反馈)')).toBeInTheDocument();
  });

  it('displays error message when failed', () => {
    const iteration = createMockIteration({
      status: 'failed',
      error_message: 'API rate limit exceeded',
    });
    render(<IterationMessage iteration={iteration} isLatest={false} />);

    expect(screen.getByText('错误')).toBeInTheDocument();
    expect(screen.getByText('API rate limit exceeded')).toBeInTheDocument();
  });

  it('shows duration when completed', () => {
    const iteration = createMockIteration({
      status: 'completed',
      created_at: '2024-01-01T10:00:00Z',
      completed_at: '2024-01-01T10:01:30Z',
    });
    render(<IterationMessage iteration={iteration} isLatest={false} />);

    expect(screen.getByText('1m 30s')).toBeInTheDocument();
  });
});
