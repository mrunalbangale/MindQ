from fastapi import APIRouter, HTTPException

from app.schemas.request_response import QuizGenerateRequest, QuizGenerateResponse
from app.services.llm import LLMError
from app.services.mcq_generation.mcq_generator import generate_mcqs_for_doc
from app.services.rag_store import get_document

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.post("/generate", response_model=QuizGenerateResponse)
def generate_quiz(req: QuizGenerateRequest):
    record = get_document(req.doc_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Document session not found or expired. Please upload the PDF or ingest the YouTube link again.",
        )

    clean_topics = [t.strip() for t in req.topics if t and t.strip()]
    if not clean_topics:
        raise HTTPException(status_code=400, detail="At least one topic must be selected.")

    try:
        questions = generate_mcqs_for_doc(
            record=record,
            topics=clean_topics,
            difficulty=req.difficulty,
            num_questions=req.num_questions,
        )
        return QuizGenerateResponse(questions=questions)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {exc}") from exc
