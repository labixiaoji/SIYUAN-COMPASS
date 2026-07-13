import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createAssessmentJob, fetchAssessmentJob } from "../api/assessments";
import type { GenerationJobStatus } from "../api/assessments";
import { ChoiceGroup, RadioGroup, ScoreRows } from "../components/FormControls";
import {
  careerConfusionOptions,
  careerRiskPreferenceOptions,
  doctoralCareerOptions,
  educationStageOptions,
  educationReasonOptions,
  executionStyleOptions,
  failedCourseOptions,
  failureRecoveryOptions,
  fiveYearFamilyOptions,
  genderOptions,
  gradeOptionsByStage,
  healthEnergyOptions,
  highIntensityOptions,
  jobInfoChannelOptions,
  majorOutcomeAwarenessOptions,
  masterPathOptions,
  missingResourceOptions,
  originalMajorSkillOptions,
  praisedTraitOptions,
  preparationOptions,
  preferredWorkStyleOptions,
  problemSolvingOptions,
  routineWorkToleranceOptions,
  secondMajorCareerInterestOptions,
  secondMajorOptions,
  secondMajorProgressOptions,
  selfDoubtOptions,
  supportNeedOptions,
  targetJobAwarenessOptions,
  tenYearFamilyOptions,
  transferMajorOptions,
  undergraduatePathOptions,
  valueOptions
} from "../features/assessment/options";
import type { AssessmentResponseInput } from "../types/assessment";

const steps = ["基本信息", "教育路径", "未来愿景", "价值能力兴趣", "学业与经历", "行动与承压", "核心困惑"];
const generationSteps = [
  { progress: 5, label: "问卷已提交" },
  { progress: 10, label: "整理问卷" },
  { progress: 20, label: "生成用户画像" },
  { progress: 45, label: "校验画像" },
  { progress: 65, label: "生成生涯报告" },
  { progress: 88, label: "校验报告" },
  { progress: 100, label: "完成" }
];
const draftKey = "siyuan_assessment_draft_v2";
const prefillKey = "siyuan_assessment_prefill_v1";

const initialForm: AssessmentResponseInput = {
  studentName: "",
  studentNumber: "",
  contactInfo: "",
  educationStage: "本科",
  grade: "大三",
  gender: "不便透露",
  collegeMajor: "",
  hometown: "",
  mastersIntention: "尚未确定",
  mastersPlan: "",
  phdIntention: "暂不适用",
  phdPlan: "",
  doctoralCareerDirection: "",
  doctoralCareerOther: "",
  educationPathReasons: [],
  educationPathReasonOther: "",
  fiveYearCity: "",
  fiveYearIncome: "",
  fiveYearIndustry: "",
  fiveYearRole: "",
  fiveYearFamilyStatus: "暂不确定",
  fiveYearHousingPlan: "",
  fiveYearHobbiesSkills: "",
  tenYearCity: "",
  tenYearIncome: "",
  tenYearIndustry: "",
  tenYearRole: "",
  tenYearFamilyStatus: "暂不确定",
  tenYearHousingPlan: "",
  tenYearHobbiesSkills: "",
  topValuesRanked: [],
  abilityScores: { logic: 3, expression: 3, spatialDesign: 3, interpersonal: 3 },
  interestScores: { handsOn: 3, research: 3, creation: 3, helping: 3, leadership: 3, detail: 3 },
  currentGpa: "",
  gpaScale: "",
  majorRank: "",
  majorTotal: "",
  failedCourseStatus: "没有挂科或重修",
  hasSecondMajor: "没有修读",
  secondMajorName: "",
  secondMajorProgress: "",
  secondMajorCareerInterest: "",
  hasTransferredMajor: "没有转过专业",
  originalMajorName: "",
  transferReason: "",
  originalMajorRetainedSkills: "不适用",
  praisedTraits: [],
  traitEvidence: "",
  immersiveActivities: "",
  favoriteKnowledgeAreas: "",
  selfDrivenActivities: "",
  preferredWorkStyle: [],
  currentPreparations: [],
  currentPreparationOther: "",
  preparationDetails: "",
  missingResources: [],
  majorOutcomeAwareness: "听说过一些",
  targetJobAwareness: "只知道大概方向",
  jobInfoChannels: [],
  jobInfoChannelOther: "",
  healthEnergyStatus: "一般，偶尔运动",
  exerciseFrequency: "",
  longTermPersistence: 3,
  executionStyle: "执行力一般，重要事情能够推进，但容易受状态影响",
  failureRecoveryTime: "需要几天恢复",
  selfDoubtFrequency: "遇到挫折时明显自我怀疑",
  problemSolvingStyle: "会先观察，再尝试解决",
  supportNeed: "需要朋友或同学交流后恢复",
  highIntensityExperience: "没有类似经历",
  routineWorkTolerance: "短期可以接受",
  careerRiskPreference: "较为宽松，发展更多取决于个人能力与行业环境，但有失业风险",
  careerConfusions: [],
  careerConfusionOther: "",
  mainConfusionText: ""
};

