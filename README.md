# ComfyUI 任务管理系统

本项目包含：

- 后端：FastAPI + SQLAlchemy + PostgreSQL(JSONB)
- 前端：Vue 3 + Vite + Element Plus

## 1）本地启动 PostgreSQL（Docker）

```bash
docker run -d \
  --name task-manager-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=task_manager \
  -p 5432:5432 \
  -v task_manager_pgdata:/var/lib/postgresql/data \
  postgres:16
```

停止/启动：

```bash
docker stop task-manager-postgres
docker start task-manager-postgres
```

## 2）后端启动

```bash
cd /Users/guyin/Desktop/Echooo/confyUI-flow-back/backend
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

## 3）前端启动

```bash
cd /Users/guyin/Desktop/Echooo/confyUI-flow-back/frontend
cp .env.example .env
npm install
npm run dev
```

## 4）核心接口

鉴权相关：

- `POST /api/v1/auth/login`

任务相关：

- `POST /api/v1/tasks`
- `GET /api/v1/tasks`
- `GET /api/v1/tasks/{task_id}`
- `PATCH /api/v1/tasks/{task_id}`
- `DELETE /api/v1/tasks/{task_id}`
- `PATCH /api/v1/tasks/{task_id}/status`

子任务相关：

- `PATCH /api/v1/subtasks/{subtask_id}`
- `PATCH /api/v1/subtasks/{subtask_id}/status`

模板相关：

- `POST /api/v1/task-templates`
- `GET /api/v1/task-templates`
- `GET /api/v1/task-templates/{template_id}`
- `PATCH /api/v1/task-templates/{template_id}`
- `DELETE /api/v1/task-templates/{template_id}`
- `POST /api/v1/task-templates/{template_id}/create-task`

上传相关：

- `POST /api/v1/uploads/image`

回调接口（免鉴权）：

- `POST /api/v1/callbacks/subtask-status`

## 5）鉴权说明

当前后端业务接口不做鉴权拦截（不需要 `Authorization` 请求头）。

前端仍保留登录页与路由拦截：必须先登录才能访问业务页面。

`POST /api/v1/auth/login` 仅用于前端登录态控制。

## 6）ComfyUI 节点可直接使用的 curl 示例

1. 子任务状态回调（免鉴权）

```bash
curl --location --request POST 'http://localhost:8000/api/v1/callbacks/subtask-status' \
--header 'Content-Type: application/json' \
--data '{
  "subtask_id": "11111111-2222-3333-4444-555555555555",
  "status": "success",
  "message": "workflow done",
  "result": {
    "output_url": "https://example.com/output.png",
    "seed": 12345
  }
}'
```

2. 按 `task_id` 查询任务详情（无需鉴权）

```bash
curl --location --request GET 'http://localhost:8000/api/v1/tasks/11111111-2222-3333-4444-555555555555' \
--header 'Content-Type: application/json'
```

## 7）使用 systemctl 启动后端（服务名：flow-task）

已提供 service 模板文件：

- `deploy/systemd/flow-task.service`

请先按你的服务器实际路径修改该文件中的以下字段：

- `User` / `Group`
- `WorkingDirectory`
- `EnvironmentFile`
- `ExecStart`

示例部署步骤（Linux）：

```bash
# 1. 代码部署后，先准备后端依赖与数据库
cd /opt/flow-task/backend
cp .env.example .env
uv sync
uv run alembic upgrade head

# 2. 安装 systemd 服务
sudo cp /home/dudewei/projects/comfyUI-flow-task/deploy/systemd/flow-task.service /etc/systemd/system/flow-task.service
sudo systemctl daemon-reload
sudo systemctl enable --now flow-task

# 3. 查看运行状态
sudo systemctl status flow-task
sudo journalctl -u flow-task -f
```

常用命令：

```bash
sudo systemctl restart flow-task
sudo systemctl stop flow-task
sudo systemctl start flow-task
```
