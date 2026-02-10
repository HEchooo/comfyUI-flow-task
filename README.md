# ComfyUI Task Manager

This repository contains:

- Backend API: FastAPI + SQLAlchemy + PostgreSQL(JSONB)
- Frontend: Vue 3 + Vite + Element Plus

## 1) Backend startup

```bash
cd /Users/guyin/Desktop/Echooo/confyUI-flow-back/backend
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

## 2) Frontend startup

```bash
cd /Users/guyin/Desktop/Echooo/confyUI-flow-back/frontend
cp .env.example .env
npm install
npm run dev
```

## 3) Core APIs

- `POST /api/v1/auth/login`
- `POST /api/v1/tasks`
- `GET /api/v1/tasks`
- `GET /api/v1/tasks/{task_id}`
- `DELETE /api/v1/tasks/{task_id}`
- `PATCH /api/v1/tasks/{task_id}`
- `POST /api/v1/tasks/{task_id}/execution/increment`
- `PATCH /api/v1/subtasks/{subtask_id}`
- `POST /api/v1/uploads/image`

All APIs except `/api/v1/auth/login` require:

`Authorization: Bearer <access_token>`
