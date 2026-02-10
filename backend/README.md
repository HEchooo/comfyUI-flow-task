# Backend (FastAPI)

## Run locally

```bash
cd /Users/guyin/Desktop/Echooo/confyUI-flow-back/backend
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

If you want clearer request logs, keep the terminal open and click frontend actions.
Each API call will print method/path/status/time and include `X-Request-ID`.

## Authentication

Login endpoint (public):

`POST /api/v1/auth/login`

Body:

```json
{
  "username": "admin",
  "password": "admin666"
}
```

Protected APIs require Bearer token:

```http
Authorization: Bearer <access_token>
```

## Image upload

`POST /api/v1/uploads/image` will forward files to:

`$UPLOAD_API_BASE_URL/api/v1/video/upload-image`

Recommended values:

- Local/dev: `UPLOAD_API_BASE_URL=http://api.test-hot-product.echooo.link`
- Production: `UPLOAD_API_BASE_URL=http://api.hot-products.echooo.link`

## Alembic migration

```bash
cd /Users/guyin/Desktop/Echooo/confyUI-flow-back/backend
uv sync
uv run alembic upgrade head
```
