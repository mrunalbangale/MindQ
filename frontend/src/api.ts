import axios from 'axios';
import { Difficulty, QuizQuestion } from './types';

export const API_URL = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_URL,
  timeout: 120000,
});

export function extractErrorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }
    if (err.code === 'ECONNABORTED') {
      return 'Request timed out. Please try again.';
    }
    if (!err.response) {
      return `Cannot reach backend at ${API_URL}. Make sure the API server is running.`;
    }
  }
  if (err instanceof Error && err.message) {
    return err.message;
  }
  return fallback;
}

export async function uploadPdfDocument(file: File): Promise<{ doc_id: string; topics: string[] }> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await client.post<{ doc_id: string; topics: string[] }>('/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

export async function ingestYouTubeVideo(url: string): Promise<{ doc_id: string; title: string; topics: string[] }> {
  const res = await client.post<{ doc_id: string; title: string; topics: string[] }>('/youtube/ingest', { url });
  return res.data;
}

export async function generateQuizQuestions(params: {
  doc_id: string;
  topics: string[];
  difficulty: Difficulty;
  num_questions: number;
}): Promise<QuizQuestion[]> {
  const res = await client.post<{ questions: QuizQuestion[] }>('/quiz/generate', params);
  return res.data.questions || [];
}
