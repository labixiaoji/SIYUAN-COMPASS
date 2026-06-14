from __future__ import annotations

import json

# These rules are a concise transcription of docs/生涯问卷更新版.docx.
# Do not expand them with additional personality or career assumptions.
QUESTION_RULES: dict[str, dict[str, object]] = {
    "grade": {
        "purpose": "结合教育路径，测算距离第一次就业的剩余时间，确定实现理想就业的准备周期。",
        "checks": ["mastersIntention", "phdIntention", "educationCertainty"],
    },
    "gender": {
        "purpose": "制定的生涯规划方案，需要结合性别特征有所调整",
        "checks": [],
    },
    "collegeMajor": {
        "purpose": "了解专业背景，判断如何与就业和生涯目标结合。",
        "checks": ["fiveYearIndustry", "fiveYearRole", "tenYearIndustry", "tenYearRole"],
    },
    "hometown": {
        "purpose": "结合未来5年、10年规划中选择的工作地点分析：距离远近、城市定位差距大小，结合自身规划，判断其就业后的生存难易程度，其性格底色",
        "checks": ["fiveYearCity", "tenYearCity"],
    },
    "mastersIntention": {
        "purpose": "了解是否读研，以及本校、国内其他高校或留学、是否转专业、是否符合条件和准备计划。",
        "checks": ["mastersPlan", "educationPathReasons", "educationCertainty"],
    },
    "mastersPlan": {
        "purpose": "了解读研方向、条件差距和准备工作，结合拟获取学位给出建议。",
        "checks": ["mastersIntention", "currentPreparations"],
    },
    "phdIntention": {
        "purpose": "了解是否读博，以及本校、国内其他高校或留学、是否转专业、是否符合条件和准备计划。",
        "checks": ["phdPlan", "educationPathReasons", "educationCertainty"],
    },
    "phdPlan": {
        "purpose": "了解读博方向、条件差距和准备工作，结合拟获取学位给出建议。",
        "checks": ["phdIntention", "currentPreparations"],
    },
    "educationPathReasons": {
        "purpose": "分析教育路径原因、在意因素、生涯思考和迷茫点，并与5年、10年规划对应。",
        "checks": ["mastersIntention", "phdIntention", "fiveYearIndustry", "fiveYearRole", "tenYearIndustry", "tenYearRole"],
    },
    "educationCertainty": {
        "purpose": "判断是否已经想清楚当前教育路径。",
        "checks": ["mastersPlan", "phdPlan", "careerConfusions"],
    },
    "fiveYearCity": {
        "purpose": "判断目标城市的宜居程度，以及是否与职业发展方向一致。",
        "checks": ["hometown", "fiveYearIndustry", "fiveYearRole"],
    },
    "fiveYearIncome": {
        "purpose": "该字段只作为原始问卷信息保存，不用于画像分析或职业路径判断。",
        "checks": [],
    },
    "fiveYearIndustry": {
        "purpose": "了解职业发展规划，检查与专业是否匹配；不匹配时检查相关积累。",
        "checks": ["collegeMajor", "currentPreparations"],
    },
    "fiveYearRole": {
        "purpose": "判断个人发展目标是否符合行业规律，并结合现有规划给出建议。",
        "checks": ["fiveYearIndustry", "currentPreparations", "targetJobAwareness"],
    },
    "fiveYearFamilyStatus": {
        "purpose": "了解亲密关系和生活状态偏好，并将其纳入整体生涯规划。",
        "checks": ["fiveYearCity", "fiveYearHousingPlan"],
    },
    "fiveYearHousingPlan": {
        "purpose": "了解居住状态偏好，但不评估购房能力或收入可行性。",
        "checks": ["fiveYearCity"],
    },
    "fiveYearHobbiesSkills": {
        "purpose": "判断爱好和核心技能能否规划为生涯第二曲线。",
        "checks": ["interestScores", "currentPreparations"],
    },
    "tenYearCity": {
        "purpose": "按5年城市问题的同一目的，判断长期城市与职业方向是否一致。",
        "checks": ["hometown", "fiveYearCity", "tenYearIndustry", "tenYearRole"],
    },
    "tenYearIncome": {
        "purpose": "该字段只作为原始问卷信息保存，不用于画像分析或职业路径判断。",
        "checks": [],
    },
    "tenYearIndustry": {
        "purpose": "按5年行业问题的同一目的，检查长期赛道与专业及已有积累是否匹配。",
        "checks": ["collegeMajor", "fiveYearIndustry", "currentPreparations"],
    },
    "tenYearRole": {
        "purpose": "按5年岗位问题的同一目的，判断长期岗位层级是否符合行业规律。",
        "checks": ["fiveYearRole", "tenYearIndustry", "currentPreparations"],
    },
    "tenYearFamilyStatus": {
        "purpose": "按5年生活状态问题的同一目的，将长期家庭生活偏好纳入生涯规划。",
        "checks": ["tenYearCity", "tenYearHousingPlan"],
    },
    "tenYearHousingPlan": {
        "purpose": "了解长期居住状态偏好，但不评估购房能力或收入可行性。",
        "checks": ["tenYearCity", "fiveYearHousingPlan"],
    },
    "tenYearHobbiesSkills": {
        "purpose": "判断长期爱好和核心技能能否形成生涯第二曲线。",
        "checks": ["fiveYearHobbiesSkills", "interestScores", "currentPreparations"],
    },
    "topValuesRanked": {
        "purpose": "了解最在意的价值，检查是否与生涯规划匹配，并辅助判断适合的工作方向。",
        "checks": ["fiveYearRole", "fiveYearFamilyStatus", "tenYearRole"],
    },
    "abilityScores": {
        "purpose": "判断适合的工作类型，以及能力自评是否与自我规划匹配；不匹配时给出建议。",
        "checks": ["fiveYearIndustry", "fiveYearRole", "tenYearRole"],
    },
    "interestScores": {
        "purpose": "判断适合的工作类型，以及兴趣是否与自我规划匹配；不匹配时给出建议。",
        "checks": ["fiveYearIndustry", "fiveYearRole", "tenYearRole"],
    },
    "currentPreparations": {
        "purpose": "基于生涯规划判断执行力，并检查努力方向是否正确。",
        "checks": ["mastersPlan", "phdPlan", "fiveYearIndustry", "fiveYearRole"],
    },
    "missingResources": {
        "purpose": "判断执行力和当前短板，并给出补齐方向、能力或资源的建议。",
        "checks": ["currentPreparations", "targetJobAwareness"],
    },
    "majorOutcomeAwareness": {
        "purpose": "辅助判断执行力、社交能力和信息索取能力。",
        "checks": ["jobInfoChannels", "currentPreparations"],
    },
    "targetJobAwareness": {
        "purpose": "判断岗位信息获取能力和执行力。",
        "checks": ["fiveYearRole", "jobInfoChannels", "currentPreparations"],
    },
    "jobInfoChannels": {
        "purpose": "了解信息渠道，给出需要补充的渠道建议，并作为了解行为特点的线索。",
        "checks": ["majorOutcomeAwareness", "targetJobAwareness"],
    },
    "healthEnergyStatus": {
        "purpose": "判断健康管理习惯和精力能否支撑生涯规划需求。",
        "checks": ["exerciseFrequency", "currentPreparations"],
    },
    "exerciseFrequency": {
        "purpose": "判断健康管理习惯能否支撑规划，并考虑将运动偏好结合进建议。",
        "checks": ["healthEnergyStatus"],
    },
    "careerConfusions": {
        "purpose": "确定报告重点回答的问题，并按所选困惑分析原因和给出建议。",
        "checks": ["mainConfusionText"],
    },
    "mainConfusionText": {
        "purpose": "补充学生最核心的困惑，作为报告重点和长期思考问题的依据。",
        "checks": ["careerConfusions"],
    },
}

