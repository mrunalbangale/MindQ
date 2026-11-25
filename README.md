# MindQ

Turn PDF study material or YouTube lecture transcripts into grounded practice quizzes.

## Run Backend
```bash
cd backend && cp .env.example .env  # add GEMINI_API_KEY
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Run Frontend
```bash
cd frontend && npm run dev
```
