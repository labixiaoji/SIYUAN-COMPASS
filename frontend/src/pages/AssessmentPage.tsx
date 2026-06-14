import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createAssessmentJob, fetchAssessmentJob } from "../api/assessments";
import type { GenerationJobStatus } from "../api/assessments";
import { ChoiceGroup, RadioGroup, ScoreRows } from "../components/FormControls";
import {
  careerConfusionOptions,
  educationReasonOptions,
  fiveYearFamilyOptions,
  genderOptions,
  gradeOptions,
  healthEnergyOptions,
  jobInfoChannelOptions,
  majorOutcomeAwarenessOptions,
  missingResourceOptions,
  preparationOptions,
  studyIntentionOptions,
  targetJobAwarenessOptions,
  tenYearFamilyOptions,
  valueOptions
} from "../features/assessment/options";
import type { AssessmentResponseInput } from "../types/assessment";

const steps = ["基本信息", "教育路径", "未来愿景", "价值能力兴趣", "行动基础", "核心困惑"];
const generationSteps = [
  { progress: 10, label: "整理问卷" },
  { progress: 20, label: "生成用户画像" },
  { progress: 45, label: "校验画像" },
  { progress: 65, label: "生成生涯报告" },
  { progress: 88, label: "校验报告" },
  { progress: 100, label: "完成" }
];

const initialForm: AssessmentResponseInput = {
  grade: "大三",
  gender: "不便透露",
  collegeMajor: "",
  hometown: "",
  mastersIntention: "还不了解",
  mastersPlan: "",
  phdIntention: "还不了解",
  phdPlan: "",
  educationPathReasons: [],
  educationCertainty: 3,
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
  currentPreparations: [],
  missingResources: [],
  majorOutcomeAwareness: "听说过一些",
  targetJobAwareness: "只知道大概方向",
  jobInfoChannels: [],
  healthEnergyStatus: "一般，偶尔运动",
  exerciseFrequency: "",
  careerConfusions: [],
  mainConfusionText: ""
};

