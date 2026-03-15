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

## 🚀 Deploy to Cloud

Want to deploy this project to the cloud? Check out our detailed [Deployment Guide](./DEPLOYMENT.md) for:

- Step-by-step instructions for deploying to **Vercel** (frontend) and **Railway** (backend)
- Setting up environment variables and API keys
- Configuring CORS for production
- Continuous deployment workflow
- Cost estimation (can be completely free!)

**Quick Links:**
- 📖 [Full Deployment Guide](./DEPLOYMENT.md)
- 🔧 [Vercel Dashboard](https://vercel.com)
- 🚂 [Railway Dashboard](https://railway.app)

## 📚 Features

- **Infinite Canvas**: Powered by tldraw for smooth, intuitive drawing experience
- **AI Integration**: Multi-provider support (OpenRouter, OpenAI) for AI-powered features
- **File Upload**: Support for images, videos, and text files
- **Modern Stack**: Built with React 18, FastAPI, TypeScript, and Python 3.12
- **Responsive Design**: Works on desktop and mobile devices

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the MIT License.
