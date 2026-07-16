# 大学生生涯规划智能小助手

大学生生涯规划智能小助手采用前后端分离结构：

```text
frontend/  React + TypeScript + Vite
backend/   Python + FastAPI
postgres  PostgreSQL 数据库
```

生产环境使用 PostgreSQL 保存数据，并按业务对象拆分表：

```text
users                  用户账号
assessment_responses   问卷单值答案
assessment_scores      能力与兴趣量表分数
assessment_choices     问卷多选答案
career_profiles        结构化人生画像
reports                当前报告
report_versions        报告历史版本
generation_jobs        生成任务
report_feedback        报告反馈
admin_audit_logs        管理员操作记录
```

各表通过 UUID 关联，不使用用户名建立关系。画像和报告正文等复杂结构使用
`JSONB` 保存，核心关联字段单独建列，方便后续查询和迁移。

系统包含学生账号和管理员账号：

- 学生注册/登录后填写问卷，报告自动归入当前账号，并可在“我的报告”中查看历史记录。
- 管理员可查看全部学生生成记录、打开报告，并人工修改报告标题和正文。
- 学生只能访问自己的生成任务、报告和反馈页面。

报告生成采用两阶段大模型流程：

```text
问卷回答
  -> 依据每道题的解释规则生成结构化用户画像
  -> 校验证据、反证、矛盾、信息缺口和 Plan A / Plan B
  -> 基于原始回答和结构化画像生成六模块报告
```

画像只做宽松的可用性校验：只要包含可用于报告生成的核心分析内容就会继续，缺失的辅助字段会记录为质量警告。画像生成成功后会立即保存问卷、结构化画像、模型原始输出和质量警告；后续报告生成失败不会丢失画像。

前端使用生成任务接口展示实时阶段：

```text
POST /api/assessment-jobs
GET  /api/assessment-jobs/{jobId}
```

原有 `POST /api/assessments` 同步接口仍然保留，适合通过 ApiPost 直接测试。

## 本地启动

首次运行先在项目根目录创建唯一环境配置：

```bash
cp .env.example .env
```

至少填写选中模型通道的 API Key：

```text
LLM_PROVIDER=kimi
KIMI_API_KEY
AUTH_SECRET
ADMIN_PASSWORD
POSTGRES_PASSWORD
```

如需改用 DeepSeek，将 `LLM_PROVIDER` 设为 `deepseek`，并填写 `DEEPSEEK_API_KEY`。

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

项目只保留根目录 `.env` 作为唯一环境配置文件。本地后端、本地前端和 Docker Compose 都读取这一份配置：

```text
LLM_PROVIDER=kimi
KIMI_API_KEY=
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=kimi-k2.6
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
LLM_TIMEOUT_SECONDS=180
FRONTEND_ORIGINS=http://localhost:5173,http://localhost:8080,http://localhost
VITE_API_BASE_URL=http://localhost:8000/api
AUTH_SECRET=please-change-to-a-long-random-string
AUTH_TOKEN_HOURS=72
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin12345
ADMIN_DISPLAY_NAME=系统管理员
POSTGRES_DB=siyuan_compass
POSTGRES_USER=siyuan
POSTGRES_PASSWORD=please-change-postgres-password
DATABASE_URL=postgresql://siyuan:please-change-postgres-password@localhost:5432/siyuan_compass
HTTP_PORT=8080
```

`LLM_PROVIDER` 支持 `kimi` 和 `deepseek`，只会调用当前选中的通道。必须配置该通道对应的 API Key。模型未配置、超时或调用失败时，报告接口会直接返回错误，不会生成备用模板报告。

首次启动时，后端会根据 `ADMIN_USERNAME` 和 `ADMIN_PASSWORD` 创建管理员账号。部署或提供给真实学生使用前，必须修改默认管理员密码和 `AUTH_SECRET`。

登录相关页面：

```text
学生登录：http://localhost:5173/login
学生注册：http://localhost:5173/register
管理员后台：http://localhost:5173/admin
```

## Docker 本地开发

项目只保留一份 `docker-compose.yml`，用于本地开发。首次启动前创建 `.env`，然后启动容器：

```bash
cp .env.example .env
docker compose up -d --build
```

访问地址：

```text
前端：http://localhost:5173
后端：http://localhost:8000
```

特点：

- 使用项目名 `siyuan-compass-dev` 和数据库 volume `postgres-dev-data`。
- 后端挂载 `backend/app`，并使用 `uvicorn --reload`。
- 前端挂载 `frontend`，并运行 Vite dev server。
- 前端依赖安装在 Docker volume `frontend-node-modules`，不会覆盖宿主机的 `frontend/node_modules`。

停止开发模式：

```bash
docker compose down
```

更新代码后通常会热更新；修改 `.env` 后需要执行 `docker compose up -d --force-recreate backend`。
