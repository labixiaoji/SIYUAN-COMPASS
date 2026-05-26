import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { submitAssessment } from "../api/assessments";
import { ChoiceGroup, RadioGroup, ScoreRows } from "../components/FormControls";
import {
  careerConfusionOptions,
  educationPathOptions,
  educationReasonOptions,
  fiveYearPriorityOptions,
  futureRoleOptions,
  gradeOptions,
  healthEnergyOptions,
  lifePreferenceOptions,
  majorOutcomeAwarenessOptions,
  missingResourceOptions,
  phdIntentionOptions,
  phdReasonOptions,
  preferredCityOptions,
  preparationOptions,
  targetIndustryOptions,
  targetJobAwarenessOptions,
  valueOptions
} from "../features/assessment/options";
import type { AssessmentResponseInput } from "../types/assessment";

const steps = ["基本信息", "当前困惑", "教育路径", "未来愿景", "价值能力兴趣", "行动基础"];

const initialForm: AssessmentResponseInput = {
  grade: "大三",
  collegeMajor: "",
  hometown: "",
  preferredCity: "上海",
  careerConfusions: [],
  mainConfusionText: "",
  educationPath: "暂不确定",
  educationPathReasons: [],
  educationCertainty: 3,
  phdIntention: "还不了解",
  phdReasons: [],
  fiveYearPriorities: [],
  targetIndustries: [],
  futureRoleType: "还不确定",
  lifePreference: "暂时不确定",
  tenYearSelfDescription: "",
  topValuesRanked: [],
  abilityScores: { logic: 3, expression: 3, spatialDesign: 3, interpersonal: 3 },
  interestScores: { handsOn: 3, research: 3, creation: 3, helping: 3, leadership: 3, detail: 3 },
  currentPreparations: [],
  missingResources: [],
  majorOutcomeAwareness: "听说过一些",
  targetJobAwareness: "只知道大概方向",
  healthEnergyStatus: "一般，偶尔运动",
  exerciseFrequency: ""
};

