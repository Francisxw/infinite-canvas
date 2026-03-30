# Infinite Studio

React Flow + FastAPI powered visual AI canvas studio.

## Stack

- Frontend: React 18, Vite 5, TypeScript, Tailwind CSS, React Flow, Zustand, i18next
- Backend: Python 3.12, FastAPI, Poetry, HTTPX

## Repository Layout

- `frontend/`: Vite + React application, colocated unit tests under `src/**/__tests__`, Playwright tests under `tests/e2e`
- `backend/`: FastAPI application and backend test suite
- `docs/`: supplemental project guides such as deployment and quick start
- `scripts/`: active QA utilities plus archived/manual investigation scripts

## Run Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Default local frontend address: `http://localhost:15191`

Set `VITE_API_BASE_URL` in `frontend/.env` to the backend you actually want to talk to. The repo now defaults to `http://localhost:18000` to avoid common local port conflicts.

## Run Backend

```bash
cd backend
poetry install
cp .env.example .env
poetry run uvicorn app.main:app --reload --port 18000
```

Backend now supports multi-provider image generation via one API:

- `provider: openrouter` (default)
- `provider: openai`

If Poetry install fails due to network/SSL restrictions, use a fallback:

```bash
cd backend
python -m pip install fastapi "uvicorn[standard]" httpx pydantic pydantic-settings python-multipart python-dotenv
uvicorn app.main:app --reload --port 18000
```

## Run with Docker (optional)

```bash
docker compose up
```

## 🚀 Deploy to Cloud

Want to deploy this project to the cloud? Check out our detailed [Deployment Guide](./docs/deployment.md) for:

- Step-by-step instructions for deploying to **Vercel** (frontend) and **Railway** (backend)
- Setting up environment variables and API keys
- Configuring CORS for production
- Continuous deployment workflow
- Cost estimation (can be completely free!)

**Quick Links:**
- ⚡ [Quick Start](./docs/quick-start.md)
- 📖 [Full Deployment Guide](./docs/deployment.md)
- 🔧 [Vercel Dashboard](https://vercel.com)
- 🚂 [Railway Dashboard](https://railway.app)

## 📚 Features

- **Visual AI Canvas**: Powered by React Flow for node-based editing, connection workflows, and media chaining
- **AI Integration**: Multi-provider support (OpenRouter, OpenAI) for AI-powered features
- **Account System**: Registration, login, session persistence, points wallet, ledger history, and recharge flow
- **WeChat Pay Flow**: Native QR recharge orders with backend callback confirmation
- **File Upload**: Support for images, videos, and text files
- **Modern Stack**: Built with React 18, FastAPI, TypeScript, and Python 3.12
- **Responsive Design**: Works on desktop and mobile devices
- **Studio Navigation**: Top-left file/edit menu, floating creation dock, minimap, zoom panel, and task strip

## Account Delivery Notes

- Backend account storage now uses SQLite at `backend/.data/account_store.db`
- Passwords are hashed with `passlib` `pbkdf2_sha256`
- Legacy JSON account data is migrated automatically on backend access
- Recharge flow is wired for WeChat Pay Native; final live payment still requires merchant credentials and a public HTTPS callback URL
- The legacy direct recharge endpoint is deprecated; frontend and backend now use WeChat order creation plus callback confirmation

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the MIT License.
