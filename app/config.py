"""Central configuration: paths and environment variables."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
PANELS_DIR = STATIC_DIR / "panels"
EXPORTS_DIR = STATIC_DIR / "exports"
FONTS_DIR = STATIC_DIR / "fonts"

for _d in (PANELS_DIR, EXPORTS_DIR, FONTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
HF_API_KEY = os.getenv("HF_API_KEY", "").strip()

GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-3.8-flash").strip()
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-3.8-flash").strip()

GEMINI_FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.7-flash,gemini-3.5-flash").split(",")
    if m.strip()
]

SD_MODEL_ID = os.getenv(
    "SD_MODEL_ID", "stable-diffusion-v1-5/stable-diffusion-v1-5"
).strip()
SD_STEPS = int(os.getenv("SD_STEPS", "25"))
USE_PLACEHOLDER_IMAGES = os.getenv("USE_PLACEHOLDER_IMAGES", "false").strip().lower() in (
    "1",
    "true",
    "yes",
)


def to_web_url(path) -> str:
    """Convert a file path inside /static into a URL such as /static/panels/x.png."""
    rel = Path(path).resolve().relative_to(STATIC_DIR.resolve())
    return "/static/" + rel.as_posix()
