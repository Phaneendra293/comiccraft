# ComicCraft - AI Comic Story Creator (FastAPI + Gemini + Stable Diffusion)

Run from the project root:

    python -m venv env
    env\Scripts\activate          # Windows   (macOS/Linux: source env/bin/activate)
    pip install -r requirements.txt
    copy .env.example .env        # macOS/Linux: cp .env.example .env   -> then add your keys
    uvicorn app.main:app --reload

Open http://127.0.0.1:8000 (API docs: /docs).
Set USE_PLACEHOLDER_IMAGES=true in .env for a quick test without Stable Diffusion.
