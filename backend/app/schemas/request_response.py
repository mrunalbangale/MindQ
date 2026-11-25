from typing import List, Literal
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    doc_id: str
    topics: List[str]


class YouTubeIngestRequest(BaseModel):
    url: str = Field(..., min_length=5)


class YouTubeIngestResponse(BaseModel):
    doc_id: str
    title: str
    topics: List[str]


class QuizGenerateRequest(BaseModel):
    doc_id: str = Field(..., min_length=1)
    topics: List[str] = Field(..., min_length=1)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    num_questions: int = Field(..., ge=1, le=30)


class NormalizedQuestion(BaseModel):
    id: str
    question: str
    options: List[str] = Field(..., min_length=4, max_length=4)
    answer_index: int = Field(..., ge=0, le=3)
    topic: str
    explanation: str
    source_ref: str


class QuizGenerateResponse(BaseModel):
    questions: List[NormalizedQuestion]
