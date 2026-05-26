from app.schemas.assessment import AssessmentResponse
from app.schemas.profile import CareerProfile


def _list(items: list[str]) -> str:
    return "、".join(items) if items else "暂未填写"


def build_report_messages(response: AssessmentResponse, profile: CareerProfile) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是一名温和、负责的高校生涯规划顾问。请基于学生问卷和画像，生成一份中文《我的生涯蓝图》。"
                "报告要具体、克制、可执行，不要做绝对化判断，不要制造焦虑。必须包含七个主体模块和安全提醒。"
            ),
        },
        {
            "role": "user",
            "content": f"""
请生成 1200-1800 中文字符的报告，必须包含以下标题：
一、你5—10年后想成为的人
二、你的当前生涯状态判断
三、你的核心优势与主要风险
四、愿景、教育路径与当前行动的匹配度诊断
五、接下来6个月建议做的3—5件事
六、半年后我会问你的问题
七、一个值得长期思考的问题
安全提醒

学生信息：
- 年级：{response.grade}
- 专业：{response.collegeMajor}
- 倾向城市：{response.preferredCity}
- 当前困惑：{_list(response.careerConfusions)}
- 主要困惑描述：{response.mainConfusionText or "未填写"}
- 毕业后路径：{response.educationPath}
- 路径原因：{_list(response.educationPathReasons)}
- 路径确定程度：{response.educationCertainty}/5
- 读博意向：{response.phdIntention}
- 五年优先事项：{_list(response.fiveYearPriorities)}
- 目标行业：{_list(response.targetIndustries)}
- 未来角色：{response.futureRoleType}
- 生活偏好：{response.lifePreference}
- 十年后自我描述：{response.tenYearSelfDescription or "未填写"}
- 价值观前三项：{_list(response.topValuesRanked)}
- 已有准备：{_list(response.currentPreparations)}
- 缺少资源：{_list(response.missingResources)}
- 专业去向认知：{response.majorOutcomeAwareness}
- 岗位认知：{response.targetJobAwareness}
- 健康精力：{response.healthEnergyStatus}

画像判断：
- 当前状态：{profile.careerStateType}
- 命中依据：{_list(profile.evidence)}
- 优势标签：{_list(profile.strengthTags)}
- 风险标签：{_list(profile.riskTags)}
""".strip(),
        },
    ]
