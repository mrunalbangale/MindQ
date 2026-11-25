import logging
import os
from typing import Optional
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("mindq.llm")


class LLMError(Exception):
    """Raised when the configured LLM provider fails to produce a valid response."""


def get_gemini_api_key() -> str:
    return (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or ""
    ).strip()


def get_gemini_model() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"


def is_llm_configured() -> bool:
    ollama_enabled = os.environ.get("OLLAMA_ENABLED", "false").strip().lower() == "true"
    return bool(get_gemini_api_key()) or ollama_enabled


def call_gemini_api(
    prompt: str,
    json_mode: bool = True,
    timeout: int = 45,
) -> Optional[str]:
    """Call Google Gemini REST API and return the text response, or raise LLMError on failure."""
    api_key = get_gemini_api_key()
    if not api_key:
        raise LLMError("GEMINI_API_KEY is not configured.")

    model_name = get_gemini_model()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload: dict = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3},
    }
    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    except requests.exceptions.Timeout as exc:
        logger.error("Gemini API request timed out after %ss (model=%s)", timeout, model_name)
        raise LLMError(f"Gemini API request timed out after {timeout}s.") from exc
    except requests.exceptions.RequestException as exc:
        logger.error("Gemini API request failed (model=%s): %s", model_name, exc)
        raise LLMError(f"Gemini API request failed: {exc}") from exc

    if response.status_code != 200:
        logger.error(
            "Gemini API non-200 response (model=%s, status=%s): %s",
            model_name,
            response.status_code,
            response.text,
        )
        raise LLMError(f"Gemini API returned HTTP {response.status_code}: {response.text[:300]}")

    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        logger.error("Gemini API returned no candidates: %s", response.text[:300])
        raise LLMError("Gemini API returned no candidates.")

    parts = candidates[0].get("content", {}).get("parts", [])
    text = parts[0].get("text", "") if parts else ""
    if not text.strip():
        raise LLMError("Gemini API returned an empty response.")
    return text


def call_ollama_api(prompt: str, timeout: int = 45) -> str:
    """Call local Ollama API when OLLAMA_ENABLED=true."""
    ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate").strip()
    ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.1").strip()
    payload = {
        "model": ollama_model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.3},
    }
    try:
        response = requests.post(ollama_url, json=payload, timeout=timeout)
    except requests.exceptions.RequestException as exc:
        logger.error("Ollama API request failed: %s", exc)
        raise LLMError(f"Ollama API request failed: {exc}") from exc

    if response.status_code != 200:
        logger.error("Ollama API non-200 response (%s): %s", response.status_code, response.text)
        raise LLMError(f"Ollama API returned HTTP {response.status_code}: {response.text[:300]}")

    text = response.json().get("response", "")
    if not text.strip():
        raise LLMError("Ollama API returned an empty response.")
    return text


def generate_with_llm(prompt: str, json_mode: bool = True, timeout: int = 45) -> str:
    """Try Gemini first; fall back to Ollama only if OLLAMA_ENABLED=true."""
    ollama_enabled = os.environ.get("OLLAMA_ENABLED", "false").strip().lower() == "true"

    if get_gemini_api_key():
        try:
            res = call_gemini_api(prompt, json_mode=json_mode, timeout=timeout)
            if res:
                return res
        except LLMError as exc:
            if not ollama_enabled:
                raise
            logger.warning("Gemini failed, trying Ollama fallback: %s", exc)

    if ollama_enabled:
        return call_ollama_api(prompt, timeout=timeout)

    raise LLMError("No LLM provider is configured. Set GEMINI_API_KEY in the backend environment.")
