from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.llm.deepseek import create_deepseek_chat_completion, is_deepseek_configured
from app.schemas.assessment import AssessmentResponse
from app.schemas.profile import CareerProfile
from app.schemas.report import CareerBlueprintReport
from app.services.report_prompt import build_report_messages
from app.services.report_quality_check import check_report_quality, count_chineseish_words

REPORT_PROMPT_VERSION = "deepseek-v1.0.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_text(items: list[str]) -> str:
    return "、".join(items) if items else "暂未填写"


def sentence(value: str | None) -> str:
    return value.strip() if value and value.strip() else "你还没有写下很具体的描述，这也说明当前可以先从探索和验证开始。"


def build_actions(response: AssessmentResponse, profile: CareerProfile) -> list[str]:
    actions: list[str] = []

    if "不了解" in response.targetJobAwareness or "大概" in response.targetJobAwareness or "还没有" in response.targetJobAwareness:
        actions.append("整理20个目标岗位JD，记录学历、技能、项目、实习和工具要求，把想象中的职业变成可比较的信息。")

    if "缺人脉和信息" in response.missingResources or "不知道本专业未来有哪些出路" in response.careerConfusions:
        actions.append("访谈3位学长学姐、老师或校友，了解就业、深造和备选路径，重点问真实日常、进入门槛和后悔点。")

    if "缺项目 / 实习经历" in response.missingResources or len(response.currentPreparations) < 2 or "还没有明显准备" in response.currentPreparations:
        actions.append("完成一个能写进简历的小项目或作品，并和目标行业连接起来，证明你已经开始靠近目标。")

    if profile.careerStateType == "教育路径摇摆型":
        actions.append("给读研、就业或其他路径设置两个月验证期，列出机会成本、准备要求和五年生活状态，再做阶段性决定。")

    if profile.careerStateType == "科研深造倾向型":
        actions.append("和1位导师或博士生聊科研训练，确认自己喜欢的是研究过程，还是学历、平台和延缓选择带来的安全感。")

    if "较差" in response.healthEnergyStatus or "一般" in response.healthEnergyStatus:
        actions.append("建立每周可持续的精力底线，例如固定2次运动和稳定睡眠窗口，让身体状态支撑长期执行。")

    if not actions:
        actions = [
            "选择一个最想靠近的目标方向，整理它的岗位、升学或科研要求，形成一页清单。",
            "找一位相关方向的学长学姐或老师做一次访谈，用真实经历校准自己的判断。",
            "把已有课程、项目或社团经历整理成简历素材，确认哪些经历能证明你的优势。",
        ]

    return actions[:5]


