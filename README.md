# BuyWise

Production-ready multi-agent procurement automation platform.

## Architecture

```
buywise/
├── buywise/              # Existing Python multi-agent engine (preserved)
├── backend/              # FastAPI application layer
├── frontend/             # Next.js App Router frontend (Vercel)
├── database/             # Schema and migrations
├── docs/                 # Architecture and deployment docs
└── vercel.json           # Vercel deployment config
```

## Technology Stack

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL
- **Orchestration:** Existing BuyWise 8-agent Python engine
- **Frontend:** Next.js 14, TypeScript, Tailwind CSS, shadcn/ui
- **Real-time:** Server-Sent Events (SSE) for workflow progress
- **Deployment:** Frontend on Vercel, backend on Python-compatible host, managed PostgreSQL

## Quick Start (Local Development)

### 1. Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your DATABASE_URL
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd frontend
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000/api
npm install
npm run dev
```

Open http://localhost:3000

## Deployment

### Frontend (Vercel)

1. Push the `frontend/` folder to a Git repository
2. Import the project in Vercel
3. Set the `NEXT_PUBLIC_API_URL` environment variable to your backend URL
4. Deploy

### Backend

Deploy the `backend/` folder to a Python-compatible hosting service (Railway, Render, Fly.io, etc.):
1. Set `DATABASE_URL` to your managed PostgreSQL connection string
2. Set `BACKEND_CORS_ORIGINS` to include your Vercel domain
3. Run `alembic upgrade head` for migrations
4. Start with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Database

Provision a managed PostgreSQL database and set `DATABASE_URL` in the backend environment.

## Key Design Decisions

- The existing BuyWise Python orchestrator is preserved unchanged
- Workflows run as background tasks; frontend polls/SSE for progress
- All procurement business logic remains on the backend
- Simulated vendor channel is used (no real emails or purchases)
- Human approval is required before any commitment