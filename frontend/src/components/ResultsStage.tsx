import React, { useMemo } from 'react';
import { CheckCircle2, Clock, RotateCcw, SlidersHorizontal, XCircle } from 'lucide-react';
import { QuizQuestion } from '../types';

interface ResultsStageProps {
  questions: QuizQuestion[];
  answers: Record<string, number>;
  score: number;
  timeSpentSeconds: number;
  onRetakeSettings: () => void;
  onNewMaterial: () => void;
}

const OPTION_LABELS = ['A', 'B', 'C', 'D'];

const ResultsStage: React.FC<ResultsStageProps> = ({
  questions,
  answers,
  score,
  timeSpentSeconds,
  onRetakeSettings,
  onNewMaterial,
}) => {
  const total = questions.length || 1;
  const percentage = Math.round((score / total) * 100);
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - percentage / 100);

  const topicBreakdown = useMemo(() => {
    const map: Record<string, { correct: number; total: number }> = {};
    for (const q of questions) {
      const topic = q.topic || 'General';
      if (!map[topic]) map[topic] = { correct: 0, total: 0 };
      map[topic].total += 1;
      if (answers[q.id] === q.answer_index) {
        map[topic].correct += 1;
      }
    }
    return Object.entries(map).map(([topic, stat]) => ({
      topic,
      ...stat,
      percent: Math.round((stat.correct / stat.total) * 100),
    }));
  }, [questions, answers]);

  const mins = Math.floor(timeSpentSeconds / 60);
  const secs = timeSpentSeconds % 60;

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      {/* Top Score Ring + Topic Breakdown */}
      <div className="grid gap-6 md:grid-cols-3">
        <div className="surface-card flex flex-col items-center justify-center p-6 text-center">
          <div className="relative h-40 w-40">
            <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100" aria-hidden="true">
              <circle cx="50" cy="50" r={radius} stroke="#1e293b" strokeWidth="8" fill="none" />
              <circle
                cx="50"
                cy="50"
                r={radius}
                stroke="#06b6d4"
                strokeWidth="8"
                fill="none"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                className="transition-all duration-700"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-bold text-white">{percentage}%</span>
              <span className="text-xs text-slate-400">
                {score}/{total} correct
              </span>
            </div>
          </div>

          <div className="mt-4 inline-flex items-center gap-1.5 text-xs text-slate-400">
            <Clock className="h-3.5 w-3.5 text-cyan-400" />
            <span>
              Completed in {mins}m {secs}s
            </span>
          </div>
        </div>

        <div className="surface-card flex flex-col justify-between p-6 md:col-span-2">
          <div className="space-y-4">
            <h1 className="text-xl font-bold text-white">Topic Breakdown</h1>
            <div className="space-y-3">
              {topicBreakdown.map((item) => (
                <div key={item.topic} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-200">{item.topic}</span>
                    <span className="text-slate-400">
                      {item.correct}/{item.total} ({item.percent}%)
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                    <div
                      className="h-full rounded-full bg-cyan-400 transition-all duration-500"
                      style={{ width: `${item.percent}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 flex flex-wrap gap-3 border-t border-slate-800 pt-4">
            <button type="button" onClick={onRetakeSettings} className="btn-secondary">
              <SlidersHorizontal className="h-4 w-4" />
              <span>New Quiz on Same Source</span>
            </button>
            <button type="button" onClick={onNewMaterial} className="btn-primary">
              <RotateCcw className="h-4 w-4" />
              <span>Upload New Material</span>
            </button>
          </div>
        </div>
      </div>

      {/* Per-Question Explanations */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-white">Question Review</h2>
        <div className="space-y-4">
          {questions.map((q, idx) => {
            const userIdx = answers[q.id];
            const isCorrect = userIdx === q.answer_index;
            return (
              <article key={q.id} className="surface-card space-y-4 p-5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="font-semibold text-slate-400">Q{idx + 1}</span>
                    <span className="rounded bg-cyan-500/10 px-2 py-0.5 font-medium text-cyan-300">
                      {q.topic}
                    </span>
                    {q.source_ref && (
                      <span className="rounded border border-slate-800 bg-slate-950/70 px-2 py-0.5 text-slate-400">
                        Source: {q.source_ref}
                      </span>
                    )}
                  </div>
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                      isCorrect
                        ? 'bg-emerald-500/15 text-emerald-300'
                        : 'bg-rose-500/15 text-rose-300'
                    }`}
                  >
                    {isCorrect ? (
                      <>
                        <CheckCircle2 className="h-3.5 w-3.5" /> Correct
                      </>
                    ) : (
                      <>
                        <XCircle className="h-3.5 w-3.5" /> Incorrect
                      </>
                    )}
                  </span>
                </div>

                <p className="text-sm font-medium text-white sm:text-base">{q.question}</p>

                <div className="grid gap-3 text-xs sm:grid-cols-2">
                  <div
                    className={`rounded-xl border p-3 ${
                      userIdx === undefined
                        ? 'border-slate-800 bg-slate-950/60 text-slate-400'
                        : isCorrect
                        ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200'
                        : 'border-rose-500/30 bg-rose-500/10 text-rose-200'
                    }`}
                  >
                    <div className="mb-1 text-[11px] uppercase tracking-wider text-slate-400">
                      Your Answer
                    </div>
                    {userIdx === undefined
                      ? 'Not answered'
                      : `${OPTION_LABELS[userIdx]}. ${q.options[userIdx]}`}
                  </div>

                  <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-3 text-cyan-100">
                    <div className="mb-1 text-[11px] uppercase tracking-wider text-cyan-300">
                      Correct Answer
                    </div>
                    {OPTION_LABELS[q.answer_index]}. {q.options[q.answer_index]}
                  </div>
                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-xs leading-relaxed text-slate-300">
                  <span className="font-semibold text-slate-200">Explanation: </span>
                  {q.explanation}
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ResultsStage;
