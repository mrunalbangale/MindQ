from collections import Counter
import json
import logging
import re
from typing import Any, Dict, List, Tuple

from app.services.llm import LLMError, call_gemini_api

logger = logging.getLogger("mindq.topics")

STOPWORDS = {
    "about", "above", "after", "again", "against", "among", "another", "because",
    "before", "being", "below", "between", "both", "could", "during", "each",
    "either", "every", "first", "found", "from", "further", "given", "having",
    "however", "into", "itself", "large", "later", "least", "might", "more",
    "most", "much", "must", "neither", "never", "often", "other", "others",
    "otherwise", "should", "since", "small", "some", "someone", "something",
    "still", "such", "than", "that", "their", "them", "then", "there", "these",
    "they", "thing", "things", "this", "those", "though", "three", "through",
    "thus", "under", "until", "using", "very", "what", "when", "where", "which",
    "while", "with", "within", "without", "would", "your",
}

# Blocklist of PDF structure, metadata, and rendering artifact tokens
ARTIFACT_BLOCKLIST = {
    "title", "producer", "skia", "google", "docs", "renderer", "endobj", "obj",
    "xobject", "font", "type", "encoding", "identity", "metadata", "xref", "trailer",
    "startxref", "normal", "creationdate", "moddate", "author", "creator", "subject",
    "keywords", "breakdown", "technical", "today", "welcome", "overview", "introduction",
    "page", "pages", "catalog", "stream", "endstream", "pdf", "unnamed", "untitled",
    "flatedecode", "ascii85decode", "asciihexdecode", "lzwdecode", "runlengthdecode",
    "dctdecode", "ccittfaxdecode", "jpxdecode", "filter", "decodeparms", "length"
}

# Regex patterns matching low-level PDF stream syntax, object structures, and metadata tags
PDF_ARTIFACT_PATTERNS = [
    r'/(ASCII85Decode|ASCIIHexDecode|FlateDecode|LZWDecode|RunLengthDecode|DCTDecode|CCITTFaxDecode|JPXDecode|Filter|DecodeParms|Length|MediaBox|CropBox|ProcSet|ExtGState)\b',
    r'/(Title|Producer|Creator|Author|Subject|Keywords|CreationDate|ModDate|Type|Font|Encoding|Catalog|Pages)\s+.*',
    r'\b(endobj|xobject|startxref|xref|trailer|obj|endstream|stream|Skia/PDF|Google Docs|Renderer|Normal\.dotm)\b',
    r'\b\d+\s+\d+\s+obj\b',
    r'\b\d+\s+\d+\s+R\b',
    r'/Type\s+/(Page|Catalog|Font|XObject)\b',
    r'According to the PDF stream metadata',
    r'PDF stream metadata',
    r'PDF object metadata'
]


def contains_pdf_artifacts(text: str) -> bool:
    """Returns True if the text contains obvious raw PDF internal streams, object syntax, or metadata artifacts."""
    if not text or not isinstance(text, str):
        return False
    for pat in PDF_ARTIFACT_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def clean_pdf_raw_text(raw_text: str) -> str:
    """
    Strips raw PDF streams, decoders, object syntax, and renderer metadata
    while preserving genuine human-readable educational text.
    """
    if not raw_text:
        return ""

    text = raw_text
    # 1. Remove PDF object headers and metadata key-value patterns
    text = re.sub(r'/(Title|Producer|Creator|Author|Subject|Keywords|CreationDate|ModDate|Type|Font|Encoding|MediaBox|CropBox|ProcSet|ExtGState)\s+.*', '', text, flags=re.IGNORECASE)
    # 2. Remove PDF decoders & filter syntax
    text = re.sub(r'/(ASCII85Decode|ASCIIHexDecode|FlateDecode|LZWDecode|RunLengthDecode|DCTDecode|CCITTFaxDecode|JPXDecode|Filter|DecodeParms|Length)\b', ' ', text, flags=re.IGNORECASE)
    # 3. Remove PDF object stream boundaries and structural keywords
    text = re.sub(r'\b(endobj|xobject|startxref|xref|trailer|obj|endstream|stream|Skia/PDF|Google Docs|Renderer|Normal\.dotm)\b', ' ', text, flags=re.IGNORECASE)
    # 4. Remove PDF object references like "12 0 R" or "5 0 obj"
    text = re.sub(r'\b\d+\s+\d+\s+(obj|R)\b', ' ', text)

    lines = []
    for line in text.splitlines():
        line_str = line.strip()
        # Filter out lines that look like pure PDF header/footer metadata, isolated numbers, or decoder tags
        if not line_str or line_str.isdigit() or len(line_str) < 3:
            continue
        if re.match(r'^(page|\d+|\s*|PDF-\d\.\d)$', line_str, re.IGNORECASE):
            continue
        if contains_pdf_artifacts(line_str):
            continue
        lines.append(line_str)
    return "\n".join(lines)


