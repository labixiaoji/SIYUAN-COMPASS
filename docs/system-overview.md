# 思源 Compass 现有系统说明

## 1. 系统定位

思源 Compass 是一个面向学生的生涯规划报告生成系统。用户在前端填写测评问卷，后端根据输入生成职业画像，再调用 DeepSeek 或本地模板生成《我的生涯蓝图》报告。用户可以查看报告、提交反馈，后台可以查看基础统计指标。

当前系统是前后端分离架构：

```text
frontend/  React + TypeScript + Vite
backend/   Python + FastAPI
data/      JSON 文件存储
```

## 2. 核心页面

| 页面 | 路径 | 说明 |
| --- | --- | --- |
| 首页 | `/` | 产品入口，跳转到测评页和后台页 |
| 测评页 | `/assessment` | 收集学生基础信息、困惑、教育路径、价值观、能力兴趣和行动基础 |
| 报告页 | `/reports/:reportId` | 展示生成后的生涯规划报告 |
| 反馈页 | `/reports/:reportId/feedback` | 收集用户对报告的四项评分和文字建议 |
| 后台页 | `/admin` | 展示填写数量、报告数量、反馈均分和最近报告 |

前端接口封装位于：

```text
frontend/src/api/
```

报告展示组件位于：

```text
frontend/src/components/ReportRenderer.tsx
```

## 3. 后端接口列表

后端基础地址：

```text
http://localhost:8000
```

| 方法 | 接口 | 说明 |
| --- | --- | --- |
| GET | `/health` | 健康检查 |
| POST | `/api/assessments` | 提交测评，生成画像和报告 |
| GET | `/api/reports?reportId=xxx` | 使用 query 查询报告 |
| GET | `/api/reports/{report_id}` | 使用路径参数查询报告 |
| POST | `/api/reports/regenerate?reportId=xxx` | 使用 query 重新生成报告 |
| POST | `/api/reports/{report_id}/regenerate` | 使用路径参数重新生成报告 |
| POST | `/api/reports/feedback?reportId=xxx` | 使用 query 提交报告反馈 |
| POST | `/api/reports/{report_id}/feedback` | 使用路径参数提交报告反馈 |
| GET | `/api/admin/metrics` | 查询后台统计指标 |
| GET | `/api/llm/status` | 查看 DeepSeek 是否配置 |

## 4. 用户输入

主要输入来自 `POST /api/assessments`。输入结构定义在：

```text
backend/app/schemas/assessment.py
```

### 4.1 测评输入字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `grade` | string | 年级 |
| `collegeMajor` | string | 学院和专业 |
| `hometown` | string/null | 家乡或成长地 |
| `preferredCity` | string | 倾向发展城市 |
| `careerConfusions` | string[] | 当前生涯困惑，最多 3 项 |
| `mainConfusionText` | string/null | 一句话描述当前困惑 |
| `educationPath` | string | 毕业后初步路径 |
| `educationPathReasons` | string[] | 选择该路径的原因 |
| `educationCertainty` | number | 路径确定程度，1-5 |
| `phdIntention` | string | 读博意向 |
| `phdReasons` | string[] | 读博原因 |
| `fiveYearPriorities` | string[] | 未来 5 年优先事项，最多 3 项 |
| `targetIndustries` | string[] | 目标行业，最多 2 项 |
| `futureRoleType` | string | 未来角色类型 |
| `lifePreference` | string | 理想生活状态 |
| `tenYearSelfDescription` | string/null | 10 年后自我描述 |
| `topValuesRanked` | string[] | 最看重的 3 项价值观 |
| `abilityScores` | object | 能力自评，1-5 |
| `interestScores` | object | 兴趣自评，1-5 |
| `currentPreparations` | string[] | 已做准备 |
| `missingResources` | string[] | 当前最缺资源，最多 3 项 |
| `majorOutcomeAwareness` | string | 对本专业毕业去向的了解程度 |
| `targetJobAwareness` | string | 对目标岗位要求的了解程度 |
| `healthEnergyStatus` | string | 健康和精力状态 |
| `exerciseFrequency` | string/null | 运动频率 |
| `userId` | string/null | 可选，已有用户 ID |

### 4.2 能力分数

```json
{
  "logic": 4,
  "expression": 3,
  "spatialDesign": 2,
  "interpersonal": 3
}
```

