# Infinite Canvas

React + tldraw + FastAPI project scaffold.

## Stack

- Frontend: React 18, Vite 5, TypeScript, Tailwind CSS, tldraw, Zustand, i18next
- Backend: Python 3.12, FastAPI, Poetry, HTTPX

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

## Run Backend

```bash
cd backend
poetry install
cp .env.example .env
poetry run uvicorn app.main:app --reload --port 8000
```

Backend now supports multi-provider image generation via one API:

- `provider: openrouter` (default)
- `provider: openai`

If Poetry install fails due to network/SSL restrictions, use a fallback:

```bash
cd backend
python -m pip install fastapi "uvicorn[standard]" httpx pydantic pydantic-settings python-multipart python-dotenv
uvicorn app.main:app --reload --port 8000
```

## Run with Docker (optional)

```bash
docker compose up
```
