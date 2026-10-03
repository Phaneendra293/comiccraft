"""Gemini Pro: detailed narration and character dialogue for each panel."""
from app import config
from app.gemini_client import generate_text


def generate_story(
    outline: list,
    character_name: str = "",
    setting: str = "",
    tone: str = "",
) -> str:
    """Expand the panel outline into one formatted comic story (text)."""
    formatted_outline = "\n".join(
        f"{p['panel']}. {p['title']}: {p['scene_description']}" for p in outline
    )
    context = []
    if character_name:
        context.append(f"Main character: {character_name}")
    if setting:
        context.append(f"Setting: {setting}")
    if tone:
        context.append(f"Tone: {tone}")
    context_block = "\n".join(context)

    prompt = f"""You are a comic book writer.

Given the panel breakdown below, write a comic-style story with engaging narration and character dialogue for each panel.

{context_block}

Panel Outline:
{formatted_outline}

Guidelines:
- Use a fun, engaging voice like a real comic book, matching the tone "{tone or 'any'}".
- Keep each panel self-contained but part of one cohesive story.
- Keep every panel short (about 40-70 words) so it fits on a comic page.
- Do NOT write image prompts or art directions.
- Use EXACTLY this layout for each panel, with nothing before the first panel and nothing after the last:

**Panel 1: <title>**
**CAPTION:** <one short line of ambient description>
**NARRATION:** <narration text>
**DIALOGUE:** <Character name>: "<line>"

**Panel 2: <title>**
...
"""
    return generate_text(config.GEMINI_PRO_MODEL, prompt)
