import React from 'react';
import { AlertCircle, ArrowLeft, Loader2, RefreshCw } from 'lucide-react';

interface GeneratingStageProps {
  loading: boolean;
  error: string | null;
  numQuestions: number;
  onRetry: () => void;
  onBack: () => void;
}

const GeneratingStage: React.FC<GeneratingStageProps> = ({
  loading,
  error,
  numQuestions,
  onRetry,
  onBack,
}) => {
  if (error && !loading) {
    return (
      <div className="mx-auto max-w-xl">
        <div role="alert" className="surface-card space-y-5 border-rose-500/30 p-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rose-500/15 text-rose-400">
            <AlertCircle className="h-6 w-6" />
          </div>
          <div className="space-y-2">
            <h1 className="text-xl font-bold text-white">Quiz generation failed</h1>
            <p className="text-sm text-slate-300">{error}</p>
          </div>
          <div className="flex flex-wrap justify-center gap-3 pt-2">
            <button type="button" onClick={onBack} className="btn-secondary">
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Settings</span>
            </button>
            <button type="button" onClick={onRetry} className="btn-primary">
              <RefreshCw className="h-4 w-4" />
              <span>Retry</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6" aria-busy="true" aria-live="polite">
      <div className="flex items-center justify-center gap-3 text-center">
        <Loader2 className="h-5 w-5 animate-spin text-cyan-400" />
        <h1 className="text-xl font-semibold text-white">
          Generating {numQuestions} grounded questions...
        </h1>
      </div>

      <div className="surface-card space-y-5 p-6">
        <div className="h-4 w-28 animate-pulse rounded bg-slate-800" />
        <div className="space-y-2">
          <div className="h-6 w-5/6 animate-pulse rounded bg-slate-800" />
          <div className="h-6 w-2/3 animate-pulse rounded bg-slate-800" />
        </div>
        <div className="space-y-3 pt-2">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-12 w-full animate-pulse rounded-xl bg-slate-800/70" />
          ))}
        </div>
      </div>
    </div>
  );
};

export default GeneratingStage;
