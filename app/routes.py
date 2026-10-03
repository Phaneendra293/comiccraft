"""All FastAPI routes for ComicCraft."""
import traceback
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app import config
from app.exporters import save_pdf
from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.templating import templates

router = APIRouter()

SETTINGS = ["school", "forest", "space", "city"]
TONES = ["light-hearted", "dramatic", "poetic", "funny"]
STYLES = ["anime", "pixel art", "comic book", "realistic"]
DEFAULT_FORM = {
    "prompt": "A brave fox explores an enchanted forest.",
    "character_name": "Free",
    "setting": "forest",
    "tone": "dramatic",
    "style": "anime",
}


class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=3, examples=["A brave fox exploring an enchanted forest."])
    character_name: str = "Hero"
    setting: str = "forest"
    tone: str = "dramatic"
    style: str = "anime"


def _create_comic(prompt: str, character_name: str, setting: str, tone: str, style: str):
    """Run the full pipeline: outline -> story -> images -> layout -> PDF."""
    outline = generate_outline(prompt, character_name, setting, tone, style)
    full_story = generate_story(outline, character_name, setting, tone)
    images = [generate_image(p["image_prompt"], style=style) for p in outline]
    layout = build_comic_layout(images, full_story, outline)
    pdf_path = save_pdf(layout)
    return layout, config.to_web_url(pdf_path)


def _index_context(request: Request, form=None, error=None):
    return {
        "request": request,
        "form": form or DEFAULT_FORM,
        "settings": SETTINGS,
        "tones": TONES,
        "styles": STYLES,
        "error": error,
    }


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", _index_context(request))


@router.post("/generate", response_class=HTMLResponse)
def generate_comic(
    request: Request,
    prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    style: str = Form(...),
):
    form = {"prompt": prompt, "character_name": character_name,
            "setting": setting, "tone": tone, "style": style}
    try:
        layout, pdf_url = _create_comic(prompt, character_name, setting, tone, style)
        return templates.TemplateResponse(
            request, "comic_preview.html",
            {"request": request, "layout": layout, "pdf_path": pdf_url},
        )
    except Exception as exc:
        traceback.print_exc()
        return templates.TemplateResponse(
            request, "index.html",
            _index_context(request, form=form, error=str(exc)),
            status_code=500,
        )


@router.post("/generate-comic/json")
def generate_comic_json(payload: PromptRequest):
    try:
        layout, pdf_url = _create_comic(
            payload.prompt, payload.character_name, payload.setting, payload.tone, payload.style
        )
        return {"layout": layout, "pdf_path": pdf_url}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/export-success", response_class=HTMLResponse)
def export_success(request: Request, pdf_path: str = ""):
    name = Path(pdf_path).name  # never trust the full path from the query string
    pdf_url = f"/static/exports/{name}" if name else ""
    return templates.TemplateResponse(
        request, "export_success.html", {"request": request, "pdf_path": pdf_url}
    )


@router.get("/test-image")
def test_image(
    prompt: str = "A futuristic city at sunset, sci-fi, cinematic, artstation",
    style: str = "",
):
    try:
        path = generate_image(prompt, style=style or None)
        return {"message": "Image generated successfully", "path": path, "url": config.to_web_url(path)}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))