const testForm: AssessmentResponseInput = {
  ...initialForm,
  studentName: "测试学生",
  studentNumber: "DEV-20260704",
  contactInfo: "dev@example.com",
  educationStage: "本科",
  grade: "大三",
  gender: "不便透露",
  collegeMajor: "计算机学院 / 软件工程",
  hometown: "上海",
  mastersIntention: "正在准备考研",
  mastersPlan: "计划优先准备本专业方向研究生，同时保留秋招实习作为备选。已经开始整理目标院校、考试科目和往年录取信息。",
  phdIntention: "暂不适用",
  phdPlan: "",
  doctoralCareerDirection: "",
  doctoralCareerOther: "",
  educationPathReasons: ["提升学历和平台", "目标职业需要更高学历", "还没有想清楚，只是暂时倾向"],
  educationPathReasonOther: "",
  fiveYearCity: "上海或杭州",
  fiveYearIncome: "希望收入能覆盖基本生活并保持一定储蓄",
  fiveYearIndustry: "互联网产品技术、企业数字化或教育科技",
  fiveYearRole: "产品经理、数据分析或研发转产品岗位",
  fiveYearFamilyStatus: "有稳定伴侣暂不婚育",
  fiveYearHousingPlan: "先租住在通勤方便的区域，重点保证学习和工作节奏稳定",
  fiveYearHobbiesSkills: "保持跑步和阅读习惯，形成数据分析、产品调研、结构化表达和项目推进能力。",
  tenYearCity: "长三角核心城市",
  tenYearIncome: "希望形成稳定上升的职业回报和抗风险能力",
  tenYearIndustry: "数字化服务、AI 应用或教育科技",
  tenYearRole: "能独立负责业务模块的产品负责人或复合型项目负责人",
  tenYearFamilyStatus: "暂不确定",
  tenYearHousingPlan: "根据职业发展和家庭安排决定，不把买房作为当前唯一目标",
  tenYearHobbiesSkills: "持续运动，保留写作和公开表达能力，形成跨团队协作、行业研究和长期学习能力。",
  topValuesRanked: ["成长 / 学习新技能的机会", "稳定 / 安全感", "自由 / 弹性 / 不被控制"],
  abilityScores: { logic: 4, expression: 4, spatialDesign: 2, interpersonal: 3 },
  interestScores: { handsOn: 3, research: 4, creation: 4, helping: 3, leadership: 3, detail: 4 },
  currentGpa: "3.55",
  gpaScale: "4.0",
  majorRank: "18",
  majorTotal: "120",
  failedCourseStatus: "没有挂科或重修",
  hasSecondMajor: "没有修读",
  secondMajorName: "",
  secondMajorProgress: "",
  secondMajorCareerInterest: "",
  hasTransferredMajor: "没有转过专业",
  originalMajorName: "",
  transferReason: "",
  originalMajorRetainedSkills: "不适用",
  praisedTraits: ["逻辑清晰", "表达能力强", "做事细致可靠"],
  traitEvidence: "课程项目答辩中负责讲解方案，老师反馈逻辑比较清楚；竞赛中整理过需求文档和演示材料。",
  immersiveActivities: "长时间整理资料、分析一个产品为什么好用，以及把复杂问题写成清楚的文档。",
  favoriteKnowledgeAreas: "产品设计、数据分析、AI 应用、教育科技和组织协作。",
  selfDrivenActivities: "会主动体验新工具，整理笔记，也会帮同学把项目思路梳理清楚。",
  preferredWorkStyle: ["分析问题", "创作表达"],
  currentPreparations: ["修读相关课程", "做过项目作品", "参加竞赛", "看过目标岗位招聘要求", "准备过简历"],
  currentPreparationOther: "",
  preparationDetails: "已经修过数据库、软件工程和数据分析课程；看过产品经理和数据分析岗位 JD，发现自己还缺实习经历和更完整的作品集。",
  missingResources: ["不知道真实岗位要求", "缺项目 / 实习经历", "缺清晰计划"],
  majorOutcomeAwareness: "听说过一些",
  targetJobAwareness: "有一点了解",
  jobInfoChannels: ["校友、老师、同学或其他熟人", "招聘网站", "宣讲会"],
  jobInfoChannelOther: "",
  healthEnergyStatus: "一般，偶尔运动",
  exerciseFrequency: "每周 1-2 次，每次 30 分钟，主要是慢跑和散步。",
  longTermPersistence: 4,
  executionStyle: "执行力一般，重要事情能够推进，但容易受状态影响",
  failureRecoveryTime: "需要几天恢复",
  selfDoubtFrequency: "遇到挫折时明显自我怀疑",
  problemSolvingStyle: "会先观察，再尝试解决",
  supportNeed: "需要朋友或同学交流后恢复",
  highIntensityExperience: "有过，但只能短期承受",
  routineWorkTolerance: "短期可以接受",
  careerRiskPreference: "较为宽松，发展更多取决于个人能力与行业环境，但有失业风险",
  careerConfusions: ["纠结就业、读研、出国、读博", "不确定自己适合哪个行业", "想提高求职 / 实习竞争力"],
  careerConfusionOther: "",
  mainConfusionText: "我不知道应该继续考研提升学历，还是尽早找实习进入产品或数据相关岗位。"
};

type FieldKey = keyof AssessmentResponseInput;
type FieldErrors = Partial<Record<FieldKey, string>>;
type AssessmentPrefill = Partial<AssessmentResponseInput> & Record<string, unknown>;