### 4.3 兴趣分数

```json
{
  "handsOn": 4,
  "research": 4,
  "creation": 3,
  "helping": 2,
  "leadership": 3,
  "detail": 4
}
```

## 5. 系统输出

### 5.1 提交测评后的输出

接口：

```text
POST /api/assessments
```

输出示例：

```json
{
  "userId": "03755039-21d5-4a4d-abe5-c87b112d9fa7",
  "responseId": "e00f6d32-d562-494c-ae48-cc7ed84507e0",
  "profileId": "ca6705a8-8b43-4f82-b5b7-302221210468",
  "reportId": "ea283701-e679-485f-9a35-cac37c4b79b1",
  "generationStatus": "success"
}
```

### 5.2 查询报告的输出

接口：

```text
GET /api/reports?reportId=xxx
```

核心字段：

| 字段 | 说明 |
| --- | --- |
| `id` | 报告 ID |
| `userId` | 用户 ID |
| `responseId` | 测评回答 ID |
| `profileId` | 职业画像 ID |
| `title` | 报告标题 |
| `content` | 报告正文 |
| `wordCount` | 字符数统计 |
| `generationStatus` | 生成状态 |
| `qualityStatus` | 质量检查状态 |
| `errorMessage` | 质量检查或生成错误信息 |
| `modelName` | 使用的模型，可能是 `deepseek-chat` 或 `local-template` |
| `promptVersion` | 提示词或模板版本 |
| `inputSnapshot` | 本次报告使用的输入快照 |
| `retryCount` | 重新生成次数 |
| `createdAt` | 创建时间 |
| `updatedAt` | 更新时间 |

前端展示时主要使用：

```text
title
content
wordCount
generationStatus
```

质量检查字段目前后端仍返回，但前端报告页已经隐藏。

### 5.3 反馈输入和输出

接口：

```text
POST /api/reports/feedback?reportId=xxx
```

输入：

```json
{
  "understandingScore": 4,
  "insightScore": 4,
  "actionScore": 4,
  "recommendScore": 4,
  "comment": "建议行动建议再具体一点"
}
```

输出：

```json
{
  "feedbackId": "xxx",
  "createdAt": "2026-05-26T06:02:37.849607+00:00"
}
```

## 6. 核心处理过程

### 6.1 提交测评到生成报告

入口文件：

```text
backend/app/api/assessments.py
```

处理链路：

```text
用户提交测评
  -> Pydantic schema 校验基础类型
  -> validate_assessment 做业务规则校验
  -> get_or_create_user 创建或复用用户
  -> 生成 AssessmentResponse
  -> build_career_profile 生成职业画像
  -> generate_report 生成报告
  -> save_assessment_bundle 保存 response/profile/report
  -> 返回 userId/responseId/profileId/reportId
```

### 6.2 测评校验

文件：

```text
backend/app/services/assessment_validator.py
```

主要规则：

| 字段 | 规则 |
| --- | --- |
| 必填字符串字段 | 不允许为空 |
| `careerConfusions` | 至少 1 项，最多 3 项 |
| `educationPathReasons` | 至少 1 项 |
| `educationCertainty` | 1-5 整数 |
| `fiveYearPriorities` | 至少 1 项，最多 3 项 |
| `targetIndustries` | 至少 1 项，最多 2 项 |
| `topValuesRanked` | 至少 3 项 |
| `currentPreparations` | 至少 1 项 |
| `missingResources` | 至少 1 项，最多 3 项 |

### 6.3 职业画像生成

主要文件：

```text
backend/app/services/profile_classifier.py
backend/app/services/profile_builder.py
backend/app/schemas/profile.py
```

当前画像由规则生成，会把用户归入以下状态之一：

```text
方向模糊型
教育路径摇摆型
科研深造倾向型
高目标高压力型
目标清晰但行动不足型
稳定安全导向型
```

画像输出字段：

| 字段 | 说明 |
| --- | --- |
| `careerStateType` | 主状态类型 |
| `matchedStateTypes` | 命中的状态类型集合 |
| `evidence` | 判断依据 |
| `strengthTags` | 优势标签 |
| `riskTags` | 风险标签 |
| `valueTags` | 价值观标签 |
| `interestTags` | 兴趣标签 |
| `actionReadinessScore` | 行动准备度 |
| `ruleVersion` | 规则版本 |

