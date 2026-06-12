import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('[Fugue] React Error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-[var(--bg-deep)]">
          <div className="w-full max-w-md glass radius-2xl shadow-2xl p-8 text-center mx-4">
            <div className="flex justify-center mb-5">
              <div className="w-14 h-14 rounded-full bg-accent-red-dim flex items-center justify-center">
                <AlertCircle className="w-7 h-7 text-accent-red" />
              </div>
            </div>

            <h1 className="text-[var(--text-xl)] font-semibold text-primary mb-2">
              出现了一些问题
            </h1>

            <p className="text-[var(--text-sm)] text-secondary mb-6">
              {this.state.error?.message || '页面渲染时发生未知错误'}
            </p>

            <button
              className="w-full py-3 px-4 bg-[var(--accent-steel)] text-[#060609] font-medium radius-lg hover:bg-[var(--accent-steel-hover)] transition-colors shadow-md inline-flex items-center justify-center gap-2"
              onClick={this.handleReset}
            >
              <RefreshCw className="w-4 h-4" />
              重试
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
