import html
import re
from typing import List, Optional
from urllib.parse import parse_qs, urlparse

from fastapi import APIRouter, HTTPException
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    InvalidVideoId,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from app.schemas.request_response import YouTubeIngestRequest, YouTubeIngestResponse
from app.services.rag_store import TextChunk, build_and_store_document
from app.services.topic_extracting.topic_extractor import extract_topics_from_pdf_text

router = APIRouter(prefix="/youtube", tags=["youtube"])

CHUNK_DURATION_SECONDS = 40.0


def extract_video_id(url: str) -> Optional[str]:
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if "youtu.be" in host:
        vid = parsed.path.strip("/").split("/")[0]
        return vid if re.fullmatch(r"[0-9A-Za-z_-]{11}", vid) else None

    if "youtube.com" in host or "youtube-nocookie.com" in host:
        qs = parse_qs(parsed.query)
        if "v" in qs and qs["v"]:
            vid = qs["v"][0]
            return vid if re.fullmatch(r"[0-9A-Za-z_-]{11}", vid) else None
        parts = [p for p in parsed.path.split("/") if p]
        for prefix in ("embed", "shorts", "live", "v"):
            if len(parts) >= 2 and parts[0] == prefix:
                vid = parts[1]
                return vid if re.fullmatch(r"[0-9A-Za-z_-]{11}", vid) else None

    match = re.search(r"(?:v=|youtu\.be/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None


def format_timestamp(seconds: float) -> str:
    total_sec = max(0, int(seconds))
    hours, rem = divmod(total_sec, 3600)
    mins, secs = divmod(rem, 60)
    if hours > 0:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def group_transcript_segments(segments: list, window_seconds: float = CHUNK_DURATION_SECONDS) -> List[TextChunk]:
    """Group transcript snippets into ~40s chunks keeping start timestamps as source_ref."""
    chunks: List[TextChunk] = []
    current_texts: List[str] = []
    window_start: Optional[float] = None

    for seg in segments:
        text = (getattr(seg, "text", None) if not isinstance(seg, dict) else seg.get("text")) or ""
        start = getattr(seg, "start", None) if not isinstance(seg, dict) else seg.get("start")
        start_val = float(start) if start is not None else 0.0
        cleaned = re.sub(r"\s+", " ", text).strip()
        if not cleaned:
            continue

        if window_start is None:
            window_start = start_val

        current_texts.append(cleaned)
        if start_val - window_start >= window_seconds:
            chunks.append(
                TextChunk(
                    text=" ".join(current_texts),
                    source_ref=format_timestamp(window_start),
                )
            )
            current_texts = []
            window_start = None

    if current_texts and window_start is not None:
        chunks.append(
            TextChunk(
                text=" ".join(current_texts),
                source_ref=format_timestamp(window_start),
            )
        )
    return chunks


def fetch_video_title(video_id: str) -> str:
    try:
        resp = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"},
            timeout=5,
        )
        if resp.status_code == 200:
            title = resp.json().get("title")
            if title:
                return html.unescape(str(title)).strip()
    except Exception:
        pass
    return f"YouTube Video ({video_id})"


def _fetch_transcript_snippets(video_id: str) -> list:
    api = YouTubeTranscriptApi()
    try:
        return list(api.fetch(video_id, languages=("en", "en-US", "en-GB")))
    except NoTranscriptFound:
        transcript_list = api.list(video_id)
        for transcript in transcript_list:
            return list(transcript.fetch())
        raise


@router.post("/ingest", response_model=YouTubeIngestResponse)
def ingest_youtube(req: YouTubeIngestRequest):
    video_id = extract_video_id(req.url)
    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL. Please paste a valid youtube.com or youtu.be link.",
        )

    try:
        snippets = _fetch_transcript_snippets(video_id)
    except (TranscriptsDisabled, NoTranscriptFound):
        raise HTTPException(
            status_code=422,
            detail="No captions or transcript are available for this YouTube video.",
        )
    except (VideoUnavailable, InvalidVideoId):
        raise HTTPException(
            status_code=404,
            detail="This YouTube video is unavailable or does not exist.",
        )
    except CouldNotRetrieveTranscript as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not retrieve transcript from YouTube: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch YouTube transcript: {exc}",
        )

    chunks = group_transcript_segments(snippets)
    if not chunks:
        raise HTTPException(
            status_code=422,
            detail="Transcript was empty for this YouTube video.",
        )

    full_text = "\n".join(c.text for c in chunks)
    topics = extract_topics_from_pdf_text(full_text).get("topics", [])
    if not topics:
        topics = ["Core Concepts"]

    title = fetch_video_title(video_id)
    record = build_and_store_document(
        source_type="youtube",
        title=title,
        topics=topics,
        chunks=chunks,
    )
    return YouTubeIngestResponse(doc_id=record.doc_id, title=record.title, topics=record.topics)