export function AssessmentPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<AssessmentResponseInput>(initialForm);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [generationJob, setGenerationJob] = useState<GenerationJobStatus | null>(null);

  const patch = <K extends keyof AssessmentResponseInput>(key: K, value: AssessmentResponseInput[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  async function submit() {
    setSubmitting(true);
    setError("");

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
          navigate(`/reports/${job.reportId}`);
          return;
        }

        if (job.status === "failed") {
          throw new Error(job.error ? `${job.message} ${job.error}` : job.message);
        }

        await new Promise((resolve) => window.setTimeout(resolve, 1000));
      }

      throw new Error("生成等待时间超过10分钟，请检查后端日志或稍后重试。");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "提交失败，请稍后重试。");
    } finally {
      setSubmitting(false);
    }
  }

  const textField = (
    key: keyof AssessmentResponseInput,
    label: string,
    multiline = false,
    placeholder = ""
  ) => (
    <div className="field">
      <label>{label}</label>
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
    </div>
  );

  return (
    <main className="shell page">
      <div className="page-title">
        <h1>生涯规划问卷</h1>
        <p>请尽量填写具体。你的回答仅用于生成个人生涯规划报告和产品优化分析。</p>
      </div>

      <div className="form-layout">
        <aside className="panel steps">
          {steps.map((name, index) => (
            <div className={`step ${index === step ? "active" : ""}`} key={name}>
              {index + 1}. {name}
            </div>
          ))}
        </aside>

        <section className="panel">
          {step === 0 && (
            <>
              <div className="field">
                <label>你的年级是？</label>
                <RadioGroup options={gradeOptions} value={form.grade} onChange={(value) => patch("grade", value)} />
              </div>
              <div className="field">
                <label>你的性别是？</label>
                <RadioGroup options={genderOptions} value={form.gender} onChange={(value) => patch("gender", value)} />
              </div>
              {textField("collegeMajor", "你的学院和专业是？", false, "例如：计算机学院 / 计算机科学与技术")}
              {textField("hometown", "你的家乡或主要成长地是？", false, "例如：上海")}
            </>
          )}

          {step === 1 && (
            <>
              <div className="field">
                <label>你是否考虑读硕士研究生？</label>
                <RadioGroup options={studyIntentionOptions} value={form.mastersIntention} onChange={(value) => patch("mastersIntention", value)} />
              </div>
              {textField("mastersPlan", "如果考虑读硕士，你目前有什么初步规划？", true, "可填写目标学校、城市、专业方向、保研/考研/留学倾向和准备情况")}
              <div className="field">
                <label>你是否考虑读博士研究生？</label>
                <RadioGroup options={studyIntentionOptions} value={form.phdIntention} onChange={(value) => patch("phdIntention", value)} />
              </div>
              {textField("phdPlan", "如果考虑读博，你目前有什么初步规划？", true, "可填写研究方向、目标院校、导师、国内外倾向和准备情况")}
              <div className="field">
                <label>你考虑上述教育路径的主要原因是什么？</label>
                <ChoiceGroup options={educationReasonOptions} values={form.educationPathReasons} onChange={(value) => patch("educationPathReasons", value)} />
              </div>
              <div className="field">
                <label>你对当前教育路径规划的确定程度是多少？</label>
                <input className="input" min={1} max={5} type="range" value={form.educationCertainty} onChange={(event) => patch("educationCertainty", Number(event.target.value))} />
                <div className="hint">当前：{form.educationCertainty}/5</div>
              </div>
            </>
          )}

          {step === 2 && (
            <>
              <h2 className="form-subtitle">5年后的愿景</h2>
              {textField("fiveYearCity", "你希望生活或工作的城市是？")}
              {textField("fiveYearIncome", "你希望达到怎样的收入状态？", false, "可填写月收入、年收入或生活水平")}
              {textField("fiveYearIndustry", "你希望进入或深耕什么行业、领域？")}
              {textField("fiveYearRole", "你希望从事什么岗位、承担什么角色？")}
              <div className="field">
                <label>你期待的家庭或亲密关系状态是？</label>
                <RadioGroup options={fiveYearFamilyOptions} value={form.fiveYearFamilyStatus} onChange={(value) => patch("fiveYearFamilyStatus", value)} />
              </div>
              {textField("fiveYearHousingPlan", "你期待怎样的居住或住房状态？")}
              {textField("fiveYearHobbiesSkills", "你希望保留哪些爱好，或形成哪些核心技能？", true)}

              <h2 className="form-subtitle">10年后的愿景</h2>
              {textField("tenYearCity", "你希望生活或工作的城市是？")}
              {textField("tenYearIncome", "你希望达到怎样的收入状态？", false, "可填写月收入、年收入或生活水平")}
              {textField("tenYearIndustry", "你希望进入或深耕什么行业、领域？")}
              {textField("tenYearRole", "你希望从事什么岗位、承担什么角色？")}
              <div className="field">
                <label>你期待的家庭或亲密关系状态是？</label>
                <RadioGroup options={tenYearFamilyOptions} value={form.tenYearFamilyStatus} onChange={(value) => patch("tenYearFamilyStatus", value)} />
              </div>
              {textField("tenYearHousingPlan", "你期待怎样的居住或住房状态？")}
              {textField("tenYearHobbiesSkills", "你希望保留哪些爱好，或形成哪些核心技能？", true)}
            </>
          )}

          {step === 3 && (
            <>
              <div className="field">
                <label>请选出你最看重的3项价值观。</label>
                <div className="hint">请选择3项。</div>
                <ChoiceGroup options={valueOptions} values={form.topValuesRanked} max={3} onChange={(value) => patch("topValuesRanked", value)} />
              </div>
              <div className="field">
                <label>能力自评：1 = 很不符合，5 = 非常符合。</label>
                <ScoreRows rows={[["logic", "数学、逻辑推理"], ["expression", "写作、表达、讲故事"], ["spatialDesign", "空间、方向、设计"], ["interpersonal", "识人、沟通、理解情绪"]]} values={form.abilityScores} onChange={(key, value) => patch("abilityScores", { ...form.abilityScores, [key]: value })} />
              </div>
              <div className="field">
                <label>兴趣倾向：1 = 很不喜欢，5 = 非常喜欢。</label>
                <ScoreRows rows={[["handsOn", "动手操作、修理工具"], ["research", "研究问题、分析数据"], ["creation", "创作、写作、设计或表达"], ["helping", "帮助他人、教学或咨询"], ["leadership", "销售、领导或影响他人"], ["detail", "按规则整理信息、处理细节"]]} values={form.interestScores} onChange={(key, value) => patch("interestScores", { ...form.interestScores, [key]: value })} />
              </div>
            </>
          )}

          {step === 4 && (
            <>
              <div className="field">
                <label>为了未来目标，你已经做过哪些准备？</label>
                <ChoiceGroup options={preparationOptions} values={form.currentPreparations} onChange={(value) => patch("currentPreparations", value)} />
              </div>
              <div className="field">
                <label>你目前最缺的是什么？</label>
                <div className="hint">最多选择3项。</div>
                <ChoiceGroup options={missingResourceOptions} values={form.missingResources} max={3} onChange={(value) => patch("missingResources", value)} />
              </div>
              <div className="field">
                <label>你是否了解本专业近几届毕业生的主要去向？</label>
                <RadioGroup options={majorOutcomeAwarenessOptions} value={form.majorOutcomeAwareness} onChange={(value) => patch("majorOutcomeAwareness", value)} />
              </div>
              <div className="field">
                <label>你是否了解自己心仪岗位的要求？</label>
                <RadioGroup options={targetJobAwarenessOptions} value={form.targetJobAwareness} onChange={(value) => patch("targetJobAwareness", value)} />
              </div>
              <div className="field">
                <label>你通常通过哪些渠道了解职业或招聘信息？</label>
                <ChoiceGroup options={jobInfoChannelOptions} values={form.jobInfoChannels} onChange={(value) => patch("jobInfoChannels", value)} />
              </div>
              <div className="field">
                <label>你的身体健康和精力状态如何？</label>
                <RadioGroup options={healthEnergyOptions} value={form.healthEnergyStatus} onChange={(value) => patch("healthEnergyStatus", value)} />
              </div>
              {textField("exerciseFrequency", "你每周运动几次、每次多长时间？偏好什么运动？", false, "例如：每周2次，每次40分钟，喜欢跑步和羽毛球")}
            </>
          )}

          {step === 5 && (
            <>
              <div className="field">
                <label>你现在最想解决的生涯问题是什么？</label>
                <div className="hint">最多选择3项。</div>
                <ChoiceGroup options={careerConfusionOptions} values={form.careerConfusions} max={3} onChange={(value) => patch("careerConfusions", value)} />
              </div>
              {textField("mainConfusionText", "如果只能用一句话描述你现在的困惑，你会怎么说？", true)}
            </>
          )}

          {submitting && generationJob && (
            <div className="generation-progress" aria-live="polite">
              <div className="generation-progress-head">
                <strong>{generationJob.message}</strong>
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

          {error && <div className="error">{error}</div>}

          <div className="actions">
            {step > 0 && <button className="button secondary" disabled={submitting} onClick={() => setStep((value) => value - 1)}>上一步</button>}
            {step < steps.length - 1 && <button className="button" disabled={submitting} onClick={() => setStep((value) => value + 1)}>下一步</button>}
            {step === steps.length - 1 && <button className="button" disabled={submitting} onClick={submit}>{submitting ? "生成中..." : "提交并生成报告"}</button>}
          </div>
        </section>
      </div>
    </main>
  );
}
