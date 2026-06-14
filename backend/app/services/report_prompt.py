import json

from app.schemas.assessment import AssessmentResponse
from app.schemas.profile import CareerProfile


def _list(items: list[str]) -> str:
    return "、".join(items) if items else "暂未填写"


def build_report_messages(response: AssessmentResponse, profile: CareerProfile) -> list[dict[str, str]]:
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
            "reportEvidenceMap": profile.reportEvidenceMap,
        },
        ensure_ascii=False,
        indent=2,
    )
    return [
        {
            "role": "system",
            "content": (
                "你是一名温和、严谨、熟悉高校学生发展规律的生涯规划顾问。"
                "请基于学生的完整问卷和画像生成中文《我的生涯蓝图》。"
                "所有判断都必须能在输入信息中找到依据，不虚构经历，不做人格定论，不制造焦虑。"
                "结构化画像已经完成分析判断，你负责依据画像证据写作，不得绕过证据重新发明结论。"
                "报告要写实、具体、有分析深度，既指出问题，也给出可执行的双路径方案。"
            ),
        },
        {
            "role": "user",
            "content": f"""
请生成约 2800-3500 个中文字符的报告，只包含下面六个主体模块和最后的安全提醒，标题名称与顺序不得改变。各模块必须控制在规定上限内，避免重复问卷答案或展开过多生活细节：

一、你5—10年后的人生画像
二、你的核心优势与风险短板
三、人生愿景与当前路径的匹配度诊断
四、接下来6个月，你可以做的3—5件事
五、半年后我会问你这些问题
六、一个值得你长期思考的问题
安全提醒

各模块写作要求：

一、你5—10年后的人生画像（建议350—450字，最多450字）
依据基本信息、5年愿景、10年愿景和价值观，概括城市、行业与岗位、生活状态和核心技能。只保留最能体现人生方向的内容，不逐项复述问卷，不展开收入、住房、家庭和爱好的琐碎细节。

二、你的核心优势与风险短板（建议450—550字，最多550字）
结合能力自评、兴趣倾向、行动基础、现有准备、资源缺口和健康精力，提炼且仅提炼2项核心优势和2项关键风险。分别使用“核心优势：”和“风险短板：”作为加粗小标题；每组编号都从1开始。每项写清表现、成因，以及对升学、就业和长期规划的影响。不要贴固定人格标签。

三、人生愿景与当前路径的匹配度诊断（建议850—1000字，最多1000字，报告重点）
对照硕士/博士/就业/出国等教育路径、专业背景和5—10年愿景，判断当前路径与目标城市、行业、岗位和生活安排的匹配度，明确现实偏差。
必须提出“Plan A：主攻路径”和“Plan B：安全兜底路径”。分别说明路径内容、适配依据、目标行业和城市契合度、进入难度、主要收益、机会成本和切换条件，最后给出清晰但不绝对的当前建议。
“Plan A：主攻路径”和“Plan B：安全兜底路径”必须分别作为独立小标题；两组下面的编号都必须各自从1开始。

四、接下来6个月，你可以做的3—5件事（建议700—850字，最多850字）
由长期愿景倒推3—5项具体行动。每项行动标题使用一级编号；该行动下的“做什么、为什么做、对Plan A的帮助、如何为Plan B预留后手、完成标准、建议时间”使用无序列表，不得继续使用与行动标题同级的数字编号。覆盖学业、技能、项目或实习、信息调研、自我提升、健康管理中最相关的事项，不要泛泛而谈。

五、半年后我会问你这些问题（建议200—300字，最多300字）
给出4—6个可复盘的问题，覆盖行动完成度、行业岗位认知、核心困惑和Plan A/Plan B是否需要切换。问题要能根据事实简短回答，不为每个问题附加长篇解释。

六、一个值得你长期思考的问题（建议120—180字，最多180字）
用一小段文字指出问题与学生的关系，再给出一句开放式问题。紧扣其最大困惑、理想与现实落差或双路径取舍，不重复前文。

安全提醒
固定提醒学生：报告是生涯探索参考，不是医学、心理诊断或人生定论；如持续感到焦虑、低落或无力，应联系学校心理咨询中心；升学就业的具体政策与机会应向学校就业指导中心、教务部门或官方渠道核实。

格式要求：
- 使用 Markdown 标题：报告标题用“#”，六个模块及安全提醒用“##”。
- 小标题可以使用“###”或单独一行的“**小标题：**”，只加粗标题、小标题和每条内容开头的短标签，不要加粗正文。
- 编号只用于模块内部的并列项目。每个新的小标题或分组都从1重新开始，禁止跨模块连续编号。
- Plan A和Plan B是两个独立分组，各自下面的编号列表必须从1重新开始。
- 第四模块只有3—5个行动标题使用数字编号；每项行动的说明字段必须使用“-”无序列表。
- “安全提醒”必须单独使用“## 安全提醒”标题，不要用“***”等分隔线代替标题。
- 不输出“质量检查”“生成说明”“字数统计”等系统信息。
- 不复述整份问卷，不使用“你一定”“你必须”“唯一选择”等绝对表达。
- 同一事实或建议最多出现一次；优先给出结论、依据和行动，删除铺垫、泛泛鼓励及重复解释。
- 不分析、不预测也不评价薪资、收入区间、收入目标是否现实或购房能力；报告正文不得出现具体薪资判断。
- 优先使用结构化画像中的结论、证据、反证与置信度。低置信度结论必须使用“可能”“有待验证”等表达。
- 已验证优势和潜在优势必须严格区分；不得把potentialStrengths写成已经具备的成熟能力。
- Plan A和Plan B必须沿用结构化画像给出的方向，只能补充表达和执行细节，不能擅自交换或另造路径。
- 画像中指出的信息缺口和矛盾必须转化为验证行动，不得用猜测填补。

学生信息：
- 年级：{response.grade}
- 性别：{response.gender}
- 专业：{response.collegeMajor}
- 家乡或成长地：{response.hometown or "未填写"}
- 当前困惑：{_list(response.careerConfusions)}
- 主要困惑描述：{response.mainConfusionText or "未填写"}
- 读硕士意向：{response.mastersIntention}
- 硕士规划：{response.mastersPlan or "未填写"}
- 读博士意向：{response.phdIntention}
- 博士规划：{response.phdPlan or "未填写"}
- 教育路径原因：{_list(response.educationPathReasons)}
- 路径确定程度：{response.educationCertainty}/5
- 五年愿景：城市={response.fiveYearCity}；行业={response.fiveYearIndustry}；岗位/角色={response.fiveYearRole}
- 五年生活：家庭状态={response.fiveYearFamilyStatus}；住房={response.fiveYearHousingPlan}；爱好与核心技能={response.fiveYearHobbiesSkills}
- 十年愿景：城市={response.tenYearCity}；行业={response.tenYearIndustry}；岗位/角色={response.tenYearRole}
- 十年生活：家庭状态={response.tenYearFamilyStatus}；住房={response.tenYearHousingPlan}；爱好与核心技能={response.tenYearHobbiesSkills}
- 价值观前三项：{_list(response.topValuesRanked)}
- 能力自评：逻辑={response.abilityScores.logic}/5；表达={response.abilityScores.expression}/5；空间设计={response.abilityScores.spatialDesign}/5；人际理解={response.abilityScores.interpersonal}/5
- 兴趣倾向：动手={response.interestScores.handsOn}/5；研究={response.interestScores.research}/5；创作={response.interestScores.creation}/5；助人={response.interestScores.helping}/5；领导影响={response.interestScores.leadership}/5；规则细节={response.interestScores.detail}/5
- 已有准备：{_list(response.currentPreparations)}
- 缺少资源：{_list(response.missingResources)}
- 专业去向认知：{response.majorOutcomeAwareness}
- 岗位认知：{response.targetJobAwareness}
- 信息渠道：{_list(response.jobInfoChannels)}
- 健康精力：{response.healthEnergyStatus}
- 运动情况：{response.exerciseFrequency or "未填写"}

结构化画像分析：
{structured_profile}
""".strip(),
        },
    ]
