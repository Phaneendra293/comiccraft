"""Match each panel image with its outline entry and story text."""
import re

from app import config

# Matches headers such as "**Panel 2: Title**", "### Panel 2 - Title", "Panel 2:"
PANEL_HEADER = re.compile(r"(?im)^[ \t#*]*panel\s*(\d+)\b")
IMAGE_PROMPT_LINE = re.compile(r"(?im)^[ \t*]*image\s*prompt.*$")


def _split_story(full_story: str) -> dict:
    """Return {panel_number: text_without_header}."""
    matches = list(PANEL_HEADER.finditer(full_story))
    segments = {}
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_story)
        block = full_story[match.start():end].strip()
        lines = block.splitlines()[1:]  # drop the "**Panel N: Title**" header line
        body = IMAGE_PROMPT_LINE.sub("", "\n".join(lines))
        body = re.sub(r"\n{3,}", "\n\n", body).strip().strip("-").strip()
        segments.setdefault(int(match.group(1)), body)
    return segments


def build_comic_layout(image_paths: list, full_story: str, outline: list) -> list:
    """Return a list of dicts: panel, title, image_path, image_url, text, scene_description."""
    segments = _split_story(full_story)
    layout = []
    for idx, (image, panel_info) in enumerate(zip(image_paths, outline), start=1):
        scene = panel_info.get("scene_description", "")
        text = segments.get(idx) or scene  # fall back to the scene if parsing missed a panel
        layout.append(
            {
                "panel": idx,
                "title": panel_info.get("title", f"Panel {idx}"),
                "image_path": image,
                "image_url": config.to_web_url(image),
                "text": text,
                "scene_description": scene,
            }
        )
    return layout
