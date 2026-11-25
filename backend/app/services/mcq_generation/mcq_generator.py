import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid

from app.services.llm import LLMError, generate_with_llm
from app.services.rag_store import DocumentRecord, TextChunk, retrieve_chunks_for_topic
from app.services.topic_extracting.topic_extractor import contains_pdf_artifacts

logger = logging.getLogger("mindq.mcq")

MAX_RETRIES = 2
LLM_TIMEOUT_SECONDS = 45
CHUNKS_PER_TOPIC = {"easy": 3, "medium": 4, "hard": 5}
LETTER_TO_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3}


def _extract_json_array(raw_text: str) -> Optional[List[Any]]:
    if not raw_text:
        return None
    text = raw_text.strip()
    start = text.find("[")
    end = text.rfind("]") + 1
    if start == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start:end])
        return parsed if isinstance(parsed, list) else None
    except json.JSONDecodeError:
        return None


def _is_pdf_spec_topic(topic: str) -> bool:
    low = topic.lower()
    return any(k in low for k in ("pdf specification", "pdf file format", "pdf architecture"))


def normalize_question(
    raw: Any,
    fallback_topic: str = "General",
    default_source_ref: str = "",
) -> Optional[Dict[str, Any]]:
    """
    Normalize a raw LLM question dict into:
    {id, question, options: string[4], answer_index: int(0..3), topic, explanation, source_ref}.
    Returns None if required structure cannot be satisfied.
    """
    if not isinstance(raw, dict):
        return None

    question_text = str(raw.get("question", "")).strip()
    if not question_text:
        return None

    # Normalize options to list of 4 non-empty strings
    raw_opts = raw.get("options")
    options: List[str] = []
    if isinstance(raw_opts, list):
        options = [str(opt).strip() for opt in raw_opts if str(opt).strip()]
    elif isinstance(raw_opts, dict):
        for letter in ("A", "B", "C", "D"):
            val = raw_opts.get(letter)
            if val is None:
                val = raw_opts.get(letter.lower())
            if val is not None and str(val).strip():
                options.append(str(val).strip())

    if len(options) != 4 or len({o.lower() for o in options}) != 4:
        return None

    # Normalize answer_index (0..3)
    answer_index: Optional[int] = None
    if isinstance(raw.get("answer_index"), int) and not isinstance(raw.get("answer_index"), bool):
        idx = raw["answer_index"]
        if 0 <= idx <= 3:
            answer_index = idx
    elif isinstance(raw.get("correctAnswer"), int) and not isinstance(raw.get("correctAnswer"), bool):
        idx = raw["correctAnswer"]
        if 0 <= idx <= 3:
            answer_index = idx
    else:
        ans_raw = raw.get("correct_answer", raw.get("answer_index"))
        if isinstance(ans_raw, str):
            cleaned = ans_raw.strip().upper()
            if cleaned in LETTER_TO_INDEX:
                answer_index = LETTER_TO_INDEX[cleaned]
            elif cleaned.isdigit() and 0 <= int(cleaned) <= 3:
                answer_index = int(cleaned)
            else:
                for i, opt in enumerate(options):
                    if opt.lower() == ans_raw.strip().lower():
                        answer_index = i
                        break

    if answer_index is None:
        return None

    raw_topic = raw.get("topic")
    if not raw_topic:
        raw_topics = raw.get("topics")
        if isinstance(raw_topics, list) and raw_topics:
            raw_topic = raw_topics[0]
        elif isinstance(raw_topics, str):
            raw_topic = raw_topics
    topic = str(raw_topic or fallback_topic).strip() or fallback_topic

    explanation = str(raw.get("explanation", "")).strip()
    if not explanation:
        explanation = f"Option {['A', 'B', 'C', 'D'][answer_index]} is correct based on the study material."

    source_ref = str(raw.get("source_ref", default_source_ref)).strip() or default_source_ref

    q_id = str(raw.get("id", "")).strip() or f"q_{uuid.uuid4().hex[:8]}"

    return {
        "id": q_id,
        "question": question_text,
        "options": options,
        "answer_index": answer_index,
        "topic": topic,
        "explanation": explanation,
        "source_ref": source_ref,
    }


def validate_question(q: Any) -> bool:
    """Validate a normalized question dict: 4 distinct options, valid answer_index, no PDF artifacts."""
    if not isinstance(q, dict):
        return False

    question = q.get("question")
    options = q.get("options")
    answer_index = q.get("answer_index")
    topic = str(q.get("topic", ""))
    explanation = q.get("explanation")

    if not isinstance(question, str) or len(question.strip()) < 8:
        return False
    if not isinstance(options, list) or len(options) != 4:
        return False
    if any(not isinstance(opt, str) or not opt.strip() for opt in options):
        return False
    if len({opt.strip().lower() for opt in options}) != 4:
        return False
    if not isinstance(answer_index, int) or isinstance(answer_index, bool) or not (0 <= answer_index <= 3):
        return False
    if not isinstance(explanation, str) or not explanation.strip():
        return False

    if not _is_pdf_spec_topic(topic):
        blob = " ".join([question, *options, explanation])
        if contains_pdf_artifacts(blob):
            return False

    return True


