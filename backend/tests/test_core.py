from app.services.mcq_generation.mcq_generator import normalize_question, validate_question
from app.services.rag_store import sentence_token_chunk


def test_question_validator():
    valid = {
        "id": "q1",
        "question": "What does virtual memory primarily allow an operating system to do?",
        "options": [
            "Execute processes not completely in physical RAM",
            "Eliminate the CPU cache completely",
            "Store registers on magnetic tape",
            "Disable hardware interrupts permanently",
        ],
        "answer_index": 0,
        "topic": "Virtual Memory",
        "explanation": "Virtual memory decouples logical address space from physical memory size.",
        "source_ref": "Page 2",
    }
    assert validate_question(valid) is True

    # Rejects PDF metadata/stream artifact
    artifact = {**valid, "question": "What does /FlateDecode and endobj do in Skia/PDF?"}
    assert validate_question(artifact) is False

    # Rejects wrong option count or out-of-range answer_index
    assert validate_question({**valid, "options": ["Only", "Three", "Opts"]}) is False
    assert validate_question({**valid, "answer_index": 4}) is False


def test_schema_normalizer():
    legacy = {
        "question": "Which algorithm can suffer from the convoy effect?",
        "options": {
            "A": "First-Come, First-Served (FCFS)",
            "B": "Round Robin",
            "C": "Shortest Remaining Time First",
            "D": "Multilevel Feedback Queue",
        },
        "correct_answer": "A",
        "topics": ["CPU Scheduling"],
        "explanation": "In FCFS, short processes wait behind a long CPU-bound process.",
    }
    norm = normalize_question(legacy, fallback_topic="OS", default_source_ref="03:25")
    assert norm is not None
    assert norm["options"] == [
        "First-Come, First-Served (FCFS)",
        "Round Robin",
        "Shortest Remaining Time First",
        "Multilevel Feedback Queue",
    ]
    assert norm["answer_index"] == 0
    assert norm["topic"] == "CPU Scheduling"
    assert norm["source_ref"] == "03:25"
    assert isinstance(norm["id"], str) and len(norm["id"]) > 0

    # Rejects invalid options dict
    assert normalize_question({"question": "Bad?", "options": {"A": "1"}, "correct_answer": "A"}) is None


def test_sentence_chunker():
    text = (
        "Operating systems manage hardware resources efficiently. "
        "Virtual memory maps logical addresses to physical frames using page tables. "
        "A page fault occurs when a referenced page is not currently in RAM. "
        "Page replacement algorithms such as LRU select a victim frame to evict."
    )
    chunks = sentence_token_chunk(text, max_tokens=20, overlap_sentences=1, tokenizer=None)
    assert len(chunks) >= 2
    assert all(isinstance(c, str) and len(c) > 0 for c in chunks)
    # Overlap preserves boundary continuity
    assert "Virtual memory" in " ".join(chunks)
    assert "LRU" in chunks[-1]
