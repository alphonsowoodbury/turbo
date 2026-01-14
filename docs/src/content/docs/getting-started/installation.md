---
title: Installation
description: Self-host Turbo-Plan on your own infrastructure
---

This guide covers self-hosting Turbo-Plan. For the hosted version, see the [Quick Start](/getting-started/quick-start) guide.

## Requirements

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis (optional, for caching)

## Backend Setup

```bash
# Clone the repository
git clone https://github.com/turbo-plan/turbo-plan.git
cd turbo-plan/turbo

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
alembic upgrade head

# Start the server
uvicorn main:app --reload
```

## Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env.local
# Edit .env.local with your API URL

# Start development server
npm run dev
```

## Environment Variables

### Backend

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SECRET_KEY` | JWT signing key | Yes |
| `REDIS_URL` | Redis connection string | No |

### Frontend

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | Yes |
| `AUTH_SECRET` | NextAuth secret | Yes |
| `AUTH_GITHUB_ID` | GitHub OAuth client ID | No |
| `AUTH_GITHUB_SECRET` | GitHub OAuth client secret | No |

## Docker Deployment

```bash
docker compose up -d
```

This starts the backend, frontend, and PostgreSQL database.

## Fly.io Deployment

See the [Fly.io Deployment Guide](https://github.com/turbo-plan/turbo-plan/blob/main/FLYIO_DEPLOYMENT_PLAN.md) for production deployment.
