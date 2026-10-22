# BuyWise Architecture & Deployment

## Overview

BuyWise is a multi-agent procurement automation platform. The existing pure-Python
orchestration engine (8 agents) is preserved and exposed through a FastAPI backend.
A Next.js frontend provides the user interface and deploys to Vercel.

## Components

### Backend (FastAPI)
- API endpoints for procurement requests, workflow status, SSE events
- SQLAlchemy models mapped to PostgreSQL tables
- Background workflow execution using asyncio
- Integration with existing BuyWise agents via `sys.path` import

### Frontend (Next.js)
- App Router with TypeScript and Tailwind CSS
- Responsive enterprise dashboard
- Real-time workflow progress via SSE
- Forms with React Hook Form + Zod validation

### Database (PostgreSQL)
- Durable storage for requests, agents, quotes, negotiations, decisions, approvals, audits
- Managed PostgreSQL recommended for production

## Deployment Architecture

```
[Vercel Frontend]  -->  [Python Backend Host]  -->  [Managed PostgreSQL]
     (Next.js)              (FastAPI + workers)
```

### Frontend Deployment (Vercel)

1. Connect your Git repo to Vercel
2. Set root directory to `frontend/`
3. Add env var: `NEXT_PUBLIC_API_URL=https://your-backend.com/api`
4. Deploy

### Backend Deployment

1. Choose a Python host (Railway, Render, Fly.io, AWS ECS, etc.)
2. Set env vars from `backend/.env.example`
3. Run migrations: `alembic upgrade head`
4. Start server: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Configure CORS to allow your Vercel domain

### Database

Use a managed PostgreSQL service (Neon, Supabase, AWS RDS, etc.).
Provide the connection string as `DATABASE_URL`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/health | Health check |
| POST | /api/procurement-requests | Create request + start workflow |
| GET | /api/procurement-requests | List requests |
| GET | /api/procurement-requests/{id} | Get request details |
| POST | /api/procurement-requests/{id}/start | (Re)start workflow |
| GET | /api/procurement-requests/{id}/status | Workflow status |
| GET | /api/procurement-requests/{id}/events | SSE event stream |
| GET | /api/procurement-requests/{id}/comparison | Vendor comparison |
| GET | /api/procurement-requests/{id}/negotiations | Negotiation history |
| GET | /api/approvals | List approvals |
| POST | /api/approvals/{id}/approve | Approve request |
| POST | /api/approvals/{id}/reject | Reject request |
| GET | /api/settings/evaluation-weights | Get weights |
| PUT | /api/settings/evaluation-weights | Update weights |
| GET | /api/audit-logs | Audit log entries |

## Notes

- Long-running workflows are executed as background tasks
- SSE endpoint provides real-time progress updates
- No real vendor emails or purchases are made (simulated channel)
- Human approval is explicitly required before commitment