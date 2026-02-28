# 部署指南 (Deployment Guide)

本项目包含后端服务、前端控制台以及与 ComfyUI 的集成。推荐在 Linux(Ubuntu) 服务器上使用 Nginx 搭配 systemd 进行部署。

## 项目结构
- `backend/`：后端服务，基于 FastAPI + SQLAlchemy + PostgreSQL
- `frontend/`：前端控制台界面，基于 Vue 3 + Vite + Element Plus
- `deploy/systemd/`：提供守护进程的 systemd 服务配置文件模板

---

## 1. 服务器环境准备与拉取代码

此处以 **Ubuntu** 操作系统为例，预设项目克隆到 `/home/dudewei/projects/comfyUI-flow-task`。
（**注意：部署时请将这些路径全局替换为您自己的实际路径**）

```bash
cd /home/dudewei/projects
git clone <your-repo-url> comfyUI-flow-task
cd comfyUI-flow-task
```

## 2. 后端配置与初始化

后端依赖于 Python 环境（推荐使用 `uv` 管理包）与 PostgreSQL 数据库。

```bash
cd /home/dudewei/projects/comfyUI-flow-task/backend
cp .env.example .env
```

使用编辑器配置 `backend/.env`，至少确认并填写以下内容：
- `DATABASE_URL`：PostgreSQL 数据库连接串
- `ADMIN_USERNAME` / `ADMIN_PASSWORD`：管理员账号密码
- `AUTH_SECRET`：JWT 加密密钥
- `COMFYUI_API_BASE_URL`：ComfyUI 实例的地址
- `CORS_ORIGINS`：跨域允许名单

安装依赖并执行数据库迁移（升级至最新结构）：
```bash
uv sync
uv run alembic upgrade head
```

## 3. 前端配置与构建

前端应用需要配置反向代理 API 地址。

```bash
cd /home/dudewei/projects/comfyUI-flow-task/frontend
cp .env.example .env.production
```

当您使用 Nginx 作为同端口的反代服务器（针对 `/api/v1` 路由转发）时，请将 `.env.production` 配置设为相对路径以避免跨域（推荐）：
```env
VITE_API_BASE_URL=/api/v1
```

安装依赖：
```bash
npm install
```

## 4. 注册与启动 systemd 后台服务

通过 systemd，可以确保您的前后端服务在系统重启后自动恢复，意外崩溃后自动拉起。

### 4.1 安装后端系统服务 (flow-task)
先检查 `deploy/systemd/flow-task.service` 文件，确保环境路径正确，然后注册系统服务：
```bash
sudo cp /home/dudewei/projects/comfyUI-flow-task/deploy/systemd/flow-task.service /etc/systemd/system/flow-task.service
sudo systemctl daemon-reload
sudo systemctl enable --now flow-task

# 检查服务运行状态
sudo systemctl status flow-task
```

### 4.2 安装前端系统服务 (flow-task-web)
同样检查 `deploy/systemd/flow-task-web.service` 文件。它当前通过 `npm run preview -- --host 0.0.0.0 --port 5173` 启动监听。
```bash
sudo cp /home/dudewei/projects/comfyUI-flow-task/deploy/systemd/flow-task-web.service /etc/systemd/system/flow-task-web.service
sudo systemctl daemon-reload
sudo systemctl enable --now flow-task-web

# 检查服务运行状态
sudo systemctl status flow-task-web
```

## 5. 配置 Nginx 反向代理

Nginx 作为统一入口网关，反代本地的前端服务器和后端 API，规避跨域并简化配置。

如果尚未安装 Nginx：
```bash
sudo apt update
sudo apt install -y nginx
```

创建反代理配置（请将 `server_name` 修改为您的解析域名或公网 IP）：

```bash
sudo tee /etc/nginx/sites-available/flow-task <<'NGINX'
server {
    listen 80;
    server_name 35.188.136.53; # 替换为您的 IP 或域名

    client_max_body_size 20m;

    # 后端 Websocket 处理
    location /api/v1/execution/ws/ {
        proxy_pass http://127.0.0.1:8000/api/v1/execution/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 3600;
    }

    # 后端普通的 RESTful API
    location /api/v1/ {
        proxy_pass http://127.0.0.1:8000/api/v1/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 前端页面
    location / {
        proxy_pass http://127.0.0.1:5173;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
NGINX
```

激活配置并重载 Nginx：
```bash
sudo ln -sf /etc/nginx/sites-available/flow-task /etc/nginx/sites-enabled/flow-task
sudo nginx -t
sudo systemctl restart nginx
```

> ⚠️ 如果您曾经将前端部署为 Nginx 的静态挂载模式（使用了 `root /var/www/...` + `try_files`），您需要将旧规则全部移除，否则本次配置的前端反向代理不会生效。

---

## 6. 日常运维指南

### 6.1 服务检查与日志
检查应用状态：
```bash
sudo systemctl status flow-task
sudo systemctl status flow-task-web
sudo systemctl status nginx
```

动态跟踪服务最近的日志：
```bash
sudo journalctl -u flow-task -f
sudo journalctl -u flow-task-web -f
sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log
```

### 6.2 代码更新流程
每次代码修改、Git 拉取后，请按照以下标准流程重启各项服务：

```bash
cd /home/dudewei/projects/comfyUI-flow-task
git pull

# 1) 后端升级：同步依赖、执行版本表结构变动、重启
cd backend
uv sync
uv run alembic upgrade head
sudo systemctl restart flow-task

# 2) 前端升级：同步依赖、重启服务重新构建
cd ../frontend
npm install  # (如 package.json 无变动可跳过)
sudo systemctl restart flow-task-web

# 3) (可选) 如果 Nginx 配置文件有变动，或者遇到缓存异常
sudo systemctl reload nginx
```

### 6.3 数据库迁移历史查询
如需查看目前的数据库变动情况是否正常：
```bash
cd backend
uv run alembic current
uv run alembic history --verbose
```

### 6.4 联通性监控检查
验证内部是否正常：
```bash
# 后端可用性探针
curl http://127.0.0.1:8000/healthz

# 前端通过网关可用性探针 (请替换请求的主机 IP)
curl http://35.188.136.53/healthz
curl -I http://127.0.0.1:5173
```
若返回 `{"status":"ok"}` 或 `200/304` 代表运转正常。

### 6.5 常见故障排查
- `ModuleNotFoundError: No module named 'app'`
  出现该错误说明您执行 Alembic 相关的指令时，您没有切入到 `backend/` 目录下。该库需要将 pwd 保持在项目中才能查找到相关包路径。
- **向后端 API 发送请求遭遇 SSL Error 或 404**
  通常是 `.env.production` 中的 `VITE_API_BASE_URL` 写错导致跨域强行触发或未路由到 Nginx 上去。如果你使用的是 Nginx 代理前端，那么 `VITE_API_BASE_URL` 应该配置为本地相对路径 `/api/v1`。
