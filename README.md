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
  -> 校验证据、反证、矛盾、信息缺口和 Plan A / Plan B / Plan C
  -> 基于原始回答和结构化画像生成六模块报告
```

画像会先经过结构校验，可用但缺少辅助字段时记录质量警告。系统长期保存经过校验的结构化画像，不保存大模型原始输出；发给模型的数据会排除姓名、学号、联系方式、收入预期和内部 ID 等不必要字段。报告首次未通过质量门禁时会自动要求模型完整修复一次，仍不合格才将任务标记为失败。

前端使用生成任务接口展示实时阶段：

```text
POST /api/assessment-jobs
GET  /api/assessment-jobs/{jobId}
```

生成任务及经过最小化处理的待处理输入保存在 PostgreSQL 中，并通过租约和心跳避免多个后端实例重复处理。服务重启后会恢复未完成任务；任务成功、失败或取消时会清除临时输入。默认每名学生每天最多创建 3 次生成任务，配额计数保存在登录账号的当日计数中，因此删除报告或业务数据不会绕过额度；终态任务记录保留 30 天，这些参数均可通过环境变量调整。

原有 `POST /api/assessments` 同步接口仍然保留，适合通过 ApiPost 直接测试。

## 隐私、移动端与数据管理

本轮已经补充：

- 问卷草稿和报告预填按用户隔离，保存在浏览器最多 7 天；切换账号不会读取其他用户草稿，并会清除上一账号在当前设备上的草稿；退出也会清除当前账号草稿。
- 问卷采集姓名、学号和联系方式（均为选填），性别及 5/10 年预期收入为必填；姓名、学号、联系方式和收入预期不会发送给 AI 服务。
- 健康、精力和心理感受题不在题目前增加额外用途说明，统一遵循隐私政策中的数据处理规则。
- 页面在手机宽度下使用单栏表单、可横向滚动的步骤与导航、适合触控的输入区和操作区；退出按钮仅在手机端隐藏。
- 提供 `/privacy` 隐私政策与数据管理页面、单份报告删除、全部业务数据清除，以及未知路由的 404 页面。
- 删除业务数据不会删除登录账号；账号认证与后续 jAccount 接入由学校统一处理。
- 管理员查看学生记录、完整问卷、审计日志以及编辑报告等敏感操作会写入审计日志；审计日志按 180 天保留策略清理。

详细字段边界、模型传输范围与保留期限见 [`docs/数据隐私与保留策略.md`](docs/数据隐私与保留策略.md)。本轮不包含 jAccount/登录方式改造、语音输入以及页脚主管单位和联系方式；页脚目前只提供产品名称和隐私入口。

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
REPORT_GENERATION_DAILY_LIMIT=3
REPORT_GENERATION_QUOTA_TIMEZONE=Asia/Shanghai
GENERATION_JOB_LEASE_SECONDS=300
GENERATION_JOB_HEARTBEAT_SECONDS=30
GENERATION_JOB_RETENTION_DAYS=30
ADMIN_AUDIT_RETENTION_DAYS=180
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

生成任务配置说明：

- `REPORT_GENERATION_DAILY_LIMIT`：每名学生每天允许创建的任务数；`0` 表示不限制。
- `REPORT_GENERATION_QUOTA_TIMEZONE`：每日额度的自然日时区，默认 `Asia/Shanghai`。
- `GENERATION_JOB_LEASE_SECONDS`：任务租约时长；应大于心跳间隔。
- `GENERATION_JOB_HEARTBEAT_SECONDS`：运行中任务续租间隔。
- `GENERATION_JOB_RETENTION_DAYS`：成功、失败和取消任务的状态记录保留天数。
- `ADMIN_AUDIT_RETENTION_DAYS`：管理员审计日志保留天数，默认 180 天。

首次启动时，后端会根据 `ADMIN_USERNAME` 和 `ADMIN_PASSWORD` 创建管理员账号。部署或提供给真实学生使用前，必须修改默认管理员密码和 `AUTH_SECRET`。

登录相关页面：

```text
学生登录：http://localhost:5173/login
学生注册：http://localhost:5173/register
管理员后台：http://localhost:5173/admin
```

当前仓库中的账号登录仅用于本地开发和联调，不代表已经完成真实 jAccount 集成。

## 自动化检查

后端包含报告质量、自动修复、生成任务恢复与模型数据最小化等单元测试；前端包含草稿隔离与过期、未授权处理、404、隐私入口和手机端退出按钮标识等测试。

```bash
cd backend
python -m unittest discover -s tests
```

```bash
cd frontend
npm test
npm run typecheck
npm run build
```

这些命令验证应用逻辑和前端构建；不能替代连接真实 PostgreSQL、真实模型供应商、学校登录系统及生产反向代理的集成验收。

## Docker 配置

项目明确区分两套 Compose：

- `docker-compose.yml`：服务器生产部署。
- `docker-compose.dev.yml`：本地开发和热更新。

### 服务器生产部署

生产版使用 Nginx 托管前端，后端不直接暴露到公网，数据保存在 `postgres-data` volume。

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
```

更新服务器代码：

```bash
git pull
docker compose up -d --build
```

修改服务器 `.env` 后：

```bash
docker compose up -d --force-recreate backend
```

### 本地开发

本地必须显式指定开发文件：

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

本地访问地址：

```text
前端：http://localhost:5173
后端：http://localhost:8000
```

开发版特点：

- 使用项目名 `siyuan-compass-dev` 和数据库 volume `postgres-dev-data`。
- 后端挂载 `backend/app`，并使用 `uvicorn --reload`。
- 前端挂载 `frontend`，并运行 Vite dev server。
- 前端依赖安装在 Docker volume `frontend-node-modules`，不会覆盖宿主机的 `frontend/node_modules`。

停止开发模式：

```bash
docker compose -f docker-compose.dev.yml down
```

本地更新代码后通常会热更新；修改 `.env` 后需要执行：

```bash
docker compose -f docker-compose.dev.yml up -d --force-recreate backend
```