const requiredFields: Array<{
  key: FieldKey;
  step: number;
  message: string;
  validate?: (form: AssessmentResponseInput) => boolean;
}> = [
  { key: "contactInfo", step: 0, message: "请填写联系方式" },
  { key: "educationStage", step: 0, message: "请选择学历阶段" },
  { key: "grade", step: 0, message: "请选择年级" },
  { key: "gender", step: 0, message: "请选择性别" },
  { key: "collegeMajor", step: 0, message: "请填写学院和专业" },
  { key: "hometown", step: 0, message: "请填写家乡或主要成长地" },
  { key: "mastersIntention", step: 1, message: "请选择本科毕业后的主要计划", validate: (form) => form.educationStage !== "本科" || hasText(form.mastersIntention) },
  { key: "phdIntention", step: 1, message: "请选择硕士毕业后的主要考虑", validate: (form) => form.educationStage !== "硕士" || hasText(form.phdIntention) },
  { key: "doctoralCareerDirection", step: 1, message: "请选择博士阶段后的发展方向", validate: (form) => form.educationStage !== "博士" || hasText(form.doctoralCareerDirection) },
  { key: "doctoralCareerOther", step: 1, message: "请填写其他发展方向", validate: (form) => form.doctoralCareerDirection !== "其他发展方向" || hasText(form.doctoralCareerOther) },
  { key: "educationPathReasons", step: 1, message: "请选择1—3项教育路径原因", validate: (form) => form.educationPathReasons.length > 0 && form.educationPathReasons.length <= 3 },
  { key: "educationPathReasonOther", step: 1, message: "请填写其他教育路径原因", validate: (form) => !form.educationPathReasons.includes("其他") || hasText(form.educationPathReasonOther) },
  { key: "fiveYearCity", step: 2, message: "请填写5年后希望生活或工作的城市" },
  { key: "fiveYearIncome", step: 2, message: "请填写5年后希望达到的收入状态" },
  { key: "fiveYearIndustry", step: 2, message: "请填写5年后希望进入或深耕的行业领域" },
  { key: "fiveYearRole", step: 2, message: "请填写5年后希望从事的岗位或角色" },
  { key: "fiveYearFamilyStatus", step: 2, message: "请选择5年后的家庭或亲密关系状态" },
  { key: "fiveYearHousingPlan", step: 2, message: "请填写5年后的居住或住房状态" },
  { key: "fiveYearHobbiesSkills", step: 2, message: "请填写5年后希望保留的爱好或核心技能" },
  { key: "tenYearCity", step: 2, message: "请填写10年后希望生活或工作的城市" },
  { key: "tenYearIncome", step: 2, message: "请填写10年后希望达到的收入状态" },
  { key: "tenYearIndustry", step: 2, message: "请填写10年后希望进入或深耕的行业领域" },
  { key: "tenYearRole", step: 2, message: "请填写10年后希望从事的岗位或角色" },
  { key: "tenYearFamilyStatus", step: 2, message: "请选择10年后的家庭或亲密关系状态" },
  { key: "tenYearHousingPlan", step: 2, message: "请填写10年后的居住或住房状态" },
  { key: "tenYearHobbiesSkills", step: 2, message: "请填写10年后希望保留的爱好或核心技能" },
  { key: "topValuesRanked", step: 3, message: "请选出最看重的3项价值观", validate: (form) => form.topValuesRanked.length === 3 },
  { key: "praisedTraits", step: 3, message: "请至少选择1项常被称赞的特质", validate: (form) => form.praisedTraits.length > 0 && form.praisedTraits.length <= 4 },
  { key: "traitEvidence", step: 3, message: "请填写特质相关成果" },
  { key: "immersiveActivities", step: 3, message: "请填写能让你长时间沉浸的事情" },
  { key: "favoriteKnowledgeAreas", step: 3, message: "请填写喜欢学习的知识领域" },
  { key: "selfDrivenActivities", step: 3, message: "请填写无外部奖励也愿意完成的事情" },
  { key: "preferredWorkStyle", step: 3, message: "请选择1—2项更偏好的工作方式", validate: (form) => form.preferredWorkStyle.length > 0 && form.preferredWorkStyle.length <= 2 },
  { key: "currentGpa", step: 4, message: "请填写当前 GPA" },
  { key: "gpaScale", step: 4, message: "请填写 GPA 满分" },
  { key: "majorRank", step: 4, message: "请填写专业排名" },
  { key: "majorTotal", step: 4, message: "请填写专业总人数" },
  { key: "failedCourseStatus", step: 4, message: "请选择是否有挂科或重修经历" },
  { key: "hasSecondMajor", step: 4, message: "请选择是否修读第二专业" },
  { key: "hasTransferredMajor", step: 4, message: "请选择是否有转专业经历" },
  { key: "currentPreparations", step: 4, message: "请至少选择1项已做准备", validate: (form) => form.currentPreparations.length > 0 },
  { key: "currentPreparationOther", step: 4, message: "请填写其他已做准备", validate: (form) => !form.currentPreparations.includes("其他") || hasText(form.currentPreparationOther) },
  { key: "preparationDetails", step: 4, message: "请具体展开说说已做的准备" },
  { key: "missingResources", step: 5, message: "请至少选择1项目前最缺的资源", validate: (form) => form.missingResources.length > 0 && form.missingResources.length <= 3 },
  { key: "majorOutcomeAwareness", step: 5, message: "请选择是否了解本专业毕业生去向" },
  { key: "targetJobAwareness", step: 5, message: "请选择是否了解心仪岗位要求" },
  { key: "jobInfoChannels", step: 5, message: "请至少选择1个职业或招聘信息渠道", validate: (form) => form.jobInfoChannels.length > 0 },
  { key: "jobInfoChannelOther", step: 5, message: "请填写其他职业信息渠道", validate: (form) => !form.jobInfoChannels.includes("其他") || hasText(form.jobInfoChannelOther) },
  { key: "healthEnergyStatus", step: 5, message: "请选择身体健康和精力状态" },
  { key: "executionStyle", step: 5, message: "请选择执行力自评" },
  { key: "failureRecoveryTime", step: 5, message: "请选择失败后的恢复速度" },
  { key: "selfDoubtFrequency", step: 5, message: "请选择自我怀疑情况" },
  { key: "problemSolvingStyle", step: 5, message: "请选择面对问题时的处理方式" },
  { key: "supportNeed", step: 5, message: "请选择恢复时需要的支持" },
  { key: "highIntensityExperience", step: 5, message: "请选择高强度投入经历" },
  { key: "routineWorkTolerance", step: 5, message: "请选择事务性工作的接受程度" },
  { key: "careerRiskPreference", step: 5, message: "请选择职业风险偏好" },
  { key: "careerConfusions", step: 6, message: "请至少选择1项当前生涯困惑", validate: (form) => form.careerConfusions.length > 0 && form.careerConfusions.length <= 3 },
  { key: "careerConfusionOther", step: 6, message: "请填写其他生涯困惑", validate: (form) => !form.careerConfusions.includes("其他") || hasText(form.careerConfusionOther) }
];

const requiredFieldKeys = new Set<FieldKey>(requiredFields.map((field) => field.key));
const requiredFieldSteps = new Map<FieldKey, number>(requiredFields.map((field) => [field.key, field.step]));

function hasText(value: unknown) {
  return typeof value === "string" && value.trim().length > 0;
}

function validateForm(form: AssessmentResponseInput): FieldErrors {
  return requiredFields.reduce<FieldErrors>((errors, field) => {
    const valid = field.validate ? field.validate(form) : hasText(form[field.key]);
    if (!valid) {
      errors[field.key] = field.message;
    }
    return errors;
  }, {});
}

