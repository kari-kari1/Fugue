import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { RefineControls } from '../RefineControls';

describe('RefineControls', () => {
  const defaultProps = {
    feedback: '',
    onFeedbackChange: vi.fn(),
    mode: 'incremental' as const,
    onModeChange: vi.fn(),
    onSubmit: vi.fn(),
    isDisabled: false,
    isRefining: false,
  };

  it('renders feedback input', () => {
    render(<RefineControls {...defaultProps} />);

    const input = screen.getByPlaceholderText('输入你的反馈，指导下一步优化方向...');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('id', 'refine-feedback');
  });

  it('calls onFeedbackChange when input changes', () => {
    const onFeedbackChange = vi.fn();
    render(<RefineControls {...defaultProps} onFeedbackChange={onFeedbackChange} />);

    const input = screen.getByPlaceholderText('输入你的反馈，指导下一步优化方向...');
    fireEvent.change(input, { target: { value: 'Test feedback' } });

    expect(onFeedbackChange).toHaveBeenCalledWith('Test feedback');
  });

  it('calls onSubmit when submit button is clicked', () => {
    const onSubmit = vi.fn();
    render(<RefineControls {...defaultProps} onSubmit={onSubmit} />);

    const submitButton = screen.getByText('提交');
    fireEvent.click(submitButton);

    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it('disables controls when isDisabled is true', () => {
    render(<RefineControls {...defaultProps} isDisabled={true} />);

    const input = screen.getByPlaceholderText('输入你的反馈，指导下一步优化方向...');
    const modeSelect = screen.getByRole('combobox');
    const submitButton = screen.getByRole('button', { name: '提交' });

    expect(input).toBeDisabled();
    expect(modeSelect).toBeDisabled();
    expect(submitButton).toBeDisabled();
  });

  it('shows loading state when isRefining is true', () => {
    render(<RefineControls {...defaultProps} isRefining={true} />);

    expect(screen.getByText('优化中...')).toBeInTheDocument();
    expect(screen.queryByText('提交')).not.toBeInTheDocument();
  });
});