export function AssessmentPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<AssessmentResponseInput>(initialForm);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const patch = <K extends keyof AssessmentResponseInput>(key: K, value: AssessmentResponseInput[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  async function submit() {
    setSubmitting(true);
    setError("");

    try {
      const userId = window.localStorage.getItem("siyuan_user_id") || undefined;
      const data = await submitAssessment({ ...form, userId });
      window.localStorage.setItem("siyuan_user_id", data.userId);
      navigate(`/reports/${data.reportId}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "提交失败，请稍后重试。");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="shell page">
      <div className="page-title">
        <h1>首次填写</h1>
        <p>你的回答仅用于生成个人生涯规划报告和产品优化分析。系统不会公开展示你的个人信息。</p>
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
                <label>你的学院和专业是？</label>
                <input className="input" value={form.collegeMajor} onChange={(event) => patch("collegeMajor", event.target.value)} />
              </div>
              <div className="field">
                <label>你的家乡或主要成长地是？</label>
                <input className="input" value={form.hometown} onChange={(event) => patch("hometown", event.target.value)} />
              </div>
              <div className="field">
                <label>你目前更倾向毕业后在哪里发展？</label>
                <RadioGroup options={preferredCityOptions} value={form.preferredCity} onChange={(value) => patch("preferredCity", value)} />
              </div>
            </>
          )}

          {step === 1 && (
            <>
              <div className="field">
                <label>你现在最想解决的生涯问题是什么？</label>
                <div className="hint">最多选择3项。</div>
                <ChoiceGroup options={careerConfusionOptions} values={form.careerConfusions} max={3} onChange={(value) => patch("careerConfusions", value)} />
              </div>
              <div className="field">
                <label>如果只能用一句话描述你现在的困惑，你会怎么说？</label>
                <textarea className="textarea" value={form.mainConfusionText} onChange={(event) => patch("mainConfusionText", event.target.value)} />
              </div>
            </>
          )}

          {step === 2 && (
            <>
              <div className="field">
                <label>你目前毕业后的初步选择是？</label>
                <RadioGroup options={educationPathOptions} value={form.educationPath} onChange={(value) => patch("educationPath", value)} />
              </div>
              <div className="field">
                <label>你选择或倾向这条路径的主要原因是什么？</label>
                <ChoiceGroup options={educationReasonOptions} values={form.educationPathReasons} onChange={(value) => patch("educationPathReasons", value)} />
              </div>
              <div className="field">
                <label>你对这个选择的确定程度是多少？</label>
                <input className="input" min={1} max={5} type="range" value={form.educationCertainty} onChange={(event) => patch("educationCertainty", Number(event.target.value))} />
                <div className="hint">当前：{form.educationCertainty}/5</div>
              </div>
              <div className="field">
                <label>你是否考虑过读博？</label>
                <RadioGroup options={phdIntentionOptions} value={form.phdIntention} onChange={(value) => patch("phdIntention", value)} />
              </div>
              {(form.phdIntention === "明确考虑" || form.phdIntention === "有一点兴趣") && (
                <div className="field">
                  <label>你考虑读博的主要原因是什么？</label>
                  <ChoiceGroup options={phdReasonOptions} values={form.phdReasons} onChange={(value) => patch("phdReasons", value)} />
                </div>
              )}
            </>
          )}

          {step === 3 && (
            <>
              <div className="field">
                <label>未来5年，你最希望优先获得什么？</label>
                <div className="hint">最多选择3项。</div>
                <ChoiceGroup options={fiveYearPriorityOptions} values={form.fiveYearPriorities} max={3} onChange={(value) => patch("fiveYearPriorities", value)} />
              </div>
              <div className="field">
                <label>未来5年，你希望主要深耕的行业或方向是？</label>
                <div className="hint">最多选择2项。</div>
                <ChoiceGroup options={targetIndustryOptions} values={form.targetIndustries} max={2} onChange={(value) => patch("targetIndustries", value)} />
              </div>
              <div className="field">
                <label>未来5-10年，你更希望成为哪类人？</label>
                <RadioGroup options={futureRoleOptions} value={form.futureRoleType} onChange={(value) => patch("futureRoleType", value)} />
              </div>
              <div className="field">
                <label>未来5-10年，你理想中的生活状态更接近哪一种？</label>
                <RadioGroup options={lifePreferenceOptions} value={form.lifePreference} onChange={(value) => patch("lifePreference", value)} />
              </div>
              <div className="field">
                <label>请用几句话描述：10年后，你希望自己成为怎样的人？</label>
                <textarea className="textarea" value={form.tenYearSelfDescription} onChange={(event) => patch("tenYearSelfDescription", event.target.value)} />
              </div>
            </>
          )}

          {step === 4 && (
            <>
              <div className="field">
                <label>请选出你最看重的3项价值观。</label>
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

          {step === 5 && (
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
                <label>你的身体健康和精力状态如何？</label>
                <RadioGroup options={healthEnergyOptions} value={form.healthEnergyStatus} onChange={(value) => patch("healthEnergyStatus", value)} />
              </div>
              <div className="field">
                <label>你每周大概运动几次？每次多长时间？</label>
                <input className="input" value={form.exerciseFrequency} onChange={(event) => patch("exerciseFrequency", event.target.value)} />
              </div>
            </>
          )}

          {error && <div className="error">{error}</div>}

          <div className="actions">
            {step > 0 && <button className="button secondary" onClick={() => setStep((value) => value - 1)}>上一步</button>}
            {step < steps.length - 1 && <button className="button" onClick={() => setStep((value) => value + 1)}>下一步</button>}
            {step === steps.length - 1 && <button className="button" disabled={submitting} onClick={submit}>{submitting ? "生成中..." : "提交并生成报告"}</button>}
          </div>
        </section>
      </div>
    </main>
  );
}
