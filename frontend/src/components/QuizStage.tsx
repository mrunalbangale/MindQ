import React, { useEffect, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, Clock } from 'lucide-react';
import { QuizQuestion } from '../types';

interface QuizStageProps {
  questions: QuizQuestion[];
  timeLimitMinutes: number;
  onFinish: (answers: Record<string, number>, timeSpentSeconds: number) => void;
}

const OPTION_LABELS = ['A', 'B', 'C', 'D'];

const QuizStage: React.FC<QuizStageProps> = ({ questions, timeLimitMinutes, onFinish }) => {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [timeRemaining, setTimeRemaining] = useState(timeLimitMinutes * 60);
  const startedAtRef = useRef<number>(Date.now());
  const answersRef = useRef<Record<string, number>>(answers);
  answersRef.current = answers;

  const submitQuiz = () => {
    const elapsed = Math.max(1, Math.round((Date.now() - startedAtRef.current) / 1000));
    onFinish(answersRef.current, elapsed);
  };

  useEffect(() => {
    if (timeLimitMinutes <= 0) return;
    const timer = window.setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          window.clearInterval(timer);
          submitQuiz();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => window.clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeLimitMinutes]);

  const currentQ = questions[currentIdx];
  if (!currentQ) return null;

  const progressPct = ((currentIdx + 1) / questions.length) * 100;
  const answeredCount = Object.keys(answers).length;
  const mins = Math.floor(timeRemaining / 60);
  const secs = timeRemaining % 60;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Progress & Timer Header */}
      <div className="surface-card flex flex-wrap items-center justify-between gap-4 px-5 py-4">
        <div className="flex flex-1 items-center gap-4">
          <span className="text-sm font-semibold text-white">
            Question {currentIdx + 1} <span className="text-slate-400">of {questions.length}</span>
          </span>
          <div className="h-2 max-w-xs flex-1 overflow-hidden rounded-full bg-slate-800">
            <div
              className="h-full rounded-full bg-cyan-400 transition-all duration-300"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-medium text-slate-300">
          <span>{answeredCount}/{questions.length} answered</span>
          {timeLimitMinutes > 0 && (
            <span className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-950/60 px-2.5 py-1 text-cyan-300">
              <Clock className="h-3.5 w-3.5" />
              {mins}:{secs.toString().padStart(2, '0')}
            </span>
          )}
        </div>
      </div>

      {/* Question Card */}
      <div className="surface-card space-y-6 p-6 sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="rounded-lg bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-300">
            {currentQ.topic}
          </span>
          {currentQ.source_ref && (
            <span className="rounded-lg border border-slate-800 bg-slate-950/70 px-2.5 py-1 text-xs text-slate-400">
              Source: {currentQ.source_ref}
            </span>
          )}
        </div>

        <h2 className="text-lg font-semibold leading-relaxed text-white sm:text-xl">
          {currentQ.question}
        </h2>

        <div className="space-y-3" role="radiogroup" aria-label="Answer options">
          {currentQ.options.map((opt, idx) => {
            const isSelected = answers[currentQ.id] === idx;
            return (
              <button
                key={idx}
                type="button"
                role="radio"
                aria-checked={isSelected}
                onClick={() => setAnswers((prev) => ({ ...prev, [currentQ.id]: idx }))}
                className={`flex w-full items-center gap-3.5 rounded-xl border px-4 py-3.5 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 ${
                  isSelected
                    ? 'border-cyan-400 bg-cyan-500/10 text-white'
                    : 'border-slate-800 bg-slate-950/50 text-slate-300 hover:border-slate-700 hover:text-white'
                }`}
              >
                <span
                  className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-bold ${
                    isSelected
                      ? 'bg-cyan-500 text-slate-950'
                      : 'bg-slate-800 text-slate-300'
                  }`}
                >
                  {OPTION_LABELS[idx]}
                </span>
                <span className="text-sm sm:text-base">{opt}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between gap-4">
        <button
          type="button"
          onClick={() => setCurrentIdx((i) => Math.max(0, i - 1))}
          disabled={currentIdx === 0}
          className="btn-secondary"
        >
          <ChevronLeft className="h-4 w-4" />
          <span>Previous</span>
        </button>

        {currentIdx === questions.length - 1 ? (
          <button type="button" onClick={submitQuiz} className="btn-primary px-6">
            Finish Quiz
          </button>
        ) : (
          <button
            type="button"
            onClick={() => setCurrentIdx((i) => Math.min(questions.length - 1, i + 1))}
            className="btn-primary"
          >
            <span>Next</span>
            <ChevronRight className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Question Navigator */}
      <div className="flex flex-wrap justify-center gap-2 pt-2">
        {questions.map((q, idx) => {
          const isCurrent = idx === currentIdx;
          const isAnswered = answers[q.id] !== undefined;
          return (
            <button
              key={q.id}
              type="button"
              onClick={() => setCurrentIdx(idx)}
              aria-label={`Go to question ${idx + 1}`}
              className={`h-8 w-8 rounded-lg text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 ${
                isCurrent
                  ? 'bg-cyan-500 text-slate-950'
                  : isAnswered
                  ? 'border border-cyan-500/40 bg-cyan-500/15 text-cyan-300'
                  : 'border border-slate-800 bg-slate-900 text-slate-400 hover:text-white'
              }`}
            >
              {idx + 1}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default QuizStage;