### 6.4 报告生成

主要文件：

```text
backend/app/services/report_generator.py
backend/app/services/report_prompt.py
backend/app/llm/deepseek.py
```

生成逻辑：

```text
检查 DEEPSEEK_API_KEY
  -> 如果已配置：调用 DeepSeek
  -> 如果未配置：使用本地模板
  -> 如果 DeepSeek 调用失败：回退本地模板
  -> 对报告做质量检查
  -> 返回 CareerBlueprintReport
```

DeepSeek 提示词位于：

```text
backend/app/services/report_prompt.py
```

本地模板位于：

```text
backend/app/services/report_generator.py
```

报告固定章节：

```text
一、你5—10年后想成为的人
二、你的当前生涯状态判断
三、你的核心优势与主要风险
四、愿景、教育路径与当前行动的匹配度诊断
五、接下来6个月建议做的3—5件事
六、半年后我会问你的问题
七、一个值得长期思考的问题
安全提醒
```

### 6.5 报告质量检查

文件：

```text
backend/app/services/report_quality_check.py
```

检查内容：

| 检查项 | 说明 |
| --- | --- |
| 必需章节 | 是否包含固定报告章节 |
| 不建议表达 | 避免“你必须”“你肯定”“唯一选择”等绝对化表达 |
| 长度 | 超过 1800 字符会 warning |
| 安全提醒 | 必须包含心理咨询中心和就业指导中心提示 |

质量检查结果会存在报告中，但目前前端不展示质量检查信息。

### 6.6 数据存储

当前使用 JSON 文件存储，文件路径：

```text
data/db.json
```

存储层代码：

```text
backend/app/storage/json_db.py
```

数据集合：

```json
{
  "users": [],
  "responses": [],
  "profiles": [],
  "reports": [],
  "feedback": []
}
```

## 7. 前端展示过程

报告页面：

```text
frontend/src/pages/ReportPage.tsx
```

报告渲染组件：

```text
frontend/src/components/ReportRenderer.tsx
```

展示流程：

```text
用户访问 /reports/:reportId
  -> 前端调用 GET /api/reports?reportId=xxx 或路径版接口
  -> 获取 report.content
  -> ReportRenderer 解析报告文本
  -> 识别章节标题、小标题、普通段落、编号列表、行动建议
  -> 渲染成前端报告样式
```

当前渲染规则：

| 内容 | 前端展示方式 |
| --- | --- |
| `一、...` / `二、...` | 章节标题 |
| `## 标题` | 章节标题 |
| `核心优势：` | 小标题 |
| `主要风险：` | 小标题 |
| 普通正文 | 段落 |
| 普通编号项 | 普通列表，按小标题或章节重新从 1 编号 |
| 行动建议章节编号项 | 行动卡片，重新从 1 编号 |

## 8. 典型完整流程

```text
1. 用户打开前端首页
2. 用户进入 /assessment 填写测评
3. 前端 POST /api/assessments
4. 后端校验输入
5. 后端创建用户和测评回答
6. 后端根据规则生成职业画像
7. 后端调用 DeepSeek 或本地模板生成报告
8. 后端保存用户、回答、画像、报告到 data/db.json
9. 后端返回 reportId
10. 前端跳转 /reports/:reportId
11. 前端查询报告并渲染
12. 用户可进入反馈页提交评分
13. 后台页通过 /api/admin/metrics 查看汇总数据
```

## 9. 当前限制

1. 数据存储仍是 JSON 文件，不适合多人高并发写入。
2. 没有登录系统，用户识别主要依赖前端保存的 `userId`。
3. DeepSeek 未配置时会走本地模板，报告个性化程度较低。
4. 报告正文仍是文本格式，前端通过规则解析，模型输出格式不稳定时仍可能需要继续增强渲染器。
5. 后台目前是轻量统计，没有权限控制。

## 10. 后续优化建议

1. 将 `data/db.json` 迁移到 SQLite 或 PostgreSQL。
2. 增加用户登录或匿名会话机制。
3. 升级 `report_prompt.py`，让模型输出更稳定的结构化 JSON，再由前端渲染。
4. 为测评提交、报告生成、反馈提交增加自动化测试。
5. 为后台增加按报告状态、画像类型、反馈分数筛选的能力。
