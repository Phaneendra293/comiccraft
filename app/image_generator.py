"""Stable Diffusion (Hugging Face Diffusers) panel image generation."""
import re
import textwrap
import threading
import uuid
from pathlib import Path

from PIL import Image, ImageDraw

from app import config

STYLE_KEYWORDS = {
    "anime": "anime style, vibrant colors, clean line art, detailed background",
    "pixel art": "pixel art, 16-bit retro game style, limited color palette",
    "comic book": "classic comic book illustration, bold ink outlines, halftone shading, vivid colors",
    "realistic": "highly detailed realistic digital painting, cinematic lighting",
}
BASE_SUFFIX = "masterpiece, best quality, highly detailed"
NEGATIVE_PROMPT = "text, letters, watermark, logo, signature, blurry, low quality, deformed, extra limbs, bad anatomy"

_pipe = None
_lock = threading.Lock()  # one image at a time; the pipeline is not thread-safe


def sanitize_filename(prompt: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", prompt).strip("_")[:40] or "panel"
    return f"{slug}_{uuid.uuid4().hex[:8]}.png"


def _load_pipeline():
    global _pipe
    if _pipe is not None:
        return _pipe

    import torch
    from diffusers import StableDiffusionPipeline

    if torch.cuda.is_available():
        device, dtype = "cuda", torch.float16
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        device, dtype = "mps", torch.float32
    else:
        device, dtype = "cpu", torch.float32

    print(f"[SD] Loading {config.SD_MODEL_ID} on {device} (first run downloads ~4 GB)...")
    pipe = StableDiffusionPipeline.from_pretrained(
        config.SD_MODEL_ID,
        torch_dtype=dtype,
        token=config.HF_API_KEY or None,
    )
    pipe = pipe.to(device)
    pipe.enable_attention_slicing()
    _pipe = pipe
    print("[SD] Model ready.")
    return _pipe


def _placeholder(prompt: str, path: Path) -> None:
    """Draw a simple gradient panel so the app works without a GPU/model."""
    img = Image.new("RGB", (512, 512))
    draw = ImageDraw.Draw(img)
    for y in range(512):
        draw.line([(0, y), (512, y)], fill=(40 + y // 8, 70 + y // 10, 140 - y // 8))
    draw.rectangle([8, 8, 503, 503], outline=(255, 210, 63), width=6)
    text = "PLACEHOLDER PANEL\n\n" + "\n".join(textwrap.wrap(prompt, 36)[:12])
    draw.multiline_text((28, 28), text, fill=(255, 255, 255), spacing=6)
    img.save(path)


def generate_image(prompt: str, filename: str = None, style: str = None) -> str:
    """Generate one panel image, save it in static/panels and return the file path."""
    if filename:
        filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
        if not filename.lower().endswith(".png"):
            filename += ".png"
    else:
        filename = sanitize_filename(prompt)
    path = config.PANELS_DIR / filename

    if config.USE_PLACEHOLDER_IMAGES:
        _placeholder(prompt, path)
        return str(path)

    style_words = STYLE_KEYWORDS.get((style or "").lower(), "")
    full_prompt = ", ".join(part for part in (prompt, style_words, BASE_SUFFIX) if part)

    with _lock:
        pipe = _load_pipeline()
        result = pipe(
            full_prompt,
            negative_prompt=NEGATIVE_PROMPT,
            num_inference_steps=config.SD_STEPS,
            guidance_scale=7.5,
            height=512,
            width=512,
        )
    result.images[0].save(path)
    return str(path)
