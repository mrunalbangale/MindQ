import os
import tempfile
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.request_response import DocumentUploadResponse
from app.services.rag_store import build_and_store_document, chunk_pdf_pages
from app.services.topic_extracting.topic_extractor import (
    extract_pages_from_pdf,
    extract_topics_from_pdf_text,
)

router = APIRouter(tags=["documents"])


@router.post("/documents", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename or "document.pdf"
    if not filename.lower().endswith(".pdf") and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    suffix = os.path.splitext(filename)[1] or ".pdf"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = tmp.name
            tmp.write(await file.read())

        pages = extract_pages_from_pdf(temp_path)
        full_text = "\n".join(text for _, text in pages)
        if not full_text.strip():
            raise HTTPException(
                status_code=422,
                detail="No readable text could be extracted from this PDF.",
            )

        topics_result = extract_topics_from_pdf_text(full_text)
        topics = topics_result.get("topics", [])
        if not topics:
            topics = ["Core Concepts"]

        chunks = chunk_pdf_pages(pages)
        record = build_and_store_document(
            source_type="pdf",
            title=filename,
            topics=topics,
            chunks=chunks,
        )
        return DocumentUploadResponse(doc_id=record.doc_id, topics=record.topics)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {exc}") from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
