# Infinite Studio Backend

## Requirements

- Python 3.12
- Poetry

## Setup

```bash
poetry install
cp .env.example .env
```

Fill provider keys in `.env`:

- `DEFAULT_PROVIDER=openrouter` (or `openai`)
- OpenRouter: `OPENROUTER_API_KEY`
- OpenAI: `OPENAI_API_KEY`

## Run

```bash
poetry run uvicorn app.main:app --reload --port 18000
```

If Poetry cannot download packages in your network, fallback to pip:

```bash
python -m pip install fastapi "uvicorn[standard]" httpx pydantic pydantic-settings python-multipart python-dotenv slowapi
uvicorn app.main:app --reload --port 18000
```

## API

- `GET /api/health` — Health check
- `POST /api/upload` — File upload (image/video)
- `POST /api/generate-text` — Text generation
- `POST /api/generate-image` — Image generation
- `POST /api/generate-video` — Video generation
- `GET /api/models?output_modality=image&provider=openrouter` — Available models

All endpoints operate in anonymous mode — no authentication or account is required.

### Provider examples

Generate with OpenRouter:

```json
{
  "provider": "openrouter",
  "prompt": "a cinematic cyberpunk alley",
  "model": "google/gemini-3.1-flash-image-preview",
  "aspect_ratio": "1:1",
  "image_size": "1K",
  "num_images": 1,
  "stream": false
}
```

Generate with OpenAI:

```json
{
  "provider": "openai",
  "prompt": "a cinematic cyberpunk alley",
  "model": "gpt-image-1",
  "aspect_ratio": "1:1",
  "image_size": "1K",
  "num_images": 1,
  "stream": false
}
```