CAREER_CONFUSION_RULES: dict[str, dict[str, str]] = {
    "不知道未来适合做什么": {
        "purpose": "分析是否对专业兴趣不足，以及是否缺少对自身和职业的了解。",
        "advice": "先了解能力、兴趣和专业出路，再通过实际行动验证。",
    },
    "纠结就业、读研、出国、读博": {
        "purpose": "说明各选择的目的、优缺点、难度及对生涯规划的影响。",
        "advice": "进行综合比较，形成Plan A、Plan B和切换条件。",
    },
    "不确定自己适合哪个行业": {
        "purpose": "分析对性格、能力、生涯规划和本专业行业出路的了解。",
        "advice": "先了解自身和本专业行业；不满足规划时再寻找交叉方向，并咨询本院校友。",
    },
    "不知道本专业未来有哪些出路": {
        "purpose": "分析专业出口的信息缺口。",
        "advice": "通过学长学姐、老师、AI、招聘会HR、实习和校友咨询了解工作并寻找兴趣点。",
    },
    "想提高求职 / 实习竞争力": {
        "purpose": "判断就业目标是否明确。",
        "advice": "明确目标岗位后有针对性地提高。",
    },
    "对未来收入、城市、生活状态感到焦虑": {
        "purpose": "区分焦虑来自经济、人际、工作生活节奏或其他压力。",
        "advice": "针对压力来源提高抗风险能力或调整预期。",
    },
    "家庭期待和个人想法不一致": {
        "purpose": "了解具体冲突，判断是家庭关系问题还是个人方案不够落地。",
        "advice": "根据具体冲突提出沟通、验证和现实调整建议。",
    },
    "想要更清楚地规划未来5—10年": {
        "purpose": "基于学生现有的5年、10年规划进行分析。",
        "advice": "从现有长期愿景倒推路径和行动，不替学生重新设定愿景。",
    },
}


def render_question_rules(selected_confusions: list[str]) -> str:
    selected_rules = {
        item: CAREER_CONFUSION_RULES[item]
        for item in selected_confusions
        if item in CAREER_CONFUSION_RULES
    }
    return json.dumps(
        {
            "source": "docs/生涯问卷更新版.docx",
            "questionRules": QUESTION_RULES,
            "selectedCareerConfusionRules": selected_rules,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
