# Infinite Canvas Backend

## Requirements

- Python 3.12
- Poetry

## Setup

```bash
poetry install
cp .env.example .env
```

Fill provider keys in `.env`.

- `DEFAULT_PROVIDER=openrouter` (or `openai`)
- OpenRouter: `OPENROUTER_API_KEY`
- OpenAI: `OPENAI_API_KEY`

## Run

```bash
poetry run uvicorn app.main:app --reload --port 8000
```

If Poetry cannot download packages in your network, fallback to pip:

```bash
python -m pip install fastapi "uvicorn[standard]" httpx pydantic pydantic-settings python-multipart python-dotenv
uvicorn app.main:app --reload --port 8000
```

## API

- `GET /api/health`
- `POST /api/upload`
- `POST /api/generate-image`
- `GET /api/models?output_modality=image&provider=openrouter`

### Provider examples

Generate with OpenRouter:

```json
{
  "provider": "openrouter",
  "prompt": "a cinematic cyberpunk alley",
  "model": "google/gemini-2.5-flash-image-preview",
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