def generate_local_report(response: AssessmentResponse, profile: CareerProfile) -> CareerBlueprintReport:
    now = now_iso()
    actions = build_actions(response, profile)
    strengths = profile.strengthTags[:4]
    risks = profile.riskTags[:4]
    ten_year_text = sentence(response.tenYearSelfDescription)

    content = f"""# 我的生涯蓝图

## 一、你5—10年后想成为的人

从你的回答看，你期待的未来不是简单地“找到一份工作”，而是希望在{response.preferredCity}或与自己生活节奏匹配的城市中，形成稳定的发展空间。你提到的目标方向是{list_text(response.targetIndustries)}，未来角色更接近{response.futureRoleType}。你最看重的是{list_text(response.topValuesRanked)}，说明你既在意现实回报，也希望选择能和长期生活方式相容。

你对10年后的描述是：“{ten_year_text}” 这句话把职业选择从岗位问题拉回到“想成为什么样的人”。接下来的规划不必立刻定终局，但每一步都要更接近这个方向。

## 二、你的当前生涯状态判断

基于当前回答，你目前更接近“{profile.careerStateType}”。这不是固定标签，而是在提示你当前最需要处理的核心问题。系统命中的依据包括：{list_text(profile.evidence[:4])}。

你现在的重点不是马上得到完美答案，而是把愿景、教育路径和行动准备重新对齐。你提到“{sentence(response.mainConfusionText)}”，说明困惑已经比较具体，适合通过信息收集和小规模行动验证。

## 三、你的核心优势与主要风险

你可以依靠的优势包括：{list_text(strengths)}。你并不是从零开始，只需要把已有能力和经历转化成更清晰的方向证据，让外部机会更容易识别你。

需要关注的风险包括：{list_text(risks)}。这些风险不是说“来不及”，而是提醒你不要停在想法层面。目标行业、学历路径和岗位要求没有拆清时，人很容易反复摇摆。

## 四、愿景、教育路径与当前行动的匹配度诊断

你当前倾向的毕业后选择是{response.educationPath}，确定程度为{response.educationCertainty}/5，主要原因包括{list_text(response.educationPathReasons)}。这条路径是否合适，关键在于它能否服务于你想进入的方向：{list_text(response.targetIndustries)}，以及你想成为的{response.futureRoleType}。

如果这条路径能补齐目标方向需要的学历、技能、项目、研究或平台资源，它就是通往愿景的工具。反过来，如果它主要在缓解短期焦虑，可能会推迟选择，却不一定提高主动权。

你已经做过的准备包括{list_text(response.currentPreparations)}，最缺的是{list_text(response.missingResources)}。下一阶段最值得投入的不是抽象思考，而是获得外部证据：岗位要求、真实路径、项目、实习、导师或校友反馈。

## 五、接下来6个月建议做的3—5件事

{chr(10).join(f"{index + 1}. {action}" for index, action in enumerate(actions))}

这些行动的目标，是让你在6个月后拥有更具体的判断依据。到那时，你未必已经确定终身方向，但应该更清楚哪些路径值得继续投入。

## 六、半年后我会问你的问题

半年后，建议你重新回答：是否完成过职业访谈？是否更清楚自己要就业、读研、出国还是读博？对城市、行业和生活状态的判断是否变化？是否完成了能写进简历的项目、实习或经历？最看重的价值观是否变化？

## 七、一个值得长期思考的问题

如果未来不能同时满足{list_text(response.topValuesRanked[:3])}，你最愿意优先守住哪一个？你又愿意暂时牺牲哪一个？

## 安全提醒

如果你在规划中感到持续的迷茫、焦虑或无力，建议你预约学校的心理咨询中心或就业指导中心进行一对一沟通。"""

    quality = check_report_quality(content)
    return CareerBlueprintReport(
        id=str(uuid4()),
        userId=response.userId,
        responseId=response.id,
        profileId=profile.id,
        title="我的生涯蓝图",
        content=content,
        wordCount=count_chineseish_words(content),
        generationStatus="success",
        qualityStatus=quality["status"],
        errorMessage="；".join(quality["warnings"]) or None,
        modelName="local-template",
        promptVersion="local-template-v1.0.0",
        inputSnapshot={"response": response, "profile": profile},
        retryCount=0,
        createdAt=now,
        updatedAt=now,
    )


async def generate_report(response: AssessmentResponse, profile: CareerProfile) -> CareerBlueprintReport:
    if not is_deepseek_configured():
        return generate_local_report(response, profile)

    now = now_iso()
    try:
        result = await create_deepseek_chat_completion(build_report_messages(response, profile))
        quality = check_report_quality(result["content"])

        return CareerBlueprintReport(
            id=str(uuid4()),
            userId=response.userId,
            responseId=response.id,
            profileId=profile.id,
            title="我的生涯蓝图",
            content=result["content"],
            wordCount=count_chineseish_words(result["content"]),
            generationStatus="success",
            qualityStatus=quality["status"],
            errorMessage="；".join(quality["warnings"]) or None,
            modelName=result["modelName"],
            promptVersion=REPORT_PROMPT_VERSION,
            inputSnapshot={"response": response, "profile": profile},
            retryCount=0,
            createdAt=now,
            updatedAt=now,
        )
    except Exception as error:
        fallback = generate_local_report(response, profile)
        fallback.modelName = f"{fallback.modelName} fallback"
        fallback.promptVersion = f"{REPORT_PROMPT_VERSION} -> {fallback.promptVersion}"
        fallback.qualityStatus = "warning" if fallback.qualityStatus == "passed" else fallback.qualityStatus
        fallback.errorMessage = f"DeepSeek 调用失败，已回退本地模板：{error}" + (f"；{fallback.errorMessage}" if fallback.errorMessage else "")
        fallback.createdAt = now
        fallback.updatedAt = now
        return fallback
