import { useState } from 'react';
import { Brain } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';
import { extractErrorMessage, generateQuizQuestions } from './api';
import GeneratingStage from './components/GeneratingStage';
import HomeStage from './components/HomeStage';
import QuizStage from './components/QuizStage';
import ResultsStage from './components/ResultsStage';
import SettingsStage from './components/SettingsStage';
import TopicsStage from './components/TopicsStage';
import './index.css';
import { QuizState, SourceType, Stage } from './types';

const INITIAL_STATE: QuizState = {
  sourceType: null,
  sourceTitle: '',
  docId: '',
  extractedTopics: [],
  selectedTopics: [],
  difficulty: 'medium',
  numQuestions: 10,
  timeLimitMinutes: 0,
  questions: [],
  answers: {},
  score: 0,
  timeSpentSeconds: 0,
};

function App() {
  const [stage, setStage] = useState<Stage>('home');
  const [state, setState] = useState<QuizState>(INITIAL_STATE);
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);

  const handleIngested = (payload: {
    sourceType: SourceType;
    sourceTitle: string;
    docId: string;
    topics: string[];
  }) => {
    setState({
      ...INITIAL_STATE,
      sourceType: payload.sourceType,
      sourceTitle: payload.sourceTitle,
      docId: payload.docId,
      extractedTopics: payload.topics,
      selectedTopics: payload.topics.slice(0, 5),
    });
    setStage('topics');
  };

  const handleGenerate = async () => {
    setStage('generating');
    setGenerating(true);
    setGenError(null);
    try {
      const questions = await generateQuizQuestions({
        doc_id: state.docId,
        topics: state.selectedTopics,
        difficulty: state.difficulty,
        num_questions: state.numQuestions,
      });
      if (!questions.length) {
        throw new Error('No questions were returned by the server.');
      }
      setState((prev) => ({
        ...prev,
        questions,
        answers: {},
        score: 0,
        timeSpentSeconds: 0,
      }));
      setStage('quiz');
    } catch (err) {
      const msg = extractErrorMessage(err, 'Failed to generate quiz questions.');
      setGenError(msg);
      toast.error(msg);
    } finally {
      setGenerating(false);
    }
  };

  const handleQuizFinish = (answers: Record<string, number>, timeSpentSeconds: number) => {
    const score = state.questions.reduce(
      (acc, q) => acc + (answers[q.id] === q.answer_index ? 1 : 0),
      0
    );
    setState((prev) => ({
      ...prev,
      answers,
      score,
      timeSpentSeconds,
    }));
    setStage('results');
  };

  const resetHome = () => {
    setGenError(null);
    setState(INITIAL_STATE);
    setStage('home');
  };

  return (
    <div className="min-h-screen text-slate-100">
      <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-md">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4 sm:px-6">
          <button
            type="button"
            onClick={resetHome}
            className="flex items-center gap-2.5 rounded-xl text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-500/15 text-cyan-400">
              <Brain className="h-5 w-5" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-white">MindQ</span>
              <span className="ml-2 text-xs text-slate-400 hidden sm:inline">
                PDF &amp; YouTube Practice Tests
              </span>
            </div>
          </button>

          {stage !== 'home' && (
            <button type="button" onClick={resetHome} className="btn-secondary px-3 py-1.5 text-xs">
              Start Over
            </button>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
        {stage === 'home' && <HomeStage onIngested={handleIngested} />}

        {stage === 'topics' && (
          <TopicsStage
            sourceType={state.sourceType}
            sourceTitle={state.sourceTitle}
            extractedTopics={state.extractedTopics}
            selectedTopics={state.selectedTopics}
            onChangeTopics={(selectedTopics) => setState((prev) => ({ ...prev, selectedTopics }))}
            onBack={resetHome}
            onNext={() => setStage('settings')}
          />
        )}

        {stage === 'settings' && (
          <SettingsStage
            difficulty={state.difficulty}
            numQuestions={state.numQuestions}
            timeLimitMinutes={state.timeLimitMinutes}
            onChange={(patch) => setState((prev) => ({ ...prev, ...patch }))}
            onBack={() => setStage('topics')}
            onGenerate={handleGenerate}
          />
        )}

        {stage === 'generating' && (
          <GeneratingStage
            loading={generating}
            error={genError}
            numQuestions={state.numQuestions}
            onRetry={handleGenerate}
            onBack={() => setStage('settings')}
          />
        )}

        {stage === 'quiz' && (
          <QuizStage
            questions={state.questions}
            timeLimitMinutes={state.timeLimitMinutes}
            onFinish={handleQuizFinish}
          />
        )}

        {stage === 'results' && (
          <ResultsStage
            questions={state.questions}
            answers={state.answers}
            score={state.score}
            timeSpentSeconds={state.timeSpentSeconds}
            onRetakeSettings={() => setStage('settings')}
            onNewMaterial={resetHome}
          />
        )}
      </main>

      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#0f172a',
            color: '#f1f5f9',
            border: '1px solid #1e293b',
          },
        }}
      />
    </div>
  );
}

export default App;
