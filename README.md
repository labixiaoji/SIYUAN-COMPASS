# Siyuan Compass

思源 Compass 现在采用前后端分离结构：

```text
frontend/  React + TypeScript + Vite
backend/   Python + FastAPI
data/      本地 JSON 数据
```

本地数据按未来数据库表结构拆分保存：

```text
data/users.json                  用户账号
data/assessment_responses.json   问卷单值答案
data/assessment_scores.json      能力与兴趣量表分数
data/assessment_choices.json     问卷多选答案
data/career_profiles.json        结构化人生画像
data/reports.json                当前报告
data/report_versions.json        报告历史版本
data/generation_jobs.json        生成任务
data/report_feedback.json        报告反馈
data/admin_audit_logs.json        管理员操作记录
```

各文件通过 UUID 关联，不使用用户名建立关系。报告的输入快照不重复写入
`reports.json`，读取报告时会根据 `responseId` 和 `profileId` 重新组装。

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
AUTH_SECRET=please-change-to-a-long-random-string
AUTH_TOKEN_HOURS=72
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin12345
ADMIN_DISPLAY_NAME=系统管理员
```

前端复制 `frontend/.env.example` 为 `frontend/.env`：

```text
VITE_API_BASE_URL=http://localhost:8000/api
```

必须配置有效的 `DEEPSEEK_API_KEY`。模型未配置、超时或调用失败时，报告接口会直接返回错误，不会生成备用模板报告。

首次启动时，后端会根据 `ADMIN_USERNAME` 和 `ADMIN_PASSWORD` 创建管理员账号。部署或提供给真实学生使用前，必须修改默认管理员密码和 `AUTH_SECRET`。

登录相关页面：

```text
学生登录：http://localhost:5173/login
学生注册：http://localhost:5173/register
管理员后台：http://localhost:5173/admin
```

## Docker 部署

推荐部署到安装了 Docker Engine 和 Docker Compose 的 Linux 服务器。当前使用
JSON 文件存储，后端必须保持单 worker；项目 Dockerfile 已固定为单 worker。

1. 将代码上传或克隆到服务器。
2. 创建生产环境变量：

```bash
cp .env.production.example .env
openssl rand -hex 32
```

将生成的随机值填写到 `.env` 的 `AUTH_SECRET`，并配置：

```text
DEEPSEEK_API_KEY
FRONTEND_ORIGINS
ADMIN_PASSWORD
```

3. 构建并启动：

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f backend
```

4. 验证：

```bash
curl http://服务器IP/health
```

返回 `{"status":"ok"}` 后即可通过 `http://服务器IP` 访问。前端容器会把
`/api` 请求转发到后端，后端端口不会直接暴露到公网。

数据持久化在服务器项目目录的 `data/` 中。升级应用时不要删除该目录：

```bash
git pull
docker compose up -d --build
```

备份可以直接打包数据目录：

```bash
tar -czf siyuan-data-$(date +%F).tar.gz data/
```

生产环境应使用域名和 HTTPS。可以在该 Compose 服务前配置服务器 Nginx、
Caddy 或云厂商负载均衡，将 HTTPS 请求转发到服务器的 `HTTP_PORT`。

注意：管理员账号只在首次启动且账号不存在时创建。`users.json` 已存在管理员后，
仅修改 `.env` 中的 `ADMIN_PASSWORD` 不会自动修改已有密码。
