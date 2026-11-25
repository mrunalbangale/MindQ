export type Stage = 'home' | 'topics' | 'settings' | 'generating' | 'quiz' | 'results';

export type SourceType = 'pdf' | 'youtube';

export type Difficulty = 'easy' | 'medium' | 'hard';

export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  answer_index: number;
  topic: string;
  explanation: string;
  source_ref: string;
}

export interface QuizState {
  sourceType: SourceType | null;
  sourceTitle: string;
  docId: string;
  extractedTopics: string[];
  selectedTopics: string[];
  difficulty: Difficulty;
  numQuestions: number;
  timeLimitMinutes: number; // 0 = unlimited
  questions: QuizQuestion[];
  answers: Record<string, number>;
  score: number;
  timeSpentSeconds: number;
}
