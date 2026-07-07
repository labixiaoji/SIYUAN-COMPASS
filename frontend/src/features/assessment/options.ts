export const educationStageOptions = ["本科", "硕士", "博士"];
export const gradeOptionsByStage: Record<string, string[]> = {
  本科: ["大一", "大二", "大三", "大四"],
  硕士: ["研一", "研二", "研三及以上"],
  博士: ["博一", "博二", "博三", "博四及以上"]
};
export const gradeOptions = Object.values(gradeOptionsByStage).flat();
export const genderOptions = ["男", "女", "不便透露"];
export const studyIntentionOptions = ["明确考虑", "有一点兴趣", "不太考虑", "完全不考虑", "还不了解"];
export const undergraduatePathOptions = ["已保研", "正在准备考研", "准备出国读研", "直接就业", "考公或考编", "尚未确定"];
export const masterPathOptions = ["考虑读博", "准备就业", "考虑考公考编", "考虑出国", "尚未确定"];
export const doctoralCareerOptions = ["高校或科研院所", "企业研发", "博士后", "公务员或事业单位", "创业或自由职业", "其他发展方向"];
export const educationReasonOptions = ["提升学历和平台", "目标职业需要更高学历", "真正喜欢科研或学术探索", "想延缓就业压力", "家庭建议或外部期待", "想获得更稳定的发展路径", "想追求更高收入", "想换城市或拓宽机会", "还没有想清楚，只是暂时倾向", "其他"];
export const fiveYearFamilyOptions = ["单身专注学业事业", "有稳定伴侣暂不婚育", "结婚暂无生育", "结婚且有小孩", "暂不确定"];
export const tenYearFamilyOptions = ["单身独立生活", "已婚二人世界", "已婚并有子女", "事业优先、随缘婚恋", "暂不确定"];
export const valueOptions = ["高收入 / 经济回报", "稳定 / 安全感", "成长 / 学习新技能的机会", "意义感 / 帮助他人或创造价值", "人际关系", "自由 / 弹性 / 不被控制", "声望 / 被认可和尊重", "平衡 / 有足够时间给家庭和生活"];
export const failedCourseOptions = ["没有挂科或重修", "有过1门挂科或重修", "有过多门挂科或重修", "不便透露"];
export const secondMajorOptions = ["没有修读", "正在修读第二专业 / 辅修 / 微专业", "已经完成第二专业 / 辅修 / 双学位", "正在考虑修读"];
export const secondMajorProgressOptions = ["入门了解", "已修读部分核心课程", "已形成项目或作品", "已获得证书或学位", "暂不确定"];
export const secondMajorCareerInterestOptions = ["明确考虑相关方向", "可以作为备选方向", "只是兴趣拓展", "暂不考虑相关职业", "尚未确定"];
export const transferMajorOptions = ["没有转过专业", "转过一次专业", "转过多次专业", "正在考虑转专业"];
export const originalMajorSkillOptions = ["基本保留并愿意继续使用", "保留部分基础", "已经较少使用", "不想继续使用原专业方向", "不适用"];
export const praisedTraitOptions = ["记忆力强", "动手能力强", "表达能力强", "逻辑清晰", "反应迅速", "组织协调能力强", "有领导力", "审美能力强", "擅长某项才艺或技能", "学习速度快", "做事细致可靠", "共情和倾听能力强"];
export const preferredWorkStyleOptions = ["分析问题", "与人沟通", "动手实践", "组织管理", "创作表达", "规则细节"];
export const preparationOptions = ["修读相关课程", "参加科研 / 课题", "做过项目作品", "参加竞赛", "有实习经历", "参加社团 / 学生工作", "和老师、学长学姐或校友聊过", "参加过宣讲会 / 招聘会", "看过目标岗位招聘要求", "准备过简历", "投递过实习 / 工作", "还没有明显准备", "其他"];
export const missingResourceOptions = ["不知道方向", "不知道真实岗位要求", "缺技能", "缺项目 / 实习经历", "缺人脉和信息", "缺行动力", "缺信心", "缺时间", "缺对行业的了解", "缺清晰计划"];
export const majorOutcomeAwarenessOptions = ["比较了解", "听说过一些", "基本不了解", "完全不了解"];
export const targetJobAwarenessOptions = ["比较了解，并看过岗位 JD", "有一点了解", "只知道大概方向", "基本不了解", "还没有心仪岗位"];
export const jobInfoChannelOptions = ["宣讲会", "招聘会", "校友、老师、同学或其他熟人", "招聘网站", "短视频", "其他"];
export const healthEnergyOptions = ["很好，每周规律运动", "一般，偶尔运动", "较差，睡眠、压力或身体状态影响学习生活", "不想回答"];
export const executionStyleOptions = ["执行力较强，确定要做的事情通常能够完成", "执行力一般，重要事情能够推进，但容易受状态影响", "执行力较弱，即使知道事情重要，也经常难以启动"];
export const failureRecoveryOptions = ["需要一周以上恢复", "需要几天恢复", "一天左右可以恢复", "能迅速调整并寻找解决办法", "基本不受影响"];
export const selfDoubtOptions = ["经常自我怀疑", "遇到挫折时明显自我怀疑", "偶尔自我怀疑但能调整", "较少自我怀疑", "不确定"];
export const problemSolvingOptions = ["会主动拆解问题并寻找资源", "会先观察，再尝试解决", "需要他人推动才会行动", "容易回避问题", "不确定"];
export const supportNeedOptions = ["通常能自我恢复", "需要朋友或同学交流后恢复", "需要老师、家人或前辈指导", "需要较长时间陪伴和安慰", "不确定"];
export const highIntensityOptions = ["有过，并且能够较好承受", "有过，但只能短期承受", "有过，对身体或情绪影响较大", "没有类似经历", "不确定自己是否能够承受"];
export const routineWorkToleranceOptions = ["可以接受，并且擅长处理细节", "短期可以接受", "只接受部分事务性工作", "不喜欢重复、琐碎的工作", "完全无法接受"];
export const careerRiskPreferenceOptions = ["铁饭碗，收入和职业发展按部就班，规章制度严格", "较为宽松，发展更多取决于个人能力与行业环境，但有失业风险", "完全自主，但收入波动巨大，例如创业或自由职业"];
export const careerConfusionOptions = ["不知道未来适合做什么", "纠结就业、读研、出国、读博", "不确定自己适合哪个行业", "不知道本专业未来有哪些出路", "想提高求职 / 实习竞争力", "对未来收入、城市、生活状态感到焦虑", "家庭期待和个人想法不一致", "想要更清楚地规划未来5—10年", "其他"];