function formFromPartial(raw: AssessmentPrefill): AssessmentResponseInput {
  const next = { ...initialForm } as AssessmentResponseInput;
  (Object.keys(initialForm) as FieldKey[]).forEach((key) => {
    if (key in raw) {
      next[key] = raw[key] as never;
    }
  });
  next.abilityScores = {
    ...initialForm.abilityScores,
    ...(typeof raw.abilityScores === "object" && raw.abilityScores ? raw.abilityScores : {})
  };
  next.interestScores = {
    ...initialForm.interestScores,
    ...(typeof raw.interestScores === "object" && raw.interestScores ? raw.interestScores : {})
  };
  const rawPreferredWorkStyle = raw.preferredWorkStyle as unknown;
  next.preferredWorkStyle = Array.isArray(rawPreferredWorkStyle)
    ? rawPreferredWorkStyle.filter((item): item is string => typeof item === "string").slice(0, 2)
    : typeof rawPreferredWorkStyle === "string" && rawPreferredWorkStyle.trim()
      ? [rawPreferredWorkStyle]
      : [];
  return next;
}

function scrollToField(key: FieldKey) {
  window.setTimeout(() => {
    document.querySelector(`[data-field="${key}"]`)?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, 80);
}

function jobStatusLabel(job: GenerationJobStatus) {
  if (job.status === "failed") return "生成失败";
  if (job.status === "cancelled") return "已取消生成";
  if (job.status === "success") return "生成成功";
  if (job.stage.includes("report")) return "正在生成报告";
  if (job.stage.includes("profile")) return "正在生成画像";
  return "问卷已提交";
}

function hasFieldErrors(error: unknown): error is Error & { fieldErrors: Record<string, string> } {
  return error instanceof Error && "fieldErrors" in error && !!error.fieldErrors;
}

export function AssessmentPage() {
  const navigate = useNavigate();
  const showDevTools = import.meta.env.DEV;
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<AssessmentResponseInput>(initialForm);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [draftReady, setDraftReady] = useState(false);
  const [draftDirty, setDraftDirty] = useState(false);
  const [generationJob, setGenerationJob] = useState<GenerationJobStatus | null>(null);

  useEffect(() => {
    const prefill = window.localStorage.getItem(prefillKey);
    if (prefill) {
      try {
        const parsed = JSON.parse(prefill) as AssessmentPrefill;
        setForm(formFromPartial(parsed));
        setDraftDirty(true);
        window.localStorage.removeItem(prefillKey);
        window.localStorage.removeItem(draftKey);
        setDraftReady(true);
        return;
      } catch {
        window.localStorage.removeItem(prefillKey);
      }
    }

    const saved = window.localStorage.getItem(draftKey);
    if (saved) {
      try {
        const parsed = JSON.parse(saved) as AssessmentPrefill;
        if (window.confirm("检测到未提交草稿，是否恢复？")) {
          setForm(formFromPartial(parsed));
          setDraftDirty(true);
        } else {
          window.localStorage.removeItem(draftKey);
        }
      } catch {
        window.localStorage.removeItem(draftKey);
      }
    }
    setDraftReady(true);
  }, []);

  useEffect(() => {
    if (!draftReady || !draftDirty || submitting) return;
    window.localStorage.setItem(draftKey, JSON.stringify(form));
  }, [draftDirty, draftReady, form, submitting]);

  const patch = <K extends keyof AssessmentResponseInput>(key: K, value: AssessmentResponseInput[K]) => {
    setDraftDirty(true);
    setForm((prev) => ({ ...prev, [key]: value }));
    setFieldErrors((prev) => {
      if (!prev[key]) return prev;
      const next = { ...prev };
      delete next[key];
      return next;
    });
  };

  function markErrors(nextErrors: FieldErrors) {
    setFieldErrors(nextErrors);
    const entries = Object.entries(nextErrors) as Array<[FieldKey, string]>;
    if (entries.length === 0) return false;

    const [firstKey] = entries[0];
    setError(`还有 ${entries.length} 项未完成，请先补充标红的问题。`);
    setStep(requiredFieldSteps.get(firstKey) ?? step);
    scrollToField(firstKey);
    return true;
  }

  async function submit() {
    if (submitting) return;
    const nextErrors = validateForm(form);
    if (markErrors(nextErrors)) return;

    setSubmitting(true);
    setError("");
    setFieldErrors({});
    setGenerationJob(null);

    try {
      const created = await createAssessmentJob(form);
      setGenerationJob({
        jobId: created.jobId,
        status: "queued",
        stage: "queued",
        progress: 5,
        message: "问卷已接收，等待开始分析。"
      });

      for (let attempt = 0; attempt < 600; attempt += 1) {
        const job = await fetchAssessmentJob(created.jobId);
        setGenerationJob(job);

        if (job.status === "success" && job.reportId && job.userId) {
          window.localStorage.removeItem(draftKey);
          navigate(`/reports/${job.reportId}`);
          return;
        }

        if (job.status === "failed") {
          throw new Error(job.error ? `${job.message} ${job.error}` : job.message);
        }

        if (job.status === "cancelled") {
          throw new Error(job.message || "报告生成已取消。");
        }

        await new Promise((resolve) => window.setTimeout(resolve, 1000));
      }

      throw new Error("生成等待时间超过10分钟，请检查后端日志或稍后重试。");
    } catch (caught) {
      if (hasFieldErrors(caught)) {
        const serverFieldErrors = caught.fieldErrors as FieldErrors;
        markErrors(serverFieldErrors);
        return;
      }
      setError(caught instanceof Error ? caught.message : "提交失败，请稍后重试。");
    } finally {
      setSubmitting(false);
    }
  }

  function backToEdit() {
    setGenerationJob(null);
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function fillTestForm() {
    setForm(testForm);
    setFieldErrors({});
    setError("");
    setGenerationJob(null);
    setSubmitting(false);
    setDraftDirty(true);
    setStep(0);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function goToStep(nextStep: number) {
    setStep(nextStep);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const currentGradeOptions = gradeOptionsByStage[form.educationStage] ?? gradeOptionsByStage["本科"];

  function patchEducationStage(educationStage: string) {
    const nextGradeOptions = gradeOptionsByStage[educationStage] ?? gradeOptionsByStage["本科"];
    setDraftDirty(true);
    setForm((prev) => ({
      ...prev,
      educationStage,
      grade: nextGradeOptions.includes(prev.grade) ? prev.grade : nextGradeOptions[0],
      mastersIntention: educationStage === "本科" ? (undergraduatePathOptions.includes(prev.mastersIntention) ? prev.mastersIntention : "尚未确定") : `已在读${educationStage}，不适用`,
      mastersPlan: educationStage === "本科" ? prev.mastersPlan : "",
      phdIntention: educationStage === "硕士" ? (masterPathOptions.includes(prev.phdIntention) ? prev.phdIntention : "尚未确定") : educationStage === "博士" ? "已在读博士，不适用" : "暂不适用",
      phdPlan: educationStage === "硕士" || educationStage === "博士" ? prev.phdPlan : "",
      doctoralCareerDirection: educationStage === "博士" ? prev.doctoralCareerDirection || doctoralCareerOptions[0] : "",
      doctoralCareerOther: educationStage === "博士" ? prev.doctoralCareerOther : ""
    }));
    setFieldErrors((prev) => {
      const next = { ...prev };
      delete next.educationStage;
      delete next.grade;
      delete next.mastersIntention;
      delete next.phdIntention;
      delete next.doctoralCareerDirection;
      return next;
    });
  }

  function patchSecondMajorStatus(hasSecondMajor: string) {
    setDraftDirty(true);
    setForm((prev) => ({
      ...prev,
      hasSecondMajor,
      secondMajorName: hasSecondMajor === "没有修读" ? "" : prev.secondMajorName,
      secondMajorProgress: hasSecondMajor === "没有修读" ? "" : prev.secondMajorProgress,
      secondMajorCareerInterest: hasSecondMajor === "没有修读" ? "" : prev.secondMajorCareerInterest
    }));
    setFieldErrors((prev) => {
      if (!prev.hasSecondMajor) return prev;
      const next = { ...prev };
      delete next.hasSecondMajor;
      return next;
    });
  }

  function patchTransferredMajorStatus(hasTransferredMajor: string) {
    setDraftDirty(true);
    setForm((prev) => ({
      ...prev,
      hasTransferredMajor,
      originalMajorName: hasTransferredMajor === "没有转过专业" ? "" : prev.originalMajorName,
      transferReason: hasTransferredMajor === "没有转过专业" ? "" : prev.transferReason,
      originalMajorRetainedSkills: hasTransferredMajor === "没有转过专业" ? "不适用" : prev.originalMajorRetainedSkills
    }));
    setFieldErrors((prev) => {
      if (!prev.hasTransferredMajor) return prev;
      const next = { ...prev };
      delete next.hasTransferredMajor;
      return next;
    });
  }

  function fieldClass(key: FieldKey) {
    return `field ${fieldErrors[key] ? "field-invalid" : ""}`;
  }

  function fieldError(key: FieldKey) {
    return fieldErrors[key] ? <div className="field-error">{fieldErrors[key]}</div> : null;
  }

  function requiredLabel(key: FieldKey, label: string) {
    return (
      <>
        {label}
        {requiredFieldKeys.has(key) && <span className="required-mark">*</span>}
      </>
    );
  }

  function questionFlags(_key: FieldKey, multiple = false, max?: number) {
    const flags = [
      multiple ? "多选" : "",
      max ? `最多选择 ${max} 项` : ""
    ].filter(Boolean);
    return flags.length > 0 ? <div className="question-flags">{flags.join("｜")}</div> : null;
  }

  const textField = (
    key: keyof AssessmentResponseInput,
    label: string,
    multiline = false,
    placeholder = ""
  ) => (
    <div className={fieldClass(key)} data-field={key}>
      <label>{requiredLabel(key, label)}</label>
      {questionFlags(key)}
      {multiline ? (
        <textarea
          className="textarea"
          placeholder={placeholder}
          value={(form[key] as string | undefined) || ""}
          onChange={(event) => patch(key, event.target.value as never)}
        />
      ) : (
        <input
          className="input"
          placeholder={placeholder}
          value={(form[key] as string | undefined) || ""}
          onChange={(event) => patch(key, event.target.value as never)}
        />
      )}
      {fieldError(key)}
    </div>
  );

  const radioField = (key: FieldKey, label: string, options: string[], hint = "") => (
    <div className={fieldClass(key)} data-field={key}>
      <label>{requiredLabel(key, label)}</label>
      {questionFlags(key)}
      {hint && <div className="hint">{hint}</div>}
      <RadioGroup options={options} value={(form[key] as string | undefined) || ""} onChange={(value) => patch(key, value as never)} />
      {fieldError(key)}
    </div>
  );

  const choiceField = (key: FieldKey, label: string, options: string[], hint = "", max?: number) => (
    <div className={fieldClass(key)} data-field={key}>
      <label>{requiredLabel(key, label)}</label>
      {questionFlags(key, true, max)}
      {hint && <div className="hint">{hint}</div>}
      <ChoiceGroup options={options} values={(form[key] as string[] | undefined) || []} max={max} onChange={(value) => patch(key, value as never)} />
      {fieldError(key)}
    </div>
  );

  return (
    <main className="shell page">
      <div className="page-title">
        <h1>生涯规划问卷</h1>
        <p>请尽量填写具体。你的回答仅用于生成个人生涯规划报告和产品优化分析。</p>
      </div>

      {showDevTools && (
        <section className="dev-tools-panel">
          <div>
            <strong>开发测试</strong>
            <span>一键填充完整问卷数据，用来快速检查前端流程。</span>
          </div>
          <button className="button secondary" disabled={submitting} onClick={fillTestForm}>填充测试数据</button>
        </section>
      )}

      <div className="form-layout">
        <aside className="panel steps">
          {steps.map((name, index) => (
            <button
              aria-current={index === step ? "step" : undefined}
              className={`step ${index === step ? "active" : ""}`}
              disabled={submitting}
              key={name}
              onClick={() => goToStep(index)}
              type="button"
            >
              {index + 1}. {name}
            </button>
          ))}
        </aside>

        <section className="panel">
          {step === 0 && (
            <>
              <p className="hint">以下信息仅用于报告归属、测试回访和系统优化，不会用于公开展示。</p>
              {textField("studentName", "你的姓名是？（选填）", false, "例如：张同学")}
              {textField("studentNumber", "你的学号是？（选填）", false, "用于区分同名学生")}
              {textField("contactInfo", "你的联系方式是？", false, "手机号、邮箱或微信号均可")}
              <div className={fieldClass("educationStage")} data-field="educationStage">
                <label>{requiredLabel("educationStage", "你当前的学历阶段是？")}</label>
                {questionFlags("educationStage")}
                <RadioGroup options={educationStageOptions} value={form.educationStage} onChange={patchEducationStage} />
                {fieldError("educationStage")}
              </div>
              <div className={fieldClass("grade")} data-field="grade">
                <label>{requiredLabel("grade", "你的年级是？")}</label>
                {questionFlags("grade")}
                <RadioGroup options={currentGradeOptions} value={form.grade} onChange={(value) => patch("grade", value)} />
                {fieldError("grade")}
              </div>
              <div className={fieldClass("gender")} data-field="gender">
                <label>{requiredLabel("gender", "你的性别是？")}</label>
                {questionFlags("gender")}
                <RadioGroup options={genderOptions} value={form.gender} onChange={(value) => patch("gender", value)} />
                {fieldError("gender")}
              </div>
              {textField("collegeMajor", "你的学院和专业是？", false, "例如：计算机学院 / 计算机科学与技术")}
              {textField("hometown", "你的家乡或主要成长地是？", false, "例如：上海")}
            </>
          )}

          {step === 1 && (
            <>
              {form.educationStage === "本科" && (
                <>
                  {radioField("mastersIntention", "本科毕业后的主要计划是？", undergraduatePathOptions)}
                  {textField("mastersPlan", "围绕这个计划，你目前有什么初步规划？", true, "可填写保研、考研、出国、就业或考公考编的准备情况")}
                </>
              )}
              {form.educationStage === "硕士" && (
                <>
                  {radioField("phdIntention", "硕士毕业后的主要考虑是什么？", masterPathOptions)}
                  {textField("phdPlan", "围绕这个选择，你目前有什么初步规划？", true, "可填写读博、就业、考公考编、出国的目标、差距和准备情况")}
                </>
              )}
              {form.educationStage === "博士" && (
                <>
                  {radioField("doctoralCareerDirection", "博士阶段后的主要发展方向是？", doctoralCareerOptions)}
                  {form.doctoralCareerDirection === "其他发展方向" && textField("doctoralCareerOther", "请填写其他发展方向")}
                  {textField("phdPlan", "围绕这个方向，你目前有什么初步规划？", true, "可填写研究方向、目标单位、博士后、企业研发、考公考编或其他准备情况")}
                </>
              )}
              <div className={fieldClass("educationPathReasons")} data-field="educationPathReasons">
                <label>{requiredLabel("educationPathReasons", "你考虑上述教育路径的主要原因是什么？")}</label>
                {questionFlags("educationPathReasons", true, 3)}
                <ChoiceGroup options={educationReasonOptions} values={form.educationPathReasons} max={3} onChange={(value) => patch("educationPathReasons", value)} />
                {fieldError("educationPathReasons")}
              </div>
              {form.educationPathReasons.includes("其他") && textField("educationPathReasonOther", "请填写其他原因", true)}
            </>
          )}

          {step === 2 && (
            <>
              <h2 className="form-subtitle">5年后的愿景</h2>
              {textField("fiveYearCity", "你希望生活或工作的城市是？")}
              {textField("fiveYearIncome", "你希望达到怎样的收入状态？", false, "可填写月收入、年收入或生活水平")}
              {textField("fiveYearIndustry", "你希望进入或深耕什么行业、领域？")}
              {textField("fiveYearRole", "你希望从事什么岗位、承担什么角色？")}
              <div className={fieldClass("fiveYearFamilyStatus")} data-field="fiveYearFamilyStatus">
                <label>{requiredLabel("fiveYearFamilyStatus", "你期待的家庭或亲密关系状态是？")}</label>
                {questionFlags("fiveYearFamilyStatus")}
                <RadioGroup options={fiveYearFamilyOptions} value={form.fiveYearFamilyStatus} onChange={(value) => patch("fiveYearFamilyStatus", value)} />
                {fieldError("fiveYearFamilyStatus")}
              </div>
              {textField("fiveYearHousingPlan", "你期待怎样的居住或住房状态？")}
              {textField("fiveYearHobbiesSkills", "你希望保留哪些爱好，或形成哪些核心技能？", true)}

              <h2 className="form-subtitle">10年后的愿景</h2>
              {textField("tenYearCity", "你希望生活或工作的城市是？")}
              {textField("tenYearIncome", "你希望达到怎样的收入状态？", false, "可填写月收入、年收入或生活水平")}
              {textField("tenYearIndustry", "你希望进入或深耕什么行业、领域？")}
              {textField("tenYearRole", "你希望从事什么岗位、承担什么角色？")}
              <div className={fieldClass("tenYearFamilyStatus")} data-field="tenYearFamilyStatus">
                <label>{requiredLabel("tenYearFamilyStatus", "你期待的家庭或亲密关系状态是？")}</label>
                {questionFlags("tenYearFamilyStatus")}
                <RadioGroup options={tenYearFamilyOptions} value={form.tenYearFamilyStatus} onChange={(value) => patch("tenYearFamilyStatus", value)} />
                {fieldError("tenYearFamilyStatus")}
              </div>
              {textField("tenYearHousingPlan", "你期待怎样的居住或住房状态？")}
              {textField("tenYearHobbiesSkills", "你希望保留哪些爱好，或形成哪些核心技能？", true)}
            </>
          )}

          {step === 3 && (
            <>
              <div className={fieldClass("topValuesRanked")} data-field="topValuesRanked">
                <label>{requiredLabel("topValuesRanked", "请选出你最看重的3项价值观。")}</label>
                {questionFlags("topValuesRanked", true, 3)}
                <ChoiceGroup options={valueOptions} values={form.topValuesRanked} max={3} onChange={(value) => patch("topValuesRanked", value)} />
                {fieldError("topValuesRanked")}
              </div>
              <div className="field">
                <label>能力自评：1 = 很不符合，5 = 非常符合。<span className="required-mark">*</span></label>
                <ScoreRows rows={[["logic", "数学、逻辑推理"], ["expression", "写作、表达、讲故事"], ["spatialDesign", "空间、方向、设计"], ["interpersonal", "识人、沟通、理解情绪"]]} values={form.abilityScores} onChange={(key, value) => patch("abilityScores", { ...form.abilityScores, [key]: value })} />
              </div>
              <div className="field">
                <label>兴趣倾向：1 = 很不喜欢，5 = 非常喜欢。<span className="required-mark">*</span></label>
                <ScoreRows rows={[["handsOn", "动手操作、修理工具"], ["research", "研究问题、分析数据"], ["creation", "创作、写作、设计或表达"], ["helping", "帮助他人、教学或咨询"], ["leadership", "销售、领导或影响他人"], ["detail", "按规则整理信息、处理细节"]]} values={form.interestScores} onChange={(key, value) => patch("interestScores", { ...form.interestScores, [key]: value })} />
              </div>
              {choiceField("praisedTraits", "从小到大，你最常被他人称赞的特质是什么？", praisedTraitOptions, "最多选择4项，请优先选择有真实例子的特质。", 4)}
              {textField("traitEvidence", "你是否凭借这些特质取得过相关成果？", true, "例如：获奖、证书、项目成果、作品、组织活动经历")}
              {textField("immersiveActivities", "哪些事情能让你长时间沉浸其中？", true)}
              {textField("favoriteKnowledgeAreas", "你喜欢学习哪方面的知识？", true)}
              {textField("selfDrivenActivities", "哪些事情即使没有外部奖励，你也愿意主动完成？", true)}
              {choiceField("preferredWorkStyle", "你更喜欢哪类工作方式？", preferredWorkStyleOptions, "", 2)}
            </>
          )}

          {step === 4 && (
            <>
              <h2 className="form-subtitle">学业竞争力</h2>
              <div className="field-grid">
                {textField("currentGpa", "当前 GPA", false, "例如：3.6")}
                {textField("gpaScale", "GPA 满分", false, "例如：4.0 或 5.0")}
                {textField("majorRank", "专业排名", false, "例如：12")}
                {textField("majorTotal", "专业总人数", false, "例如：120")}
              </div>
              {radioField("failedCourseStatus", "是否有挂科或重修经历？", failedCourseOptions)}

              <h2 className="form-subtitle">第二专业与转专业</h2>
              <div className={fieldClass("hasSecondMajor")} data-field="hasSecondMajor">
                <label>{requiredLabel("hasSecondMajor", "是否修读第二专业、辅修、微专业或双学位？")}</label>
                {questionFlags("hasSecondMajor")}
                <RadioGroup options={secondMajorOptions} value={form.hasSecondMajor} onChange={patchSecondMajorStatus} />
                {fieldError("hasSecondMajor")}
              </div>
              {form.hasSecondMajor !== "没有修读" && (
                <>
                  {textField("secondMajorName", "第二专业或辅修名称", false, "例如：金融学、数据科学、设计学")}
                  {radioField("secondMajorProgress", "第二专业修读程度", secondMajorProgressOptions)}
                  {radioField("secondMajorCareerInterest", "是否考虑从事第二专业相关方向？", secondMajorCareerInterestOptions)}
                </>
              )}
              <div className={fieldClass("hasTransferredMajor")} data-field="hasTransferredMajor">
                <label>{requiredLabel("hasTransferredMajor", "是否有转专业经历？")}</label>
                {questionFlags("hasTransferredMajor")}
                <RadioGroup options={transferMajorOptions} value={form.hasTransferredMajor} onChange={patchTransferredMajorStatus} />
                {fieldError("hasTransferredMajor")}
              </div>
              {form.hasTransferredMajor !== "没有转过专业" && (
                <>
                  {textField("originalMajorName", "原专业名称", false)}
                  {textField("transferReason", "转专业或考虑转专业的原因", true)}
                  {radioField("originalMajorRetainedSkills", "原专业相关知识和能力是否仍然保留？", originalMajorSkillOptions)}
                </>
              )}

              <h2 className="form-subtitle">已有准备</h2>
              <div className={fieldClass("currentPreparations")} data-field="currentPreparations">
                <label>{requiredLabel("currentPreparations", "为了未来目标，你已经做过哪些准备？")}</label>
                {questionFlags("currentPreparations", true)}
                <ChoiceGroup options={preparationOptions} values={form.currentPreparations} onChange={(value) => patch("currentPreparations", value)} />
                {fieldError("currentPreparations")}
              </div>
              {form.currentPreparations.includes("其他") && textField("currentPreparationOther", "请填写其他已做准备", true)}
              {textField("preparationDetails", "请具体展开说说这些准备。", true, "可写课程、比赛、科研项目、荣誉证书、个人作品、实习、社团或学生工作")}
            </>
          )}

          {step === 5 && (
            <>
              <div className={fieldClass("missingResources")} data-field="missingResources">
                <label>{requiredLabel("missingResources", "你目前最缺的是什么？")}</label>
                {questionFlags("missingResources", true, 3)}
                <ChoiceGroup options={missingResourceOptions} values={form.missingResources} max={3} onChange={(value) => patch("missingResources", value)} />
                {fieldError("missingResources")}
              </div>
              <div className={fieldClass("majorOutcomeAwareness")} data-field="majorOutcomeAwareness">
                <label>{requiredLabel("majorOutcomeAwareness", "你是否了解本专业近几届毕业生的主要去向？")}</label>
                {questionFlags("majorOutcomeAwareness")}
                <RadioGroup options={majorOutcomeAwarenessOptions} value={form.majorOutcomeAwareness} onChange={(value) => patch("majorOutcomeAwareness", value)} />
                {fieldError("majorOutcomeAwareness")}
              </div>
              <div className={fieldClass("targetJobAwareness")} data-field="targetJobAwareness">
                <label>{requiredLabel("targetJobAwareness", "你是否了解自己心仪岗位的要求？")}</label>
                {questionFlags("targetJobAwareness")}
                <RadioGroup options={targetJobAwarenessOptions} value={form.targetJobAwareness} onChange={(value) => patch("targetJobAwareness", value)} />
                {fieldError("targetJobAwareness")}
              </div>
              <div className={fieldClass("jobInfoChannels")} data-field="jobInfoChannels">
                <label>{requiredLabel("jobInfoChannels", "你通常通过哪些渠道了解职业或招聘信息？")}</label>
                {questionFlags("jobInfoChannels", true)}
                <ChoiceGroup options={jobInfoChannelOptions} values={form.jobInfoChannels} onChange={(value) => patch("jobInfoChannels", value)} />
                {fieldError("jobInfoChannels")}
              </div>
              {form.jobInfoChannels.includes("其他") && textField("jobInfoChannelOther", "请填写其他职业信息渠道", true)}
              <div className={fieldClass("healthEnergyStatus")} data-field="healthEnergyStatus">
                <label>{requiredLabel("healthEnergyStatus", "你的身体健康和精力状态如何？")}</label>
                {questionFlags("healthEnergyStatus")}
                <RadioGroup options={healthEnergyOptions} value={form.healthEnergyStatus} onChange={(value) => patch("healthEnergyStatus", value)} />
                {fieldError("healthEnergyStatus")}
              </div>
              {textField("exerciseFrequency", "你每周运动几次、每次多长时间？偏好什么运动？", false, "例如：每周2次，每次40分钟，喜欢跑步和羽毛球")}

              <h2 className="form-subtitle">执行力与承压</h2>
              <div className="field">
                <label>为实现目标，在没有监督、且一年内看不到成果的情况下，你能否坚持？<span className="required-mark">*</span></label>
                <input className="input" min={1} max={5} type="range" value={form.longTermPersistence} onChange={(event) => patch("longTermPersistence", Number(event.target.value))} />
                <div className="hint">当前：{form.longTermPersistence}/5</div>
              </div>
              {radioField("executionStyle", "你的执行力更接近哪种情况？", executionStyleOptions)}
              {radioField("failureRecoveryTime", "遇到失败后通常多久恢复？", failureRecoveryOptions)}
              {radioField("selfDoubtFrequency", "你是否容易产生自我怀疑？", selfDoubtOptions)}
              {radioField("problemSolvingStyle", "遇到问题时，你通常会如何处理？", problemSolvingOptions)}
              {radioField("supportNeed", "恢复状态时，你通常需要怎样的支持？", supportNeedOptions)}
              {radioField("highIntensityExperience", "过去是否有过连续一个月以上高强度投入的经历？", highIntensityOptions)}
              {radioField("routineWorkTolerance", "你能否接受纯事务性、琐碎、繁杂的工作？", routineWorkToleranceOptions)}
              {radioField("careerRiskPreference", "如果必须选择一种职业环境，你更偏好哪一种？", careerRiskPreferenceOptions)}
            </>
          )}

          {step === 6 && (
            <>
              <div className={fieldClass("careerConfusions")} data-field="careerConfusions">
                <label>{requiredLabel("careerConfusions", "你现在最想解决的生涯问题是什么？")}</label>
                {questionFlags("careerConfusions", true, 3)}
                <ChoiceGroup options={careerConfusionOptions} values={form.careerConfusions} max={3} onChange={(value) => patch("careerConfusions", value)} />
                {fieldError("careerConfusions")}
              </div>
              {form.careerConfusions.includes("其他") && textField("careerConfusionOther", "请填写其他生涯困惑", true)}
              {textField("mainConfusionText", "如果只能用一句话描述你现在的困惑，你会怎么说？", true)}
            </>
          )}

          {generationJob && generationJob.status !== "failed" && generationJob.status !== "cancelled" && (
            <div className="generation-progress" aria-live="polite">
              <div className="generation-status-label">{jobStatusLabel(generationJob)}</div>
              <div className="generation-progress-head">
                <strong>生成进度</strong>
                <span>{generationJob.progress}%</span>
              </div>
              <div className="generation-progress-track">
                <span style={{ width: `${generationJob.progress}%` }} />
              </div>
              <div className="generation-progress-steps">
                {generationSteps.map((item) => (
                  <div className={generationJob.progress >= item.progress ? "complete" : ""} key={item.label}>
                    <span />
                    {item.label}
                  </div>
                ))}
              </div>
            </div>
          )}

          {generationJob?.status === "cancelled" && !submitting && (
            <div className="generation-failed" aria-live="polite">
              <strong>生成已取消</strong>
              <p>{generationJob.message || "报告生成已取消。"}</p>
              <div className="actions failure-actions">
                <button className="button secondary" onClick={backToEdit}>返回修改问卷</button>
              </div>
            </div>
          )}

          {generationJob?.status === "failed" && !submitting && (
            <div className="generation-failed" aria-live="polite">
              <strong>生成失败</strong>
              <p>失败阶段：{generationJob.stage}</p>
              <p>{generationJob.error || generationJob.message}</p>
              <div className="actions failure-actions">
                <button className="button" onClick={submit}>重新生成</button>
                <button className="button secondary" onClick={backToEdit}>返回修改问卷</button>
              </div>
            </div>
          )}

          {error && <div className="error">{error}</div>}

          <div className="actions">
            {step > 0 && <button className="button secondary" disabled={submitting} onClick={() => goToStep(step - 1)}>上一步</button>}
            {step < steps.length - 1 && <button className="button" disabled={submitting} onClick={() => goToStep(step + 1)}>下一步</button>}
            {step === steps.length - 1 && <button className="button" disabled={submitting} onClick={submit}>{submitting ? "生成中..." : "提交并生成报告"}</button>}
          </div>
        </section>
      </div>
    </main>
  );
}
