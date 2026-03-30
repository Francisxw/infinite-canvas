# Infinite Studio Backend

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
- Account storage: `ACCOUNT_DATA_FILE` (defaults to `.data/account_store.db`)
- Session TTL: `ACCOUNT_SESSION_TTL_HOURS` (defaults to `720`)
- Signup bonus: `SIGNUP_BONUS_POINTS` (defaults to `120`)
- WeChat Pay: `WECHAT_PAY_MCHID`, `WECHAT_PAY_APPID`, `WECHAT_PAY_PRIVATE_KEY`, `WECHAT_PAY_CERT_SERIAL_NO`, `WECHAT_PAY_APIV3_KEY`, `WECHAT_PAY_NOTIFY_URL`, `WECHAT_PAY_CERT_DIR`

The account database schema is created automatically on first use. If an old `.data/account_store.json` file exists, the backend will migrate legacy users, sessions, ledger entries, and recharge records into SQLite on access.

## Run

```bash
poetry run uvicorn app.main:app --reload --port 18000
```

If Poetry cannot download packages in your network, fallback to pip:

```bash
python -m pip install fastapi "uvicorn[standard]" httpx pydantic pydantic-settings python-multipart python-dotenv passlib "wechatpayv3[async]"
uvicorn app.main:app --reload --port 18000
```

## API

- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/account/profile`
- `GET /api/account/packages`
- `POST /api/account/recharge` (deprecated, returns 410)
- `POST /api/payments/wechat/orders`
- `GET /api/payments/wechat/orders/{order_id}`
- `POST /api/payments/wechat/notify`
- `POST /api/upload`
- `POST /api/generate-text`
- `POST /api/generate-image`
- `POST /api/generate-video`
- `GET /api/models?output_modality=image&provider=openrouter`

## Account and Credits

- Accounts are persisted in SQLite and passwords are stored with `passlib` `pbkdf2_sha256`
- Sessions expire automatically according to `ACCOUNT_SESSION_TTL_HOURS`
- Image, text, and video generation deduct credits server-side and refund automatically on failure/cancellation
- Recharge UI now creates WeChat Pay Native orders and displays a QR code for payment
- The backend credits points only after WeChat callback confirmation or order query confirms `SUCCESS`
- `WECHAT_PAY_NOTIFY_URL` must be a public HTTPS callback endpoint before going live

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
