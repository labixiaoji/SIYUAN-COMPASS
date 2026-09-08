import json

from app.schemas.assessment import AssessmentResponse
from app.schemas.profile import CareerProfile
from app.schemas.report import CareerBlueprintDraft
from app.services.profile_prompt import (
    build_model_safe_response_payload,
    compact_model_payload,
    redact_model_forbidden_values,
)

REPORT_DIRECT_RESPONSE_FIELDS = frozenset(
    {
        "educationStage",
        "grade",
        "collegeMajor",
        "hometown",
        "careerConfusions",
        "careerConfusionOther",
        "mainConfusionText",
        "fiveYearCity",
        "fiveYearIndustry",
        "fiveYearRole",
        "fiveYearFamilyStatus",
        "fiveYearHousingPlan",
        "fiveYearHobbiesSkills",
        "tenYearCity",
        "tenYearIndustry",
        "tenYearRole",
        "tenYearFamilyStatus",
        "tenYearHousingPlan",
        "tenYearHobbiesSkills",
        "topValuesRanked",
    }
)


def _list(items: list[str]) -> str:
    return "、".join(items) if items else "暂未填写"


def build_report_messages(
    response: AssessmentResponse,
    profile: CareerProfile,
    retry_reason: str | None = None,
) -> list[dict[str, str]]:
    # Reuse the same approved, compact payload as the profile stage.  This
    # avoids maintaining a second hand-written list of report input fields.
    response_payload = compact_model_payload(build_model_safe_response_payload(response))
    response_payload = {
        field_name: value
        for field_name, value in response_payload.items()
        if field_name in REPORT_DIRECT_RESPONSE_FIELDS
    }
    response_json = json.dumps(
        response_payload,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    structured_profile = json.dumps(
        {
            "summary": profile.summary,
            "coreMotivations": [item.model_dump() for item in profile.coreMotivations],
            "verifiedStrengths": [item.model_dump() for item in profile.verifiedStrengths],
            "potentialStrengths": [item.model_dump() for item in profile.potentialStrengths],
            "keyRisks": [item.model_dump() for item in profile.keyRisks],
            "visionConsistency": profile.visionConsistency.model_dump() if profile.visionConsistency else None,
            "contradictions": [item.model_dump() for item in profile.contradictions],
            "informationGaps": profile.informationGaps,
            "educationPathAssessments": [item.model_dump() for item in profile.educationPathAssessments],
            "planA": profile.planA.model_dump() if profile.planA else None,
            "planB": profile.planB.model_dump() if profile.planB else None,
            "planC": profile.planC.model_dump() if profile.planC else None,
            "reportEvidenceMap": profile.reportEvidenceMap,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    structured_profile = redact_model_forbidden_values(structured_profile, response)
    schema_json = json.dumps(
        CareerBlueprintDraft.model_json_schema(),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    retry_instruction = ""
    if retry_reason:
        retry_instruction = (
            f"\n上一次输出未通过校验，原因是：{retry_reason}。"
            "请只修复对应字段，仍然输出完整JSON对象；不要复述错误说明。"
        )
    user_content = f"""
请根据结构化画像和补充问卷生成《我的生涯蓝图》的结构化JSON草稿。后端会负责Markdown标题、编号和安全提醒；你只负责内容，不要输出Markdown。目标是让这名学生读完后看见几种可能的未来，并知道未来半年可以从哪里开始。最终报告应约4500—5500个中文字符。{retry_instruction}

写作规则：
1. 把文字写给眼前这一名学生。自然使用其城市、行业、岗位、价值排序、困惑和已有经历中的具体信息；不要把问卷答案换一种说法逐项复述，也不要写成给所有学生都适用的模板。
2. portrait只负责展开未来生活画面，不分析学生当前情况，也不给行动建议。fiveYearPortrait用320—500字，以“五年后的……”直接进入一个可能的普通日子，围绕fiveYearCity、fiveYearIndustry、fiveYearRole、fiveYearFamilyStatus、fiveYearHousingPlan和fiveYearHobbiesSkills自然写出工作与生活；tenYearPortrait用320—500字，以“到了十年左右……”展开tenYear对应答案中的职业角色、生活状态和价值取舍。只使用问卷明确提供的信息，不虚构公司、住址、伴侣、职位级别等细节。不得出现GPA、排名、年级、当前不足、家庭分歧、求职步骤、建议、证据说明或“从现在到未来需要做什么”。
3. strengthsAndRisks必须恰好包含2项优势和2项风险。studentNarrative用150—230字把能力或需要留意的地方放回学生的真实处境；futureRelevance用80—140字说明它会怎样影响未来选择。已被行为或成果支持的优势使用evidenceStatus=verified；仅来自自评、兴趣或称赞的优势使用potential；风险固定使用risk并在validation中写一项容易开始的尝试。evidenceStatus和validation是内部字段名，学生可见文字不要解释“验证、已验证、待验证”等系统术语。
4. diagnosis.currentConfusion自然写出学生选择中的拉扯，必须覆盖这些困惑：{_list(response.careerConfusions)}，并具体回应mainConfusionText；underlyingProblem解释真正缺少的信息、经历或判断标准。这里不要列“第一、第二、第三”行动，不提前展开访谈、项目、简历或家庭沟通步骤。
5. diagnosis.plans必须恰好包含id为A、B、C的三条不同路径。A和B沿用画像方向；C沿用画像planC，或在其为空时提出基于现有证据的低成本探索方向。title直接写学生可能走向的行业、岗位或发展组合，不写“主攻路径”“稳妥选择”等泛化标题。每条路径都要形成完整叙事：futureScene写这条路逐渐变清晰后可能出现的学习与工作日常；whyItFitsYou连接学生自己的经历、价值和取舍；currentGap指出眼下还可以补充的了解或能力；firstExperiment给出一项容易开始的真实尝试；decisionSignal写清看到什么结果时继续投入，出现什么情况时换一种走法。每条建议总计约500—700字，三条之间不能只替换岗位名称。
6. pathRelationship会显示在三条路径之后，用180—300字比较Plan A、Plan B、Plan C分别承担什么作用，说明当前先关注哪条、为哪条保留基础、哪条适合低成本体验。不要重复每条路径的完整内容，不另列行动清单，也不替学生做终身决定。
7. sixMonthActions把三条路径中的起步想法整合成3项高优先级行动；确有必要时最多5项，不能再创造一套与路径无关的任务。每项包含目的、1—4个连续步骤、可检查的完成标准和时间；validatesPlans填写这项行动实际关联的路径；pathConnection必须逐一写出它与validatesPlans中每条Plan的具体关系；reflectionSignal说明做完后观察什么事实，以及这些事实会怎样影响对应路径的优先级。行动要能产出作品、访谈记录、真实体验或外部反馈，不能只写“学习、提升、关注”。
8. reviewQuestions提供5—7个半年后能依据事实回答的问题；longTermQuestion只保留一段与该学生的选择有关的说明和一个开放问题。
9. 优先使用画像中的结论、经历、不同信号与置信度。同一事实或建议只出现一次；信息不够时使用“可能”“如果”“还可以再了解”等表达。先写具体处境，再给判断；长短句交替，语气像熟悉学生情况的生涯导师。
10. 学生可见文字优先使用“试一试、去了解、先做一步、看看是否、再想一想”等日常表达，避免反复使用“验证、证据状态、切换条件、匹配度”等分析术语。内部JSON字段名不受这条限制。
11. 避免“基于以上分析”“综合来看”“总体而言”“值得注意的是”“可以看出”“有利于提升”“进一步提升”“增强竞争力”“实现个人价值”“在未来发展中”等套话。不要连续使用相同句式，不要为了凑字数堆同义形容词或重复鼓励。
12. 不虚构经历、院校、家庭意见或确定结论；不分析薪资、收入或购房能力；不做医学、心理或人格诊断；不输出姓名、学号、联系方式、内部ID或时间戳。
13. 不使用“你必须”“你一定适合”“你不适合”“你肯定”“绝对”“唯一选择”“严重不足”“竞争力很弱”等表达。
14. 所有字符串只写可直接给学生阅读的纯文本，不包含Markdown标题、列表编号或换行；只输出紧凑JSON对象，不要代码块、解释、质量检查或字数统计。

问卷补充信息（仅保留困惑、基本信息和5—10年愿景；键名为问卷字段英文名，未出现的字段表示未提供）：
{response_json}

结构化画像分析（JSON；这是报告的主要依据）：
{structured_profile}

输出必须符合以下JSON Schema：
{schema_json}
""".strip()
    user_content = redact_model_forbidden_values(user_content, response)

    return [
        {
            "role": "system",
            "content": (
                "你是一名熟悉高校学生处境的生涯导师和结构化写作者。依据脱敏问卷和已完成的结构化画像，"
                "为眼前这一名学生写具体、克制、有未来画面的内容，并只输出符合Schema的JSON对象。"
                "确保结论有证据、建议可验证、三条路径有实质差异；不得虚构经历、做人格或心理诊断，"
                "也不得绕过画像重新发明结论。"
            ),
        },
        {
            "role": "user",
            "content": user_content,
        },
    ]