def sanitize_educational_text(text: str) -> str:
    """Alias/wrapper to return clean educational text."""
    return clean_pdf_raw_text(text)


def is_valid_educational_topic(topic: str) -> bool:
    if not topic or not isinstance(topic, str):
        return False
    
    clean_t = topic.strip()
    words = clean_t.lower().split()
    
    if len(clean_t) < 3 or len(clean_t) > 40 or len(words) > 4:
        return False
        
    # Strictly reject any topic that contains blocklisted artifact tokens
    for w in words:
        if w in ARTIFACT_BLOCKLIST:
            return False
            
    # Require alphabetic characters
    if not re.search(r'[a-zA-Z]', clean_t):
        return False
        
    return True


def extract_topics_with_gemini(clean_text: str) -> List[str]:
    sample_text = clean_text[:6000] if len(clean_text) > 6000 else clean_text
    prompt = f"""You are MindQ's Educational Topic Extractor.
Extract 5 to 10 major, genuine educational topics and concepts from the following study content.

Guidelines:
- Topics must be real educational subjects, chapters, or concepts (1 to 4 words each).
- STRICTLY EXCLUDE PDF metadata, rendering engine names (Skia, Google Docs, Producer, Renderer, Endobj, Title, Author), filenames, or generic filler words.
- Return ONLY a JSON array of strings.

Study Content:
\"\"\"
{sample_text}
\"\"\"
"""
    try:
        res = call_gemini_api(prompt, json_mode=True, timeout=30)
        if not res:
            return []
        raw = res.strip()
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start != -1 and end > start:
            raw = raw[start:end]
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            valid_topics = []
            for t in parsed:
                if isinstance(t, str) and is_valid_educational_topic(t):
                    valid_topics.append(t.strip().title())
            return valid_topics
    except LLMError as exc:
        logger.warning("Gemini topic extraction unavailable, using keyword fallback: %s", exc)
    except Exception as exc:
        logger.warning("Gemini topic extraction parse error: %s", exc)
    return []


def fallback_extract_topics(clean_text: str, max_topics: int = 8) -> List[str]:
    """Keyword-frequency topic extractor over cleaned text (no spaCy)."""
    if not clean_text:
        return []

    words = re.findall(r"\b[A-Za-z][A-Za-z0-9-]{3,22}\b", clean_text)
    filtered = []
    for word in words:
        low = word.lower()
        if low in STOPWORDS or low in ARTIFACT_BLOCKLIST:
            continue
        candidate = word.title()
        if is_valid_educational_topic(candidate):
            filtered.append(candidate)

    counts = Counter(filtered)
    return [w for w, _ in counts.most_common(max_topics)]


def extract_pages_from_pdf(pdf_path: str) -> List[Tuple[int, str]]:
    """Return list of (1-based page_number, cleaned_page_text) from a PDF file."""
    import fitz

    pages: List[Tuple[int, str]] = []
    with fitz.open(pdf_path) as doc:
        for idx, page in enumerate(doc, start=1):
            cleaned = clean_pdf_raw_text(page.get_text("text") or "")
            if cleaned.strip():
                pages.append((idx, cleaned))
    return pages


def extract_text_from_pdf(pdf_path: str) -> str:
    pages = extract_pages_from_pdf(pdf_path)
    return "\n".join(text for _, text in pages)


def extract_topics_from_pdf_text(text: str) -> Dict[str, Any]:
    clean_text = clean_pdf_raw_text(text)
    if not clean_text.strip():
        return {"topics": []}

    gemini_topics = extract_topics_with_gemini(clean_text)
    final_topics: List[str] = []
    seen = set()

    for t in gemini_topics:
        norm = t.lower()
        if norm not in seen and is_valid_educational_topic(t):
            seen.add(norm)
            final_topics.append(t)

    if len(final_topics) < 3:
        for ft in fallback_extract_topics(clean_text, max_topics=8):
            norm = ft.lower()
            if norm not in seen and is_valid_educational_topic(ft):
                seen.add(norm)
                final_topics.append(ft)

    return {"topics": final_topics[:10]}
