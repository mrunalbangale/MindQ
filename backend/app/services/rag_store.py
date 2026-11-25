from collections import OrderedDict
from dataclasses import dataclass
import re
import threading
from typing import Dict, List, Optional, Tuple
import uuid

import faiss
import numpy as np

from app.services.topic_extracting.topic_extractor import clean_pdf_raw_text, contains_pdf_artifacts

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MAX_STORED_DOCS = 5
MAX_CHUNK_TOKENS = 240
OVERLAP_SENTENCES = 1
SENTENCE_SPLIT_REGEX = r"(?<=[.!?])\s+"

_model_lock = threading.Lock()
_embed_model = None
_docs_lock = threading.Lock()
_DOC_STORE: "OrderedDict[str, DocumentRecord]" = OrderedDict()


@dataclass
class TextChunk:
    text: str
    source_ref: str


@dataclass
class DocumentRecord:
    doc_id: str
    source_type: str  # "pdf" or "youtube"
    title: str
    topics: List[str]
    chunks: List[TextChunk]
    index: Optional[faiss.IndexFlatL2]


def get_embed_model():
    """Load SentenceTransformer all-MiniLM-L6-v2 once, lazily."""
    global _embed_model
    if _embed_model is None:
        with _model_lock:
            if _embed_model is None:
                from sentence_transformers import SentenceTransformer

                _embed_model = SentenceTransformer(EMBED_MODEL_NAME)
    return _embed_model


def split_into_sentences(text: str) -> List[str]:
    normalized = text.replace("\r", " ").replace("\n", " ")
    raw_sentences = re.split(SENTENCE_SPLIT_REGEX, normalized)
    return [s.strip() for s in raw_sentences if s and s.strip()]


def preprocess_text(text: str) -> str:
    """Clean OCR/PDF artifacts and normalize whitespace."""
    cleaned = clean_pdf_raw_text(text)
    cleaned = re.sub(r"[^\x00-\x7F]+", " ", cleaned)
    cleaned = re.sub(r"(\w)-\n(\w)", r"\1\2", cleaned)
    cleaned = re.sub(r"\n", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def sentence_token_chunk(
    text: str,
    max_tokens: int = MAX_CHUNK_TOKENS,
    overlap_sentences: int = OVERLAP_SENTENCES,
    tokenizer=None,
) -> List[str]:
    """
    Split text into overlapping sentence-aligned chunks bounded by max_tokens.
    Uses the SentenceTransformer tokenizer when available, with a word-count fallback.
    """
    sentences = split_into_sentences(text)
    if not sentences:
        return []

    if tokenizer is None:
        try:
            tokenizer = get_embed_model().tokenizer
        except Exception:
            tokenizer = None

    if tokenizer is not None:
        sent_token_ids = [tokenizer.encode(s, add_special_tokens=False) for s in sentences]
        sent_token_lens = [len(ids) for ids in sent_token_ids]
    else:
        sent_token_ids = None
        sent_token_lens = [max(1, len(s.split())) for s in sentences]

    chunks: List[str] = []
    n = len(sentences)
    i = 0

    while i < n:
        curr_indices: List[int] = []
        curr_len = 0
        j = i

        while j < n and (curr_len + sent_token_lens[j] <= max_tokens):
            curr_indices.append(j)
            curr_len += sent_token_lens[j]
            j += 1

        if j == i:
            if sent_token_ids is not None and tokenizer is not None:
                long_ids = sent_token_ids[i]
                for start_idx in range(0, len(long_ids), max_tokens):
                    slice_text = tokenizer.decode(
                        long_ids[start_idx : start_idx + max_tokens],
                        clean_up_tokenization_spaces=True,
                    ).strip()
                    if slice_text:
                        chunks.append(slice_text)
            else:
                words = sentences[i].split()
                for start_idx in range(0, len(words), max_tokens):
                    slice_text = " ".join(words[start_idx : start_idx + max_tokens]).strip()
                    if slice_text:
                        chunks.append(slice_text)
            i += 1
            continue

        chunk_text = " ".join(sentences[idx] for idx in curr_indices).strip()
        if chunk_text:
            chunks.append(chunk_text)

        if overlap_sentences <= 0:
            i = j
        else:
            next_start = j - overlap_sentences
            i = i + 1 if next_start <= i else next_start

    return chunks


def is_valid_educational_chunk(chunk: str) -> bool:
    if not chunk or not isinstance(chunk, str):
        return False
    if len(chunk.strip()) < 15:
        return False
    if contains_pdf_artifacts(chunk):
        return False
    return True


def chunk_pdf_pages(pages: List[Tuple[int, str]]) -> List[TextChunk]:
    """Clean and chunk page-indexed PDF text, preserving page source_ref."""
    result: List[TextChunk] = []
    for page_num, raw_page_text in pages:
        cleaned = preprocess_text(raw_page_text)
        if not cleaned:
            continue
        for chunk_text in sentence_token_chunk(cleaned):
            if is_valid_educational_chunk(chunk_text):
                result.append(TextChunk(text=chunk_text, source_ref=f"Page {page_num}"))
    return result


def build_and_store_document(
    source_type: str,
    title: str,
    topics: List[str],
    chunks: List[TextChunk],
) -> DocumentRecord:
    """Build an in-memory FAISS index for chunks and cache up to MAX_STORED_DOCS documents."""
    doc_id = uuid.uuid4().hex[:12]
    index = None

    if chunks:
        model = get_embed_model()
        embeddings = model.encode([c.text for c in chunks], show_progress_bar=False)
        arr = np.asarray(embeddings, dtype="float32")
        if arr.ndim == 2 and arr.shape[0] > 0:
            index = faiss.IndexFlatL2(arr.shape[1])
            index.add(arr)

    record = DocumentRecord(
        doc_id=doc_id,
        source_type=source_type,
        title=title,
        topics=topics,
        chunks=chunks,
        index=index,
    )

    with _docs_lock:
        _DOC_STORE[doc_id] = record
        _DOC_STORE.move_to_end(doc_id)
        while len(_DOC_STORE) > MAX_STORED_DOCS:
            _DOC_STORE.popitem(last=False)

    return record


def get_document(doc_id: str) -> Optional[DocumentRecord]:
    with _docs_lock:
        record = _DOC_STORE.get(doc_id)
        if record is not None:
            _DOC_STORE.move_to_end(doc_id)
        return record


def retrieve_chunks_for_topic(
    record: DocumentRecord,
    topic: str,
    difficulty: str,
    k: int = 4,
) -> List[TextChunk]:
    """Retrieve the top-k relevant chunks for a topic from the document's in-memory FAISS index."""
    if not record.chunks:
        return []

    if record.index is None or len(record.chunks) <= k:
        return record.chunks[:k]

    model = get_embed_model()
    query = f"Topic: {topic}. Difficulty: {difficulty}."
    query_vec = np.asarray(model.encode([query], show_progress_bar=False), dtype="float32")
    top_k = min(k, len(record.chunks))
    _, indices = record.index.search(query_vec, top_k)

    selected: List[TextChunk] = []
    seen_idx = set()
    for idx in indices[0]:
        if 0 <= idx < len(record.chunks) and idx not in seen_idx:
            seen_idx.add(int(idx))
            selected.append(record.chunks[int(idx)])
    return selected
