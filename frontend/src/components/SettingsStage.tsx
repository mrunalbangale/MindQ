import React from 'react';
import { ArrowLeft, Clock, Sparkles } from 'lucide-react';
import { Difficulty } from '../types';

interface SettingsStageProps {
  difficulty: Difficulty;
  numQuestions: number;
  timeLimitMinutes: number;
  onChange: (patch: Partial<{ difficulty: Difficulty; numQuestions: number; timeLimitMinutes: number }>) => void;
  onBack: () => void;
  onGenerate: () => void;
}

const DIFFICULTIES: Array<{ id: Difficulty; label: string; desc: string }> = [
  { id: 'easy', label: 'Easy', desc: 'Core definitions & recall' },
  { id: 'medium', label: 'Medium', desc: 'Applied concepts & comparisons' },
  { id: 'hard', label: 'Hard', desc: 'Deep analysis & edge cases' },
];

const COUNT_PRESETS = [5, 10, 15, 20, 30];
const TIMER_PRESETS = [
  { label: 'Unlimited', minutes: 0 },
  { label: '10 min', minutes: 10 },
  { label: '20 min', minutes: 20 },
  { label: '30 min', minutes: 30 },
];

const SettingsStage: React.FC<SettingsStageProps> = ({
  difficulty,
  numQuestions,
  timeLimitMinutes,
  onChange,
  onBack,
  onGenerate,
}) => {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-white sm:text-3xl">Quiz Settings</h1>
        <p className="text-sm text-slate-400">
          Customize difficulty, question count (1–30), and an optional timer before generating.
        </p>
      </div>

      <div className="surface-card space-y-7 p-6">
        {/* Difficulty */}
        <div className="space-y-3">
          <span className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
            Difficulty
          </span>
          <div className="grid gap-3 sm:grid-cols-3">
            {DIFFICULTIES.map((item) => {
              const active = difficulty === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  aria-pressed={active}
                  onClick={() => onChange({ difficulty: item.id })}
                  className={`rounded-xl border p-3.5 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 ${
                    active
                      ? 'border-cyan-400 bg-cyan-500/10 text-white'
                      : 'border-slate-800 bg-slate-950/50 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="text-sm font-semibold">{item.label}</div>
                  <div className="mt-1 text-xs text-slate-400">{item.desc}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Question Count */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label htmlFor="question-count-range" className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Number of Questions
            </label>
            <span className="text-sm font-bold text-cyan-400">{numQuestions} questions</span>
          </div>

          <input
            id="question-count-range"
            type="range"
            min={1}
            max={30}
            value={numQuestions}
            onChange={(e) => onChange({ numQuestions: Number(e.target.value) })}
            className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-slate-800 accent-cyan-400"
          />

          <div className="flex flex-wrap gap-2">
            {COUNT_PRESETS.map((n) => (
              <button
                key={n}
                type="button"
                onClick={() => onChange({ numQuestions: n })}
                className={`rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 ${
                  numQuestions === n
                    ? 'border-cyan-400 bg-cyan-500/15 text-cyan-300'
                    : 'border-slate-800 bg-slate-950/50 text-slate-400 hover:text-white'
                }`}
              >
                {n}
              </button>
            ))}
          </div>
        </div>

        {/* Optional Timer */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <Clock className="h-3.5 w-3.5 text-cyan-400" />
            <span>Timer (Optional)</span>
          </div>

          <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
            {TIMER_PRESETS.map((preset) => {
              const active = timeLimitMinutes === preset.minutes;
              return (
                <button
                  key={preset.minutes}
                  type="button"
                  aria-pressed={active}
                  onClick={() => onChange({ timeLimitMinutes: preset.minutes })}
                  className={`rounded-xl border px-3 py-2.5 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 ${
                    active
                      ? 'border-cyan-400 bg-cyan-500/15 text-cyan-300'
                      : 'border-slate-800 bg-slate-950/50 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  {preset.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <button type="button" onClick={onBack} className="btn-secondary">
          <ArrowLeft className="h-4 w-4" />
          <span>Back</span>
        </button>
        <button type="button" onClick={onGenerate} className="btn-primary px-6">
          <Sparkles className="h-4 w-4" />
          <span>Generate</span>
        </button>
      </div>
    </div>
  );
};

export default SettingsStage;
