"""ComicCraft - FastAPI entry point.  Run:  uvicorn app.main:app --reload"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import config
from app.routes import router

app = FastAPI(title="ComicCraft", description="AI Comic Story Creator using Gemini + Stable Diffusion")
app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")
app.include_router(router)