def _build_multi_topic_context(
    record: DocumentRecord,
    topics: List[str],
    difficulty: str,
) -> Tuple[str, str]:
    k = CHUNKS_PER_TOPIC.get(difficulty.lower(), 4)
    sections: List[str] = []
    seen_texts = set()
    default_ref = record.chunks[0].source_ref if record.chunks else "Source"

    for topic in topics:
        chunks: List[TextChunk] = retrieve_chunks_for_topic(record, topic, difficulty, k=k)
        topic_lines: List[str] = []
        for chunk in chunks:
            sig = chunk.text[:120]
            if sig in seen_texts:
                continue
            seen_texts.add(sig)
            topic_lines.append(f"[{chunk.source_ref}] {chunk.text}")

        if not topic_lines and record.chunks:
            fallback_chunk = record.chunks[0]
            topic_lines.append(f"[{fallback_chunk.source_ref}] {fallback_chunk.text}")

        sections.append(f"### TOPIC: {topic}\n" + "\n".join(topic_lines))

    return "\n\n".join(sections), default_ref


def _build_generation_prompt(
    context_text: str,
    topics: List[str],
    difficulty: str,
    count: int,
    existing_questions: List[str],
) -> str:
    topics_str = ", ".join(topics)
    avoid_block = ""
    if existing_questions:
        listed = "\n".join(f"- {q}" for q in existing_questions[:20])
        avoid_block = f"\nDo NOT repeat or paraphrase these already generated questions:\n{listed}\n"

    return f"""You are MindQ's expert educational MCQ generator.
Generate EXACTLY {count} multiple-choice questions grounded strictly in the provided source excerpts.

Target Topics: {topics_str}
Difficulty: {difficulty}
{avoid_block}
Source Excerpts (each excerpt starts with its source reference in brackets, e.g. [Page 2] or [03:25]):
\"\"\"
{context_text}
\"\"\"

Rules:
1. Cover all target topics as evenly as possible.
2. Each question MUST have:
   - "question": clear, unambiguous educational question
   - "options": array of EXACTLY 4 distinct answer strings
   - "answer_index": integer 0, 1, 2, or 3 indicating the single correct option
   - "topic": one of [{topics_str}]
   - "explanation": concise explanation of why the correct option is right and others are wrong
   - "source_ref": exact source tag from the excerpt used (e.g., "Page 2" or "03:25")
3. STRICTLY FORBIDDEN: any mention of PDF internals, stream decoders (/FlateDecode), object tags (endobj, xref), or renderer metadata (Skia, Google Docs, Producer).
4. Return ONLY a valid JSON array of {count} objects. No markdown fences or extra prose.
"""


def generate_mcqs_for_doc(
    record: DocumentRecord,
    topics: List[str],
    difficulty: str,
    num_questions: int,
) -> List[Dict[str, Any]]:
    """
    Generate `num_questions` validated, normalized MCQs using ONE LLM call covering all topics,
    retrying up to MAX_RETRIES times only for the missing count.
    """
    clean_topics = [t.strip() for t in topics if t and t.strip()]
    if not clean_topics:
        clean_topics = record.topics[:4] or ["General"]

    context_text, default_ref = _build_multi_topic_context(record, clean_topics, difficulty)

    collected: List[Dict[str, Any]] = []
    seen_questions = set()
    last_error: Optional[Exception] = None

    for attempt in range(MAX_RETRIES + 1):
        missing = num_questions - len(collected)
        if missing <= 0:
            break

        prompt = _build_generation_prompt(
            context_text=context_text,
            topics=clean_topics,
            difficulty=difficulty,
            count=missing,
            existing_questions=[q["question"] for q in collected],
        )

        try:
            raw_output = generate_with_llm(prompt, json_mode=True, timeout=LLM_TIMEOUT_SECONDS)
        except LLMError as exc:
            last_error = exc
            logger.warning("Attempt %d/%d LLM call failed: %s", attempt + 1, MAX_RETRIES + 1, exc)
            continue

        parsed = _extract_json_array(raw_output)
        if not parsed:
            logger.warning("Attempt %d/%d returned non-JSON array", attempt + 1, MAX_RETRIES + 1)
            continue

        for idx, item in enumerate(parsed):
            fallback_topic = clean_topics[idx % len(clean_topics)]
            norm = normalize_question(item, fallback_topic=fallback_topic, default_source_ref=default_ref)
            if not norm or not validate_question(norm):
                continue
            q_key = re.sub(r"\s+", " ", norm["question"].lower()).strip()
            if q_key in seen_questions:
                continue
            seen_questions.add(q_key)
            collected.append(norm)
            if len(collected) >= num_questions:
                break

    if not collected:
        detail = str(last_error) if last_error else "LLM failed to return valid questions."
        raise LLMError(detail)

    return collected[:num_questions]
