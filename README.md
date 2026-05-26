# Siyuan Compass

思源 Compass 现在采用前后端分离结构：

```text
frontend/  React + TypeScript + Vite
backend/   Python + FastAPI
data/      本地 JSON 数据
```

## 本地启动

后端：

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

访问地址：

```text
前端：http://localhost:5173
后端：http://localhost:8000
接口文档：http://localhost:8000/docs
```

## 环境变量

后端复制 `backend/.env.example` 为 `backend/.env`，按需配置 DeepSeek：

```text
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
LLM_TIMEOUT_SECONDS=180
FRONTEND_ORIGINS=http://localhost:5173
```

前端复制 `frontend/.env.example` 为 `frontend/.env`：

```text
VITE_API_BASE_URL=http://localhost:8000/api
```

没有配置 `DEEPSEEK_API_KEY` 时，后端会自动使用本地模板生成报告。
