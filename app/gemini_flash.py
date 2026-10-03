"""Gemini Flash: fast, structured 5-panel comic outline (JSON)."""
import json
import re

from app import config
from app.gemini_client import generate_text

REQUIRED_KEYS = ("panel", "title", "scene_description", "image_prompt")
NUM_PANELS = 5


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _validate(data) -> list:
    if isinstance(data, dict):  # model wrapped the list in an object
        for value in data.values():
            if isinstance(value, list):
                data = value
                break
    if not isinstance(data, list) or not data:
        raise ValueError("Gemini response is not a non-empty list.")
    panels = []
    for item in data[:NUM_PANELS]:
        if not isinstance(item, dict) or not all(k in item for k in REQUIRED_KEYS):
            raise ValueError(f"Invalid panel format or missing keys: {item}")
        panels.append(
            {
                "panel": len(panels) + 1,
                "title": str(item["title"]).strip(),
                "scene_description": str(item["scene_description"]).strip(),
                "image_prompt": str(item["image_prompt"]).strip(),
            }
        )
    return panels


def generate_outline(
    user_prompt: str,
    character_name: str = "",
    setting: str = "",
    tone: str = "",
    style: str = "",
) -> list:
    """Return a list of 5 dicts: panel, title, scene_description, image_prompt."""
    details = []
    if character_name:
        details.append(f"- Main character name: {character_name}")
    if setting:
        details.append(f"- Setting: {setting}")
    if tone:
        details.append(f"- Story tone: {tone}")
    if style:
        details.append(f"- Art style: {style}")
    details_block = "\n".join(details) if details else "- (no extra details)"

    prompt = f"""You are a professional AI comic planner.

Create a {NUM_PANELS}-panel comic outline for the story idea below.

STORY IDEA: "{user_prompt}"

Details:
{details_block}

Rules:
- Exactly {NUM_PANELS} panels that form one story with a clear beginning, middle and end.
- The mood of every scene must match the tone "{tone or 'any'}".
- Each "image_prompt" is for Stable Diffusion: under 50 words, comma-separated visual keywords. Describe the main character the SAME way in every panel (species/appearance, colors, clothing), plus the setting, camera angle, lighting and the art style "{style or 'comic book'}". Never ask for text, speech bubbles or captions inside the image.

Each JSON object must contain exactly these keys:
"panel" (integer), "title" (string), "scene_description" (string), "image_prompt" (string)

Respond ONLY with a valid JSON array, no explanations and no markdown, in this format:
[
  {{"panel": 1, "title": "Title here", "scene_description": "Scene description here", "image_prompt": "Image prompt here"}}
]
"""

    last_error = None
    for attempt in range(1, 3):
        raw = ""
        try:
            raw = generate_text(config.GEMINI_FLASH_MODEL, prompt, json_mode=True)
            return _validate(json.loads(_strip_fences(raw)))
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            print(f"[Flash] attempt {attempt}: could not parse outline: {exc}\nRaw response:\n{raw}")
    raise RuntimeError(f"Could not generate a valid comic outline: {last_error}")
