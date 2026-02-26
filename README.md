# ComfyUI Flow Task Manager

本仓库是完整的前后端项目：

- 后端：FastAPI + SQLAlchemy + Alembic + PostgreSQL
- 前端：Vue 3 + Vite + Element Plus
- 进程管理：systemd（`flow-task` / `flow-task-web`）
- 反向代理：Nginx

目录：

- `backend/`：后端代码与 Alembic
- `frontend/`：前端代码
- `deploy/systemd/`：systemd 服务模板

## 1. 服务器一次性部署

以下示例以 Ubuntu 为例，项目路径用：

`/home/dudewei/projects/comfyUI-flow-task`

请按你的实际路径替换。

### 1.1 拉取代码

```bash
cd /home/dudewei/projects
git clone <your-repo-url> comfyUI-flow-task
cd comfyUI-flow-task
```

### 1.2 配置后端

```bash
cd /home/dudewei/projects/comfyUI-flow-task/backend
cp .env.example .env
```

编辑 `backend/.env`，至少确认这些项：

- `DATABASE_URL`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `AUTH_SECRET`
- `COMFYUI_API_BASE_URL`
- `CORS_ORIGINS`

安装依赖并迁移数据库：

```bash
uv sync
uv run alembic upgrade head
```

### 1.3 配置前端

```bash
cd /home/dudewei/projects/comfyUI-flow-task/frontend
cp .env.example .env.production
```

如果你用 Nginx 做同域反代（推荐），设置为：

```env
VITE_API_BASE_URL=/api/v1
```

安装依赖：

```bash
npm install
```

### 1.4 安装后端 systemd 服务

先检查并按实际路径修改模板：

- `deploy/systemd/flow-task.service`

然后安装并启动：

```bash
sudo cp /home/dudewei/projects/comfyUI-flow-task/deploy/systemd/flow-task.service /etc/systemd/system/flow-task.service
sudo systemctl daemon-reload
sudo systemctl enable --now flow-task
sudo systemctl status flow-task
```

### 1.5 安装前端 systemd 服务

先检查并按实际路径修改模板：

- `deploy/systemd/flow-task-web.service`

然后安装并启动：

```bash
sudo cp /home/dudewei/projects/comfyUI-flow-task/deploy/systemd/flow-task-web.service /etc/systemd/system/flow-task-web.service
sudo systemctl daemon-reload
sudo systemctl enable --now flow-task-web
sudo systemctl status flow-task-web
```

`flow-task-web` 当前通过 `npm run preview -- --host 0.0.0.0 --port 5173` 提供前端页面。

### 1.6 安装并配置 Nginx

安装：

```bash
sudo apt update
sudo apt install -y nginx
```

创建站点配置（只有 IP 也可以，`server_name` 直接写 IP）：

```bash
sudo tee /etc/nginx/sites-available/flow-task <<'NGINX'
server {
    listen 80;
    server_name 35.188.136.53;

    client_max_body_size 50m;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    location / {
        proxy_pass http://127.0.0.1:5173;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX
```

启用并重载：

```bash
sudo ln -sf /etc/nginx/sites-available/flow-task /etc/nginx/sites-enabled/flow-task
sudo nginx -t
sudo systemctl restart nginx
```

## 2. 日常运维命令

查看状态：

```bash
sudo systemctl status flow-task
sudo systemctl status flow-task-web
sudo systemctl status nginx
```

查看日志：

```bash
sudo journalctl -u flow-task -f
sudo journalctl -u flow-task-web -f
sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log
```

重启服务：

```bash
sudo systemctl restart flow-task
sudo systemctl restart flow-task-web
sudo systemctl restart nginx
```

## 3. 更新代码后的标准流程（前后端）

每次发版后，按下面步骤执行：

```bash
cd /home/dudewei/projects/comfyUI-flow-task
git pull

# 1) 后端：依赖 + 迁移 + 重启
cd backend
uv sync
uv run alembic upgrade head
sudo systemctl restart flow-task

# 2) 前端：依赖 + 重启（服务会自动执行 build）
cd ../frontend
npm install
sudo systemctl restart flow-task-web

# 3) 反向代理重载（可选）
sudo systemctl reload nginx
```

如果本次更新没有改前端依赖，`npm install` 可以跳过。

## 4. 数据库迁移说明

- 新环境：直接 `uv run alembic upgrade head`
- 已有历史库：先确认当前状态，再执行升级

```bash
cd /home/dudewei/projects/comfyUI-flow-task/backend
uv run alembic current
uv run alembic history --verbose
```

## 5. 健康检查

后端健康检查：

```bash
curl http://127.0.0.1:8000/healthz
```

通过 Nginx 检查：

```bash
curl http://35.188.136.53/healthz
```

返回 `{"status":"ok"}` 说明后端可用。

## 6. 常见问题

### 6.1 `ModuleNotFoundError: No module named 'app'`（执行 Alembic）

确保在 `backend/` 目录执行命令：

```bash
cd /home/dudewei/projects/comfyUI-flow-task/backend
uv run alembic upgrade head
```

### 6.2 前端请求到了 `https://IP:8000` 报 SSL 错误

通常是前端 `VITE_API_BASE_URL` 配置错误。

- 如果走 Nginx 反代，前端应配置：`VITE_API_BASE_URL=/api/v1`
- 不要在无证书情况下直接请求 `https://<ip>:8000`

### 6.3 CORS 要不要开

- 如果前端与后端都走同一域名/IP 的 Nginx（前端 `/`，后端 `/api/`），通常不会触发跨域。
- 仍建议保留后端 `CORS_ORIGINS` 正确配置，便于本地调试。
