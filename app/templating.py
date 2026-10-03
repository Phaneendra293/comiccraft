"""Shared Jinja2 environment and custom filters."""
import re

from fastapi.templating import Jinja2Templates
from markupsafe import Markup, escape

from app.config import TEMPLATES_DIR

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

_BOLD = re.compile(r"\*\*(.+?)\*\*")


def format_story(text: str) -> Markup:
    """Escape HTML, turn **bold** into <strong>, keep line breaks."""
    safe = str(escape(text or ""))
    safe = _BOLD.sub(r"<strong>\1</strong>", safe)
    return Markup(safe.replace("\n", "<br>"))


templates.env.filters["format_story"] = format_story
