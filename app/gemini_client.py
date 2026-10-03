"""Thin wrapper around the Google Gemini SDK (google-genai) with retries and model fallback."""
import time

from google import genai
from google.genai import types

from app import config

_client = None

# Errors that are temporary: wait and retry the same model.
TRANSIENT_MARKERS = (
    "503", "500", "504", "429", "unavailable", "resource_exhausted",
    "overloaded", "high demand", "timed out", "timeout", "deadline",
)


def get_client():
    global _client
    if _client is None:
        if not config.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


def _is_transient(exc: Exception) -> bool:
    text = str(exc).lower()
    # A daily quota will not recover in seconds: skip to the next model instead of waiting.
    if "perday" in text or "per day" in text or "daily" in text:
        return False
    return any(marker in text for marker in TRANSIENT_MARKERS)


def generate_text(model: str, prompt: str, json_mode: bool = False, retries: int = 4) -> str:
    """Call Gemini. Retries busy-server errors with backoff, then tries fallback models."""
    client = get_client()
    cfg = types.GenerateContentConfig(response_mime_type="application/json") if json_mode else None
    models = [model] + [m for m in config.GEMINI_FALLBACK_MODELS if m != model]

    last_error = None
    for name in models:
        for attempt in range(1, retries + 1):
            try:
                response = client.models.generate_content(model=name, contents=prompt, config=cfg)
                text = (response.text or "").strip()
                if not text:
                    raise RuntimeError("Gemini returned an empty response.")
                return text
            except Exception as exc:
                last_error = exc
                print(f"[Gemini] {name} attempt {attempt}/{retries} failed: {exc}")
                if not _is_transient(exc):
                    break  # e.g. 404 model not found -> go straight to the next model
                if attempt < retries:
                    time.sleep(min(3 * 2 ** (attempt - 1), 30))  # 3s, 6s, 12s
        print(f"[Gemini] giving up on {name}, trying next model (if any)...")
    raise RuntimeError(f"Gemini request failed on all models ({', '.join(models)}): {last_error}") from last_error
