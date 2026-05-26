import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { submitReportFeedback } from "../api/reports";

const fields = [
  ["understandingScore", "这份报告是否准确理解了你？"],
  ["insightScore", "这份报告是否帮你看清了问题？"],
  ["actionScore", "这份报告的行动建议是否可执行？"],
  ["recommendScore", "你愿意推荐同学使用吗？"]
] as const;

type Scores = {
  understandingScore: number;
  insightScore: number;
  actionScore: number;
  recommendScore: number;
};

export function FeedbackPage() {
  const { reportId } = useParams();
  const [scores, setScores] = useState<Scores>({
    understandingScore: 4,
    insightScore: 4,
    actionScore: 4,
    recommendScore: 4
  });
  const [comment, setComment] = useState("");
  const [status, setStatus] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    if (!reportId) return;
    setSubmitting(true);
    setStatus("");

    try {
      await submitReportFeedback(reportId, { ...scores, comment });
      setStatus("反馈已提交，感谢你帮我们把报告变得更好。");
    } catch {
      setStatus("提交失败，请稍后重试。");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="shell page">
      <div className="page-title">
        <h1>报告反馈</h1>
        <p>你的评分会用于改进问卷、分类规则和报告生成质量。</p>
      </div>
      <section className="panel">
        {fields.map(([key, label]) => (
          <div className="field" key={key}>
            <label>{label}</label>
            <div className="score-options" style={{ maxWidth: 320 }}>
              {[1, 2, 3, 4, 5].map((score) => (
                <label key={score}>
                  <input checked={scores[key] === score} onChange={() => setScores((prev) => ({ ...prev, [key]: score }))} type="radio" />
                  {score}
                </label>
              ))}
            </div>
          </div>
        ))}
        <div className="field">
          <label>其他建议</label>
          <textarea className="textarea" value={comment} onChange={(event) => setComment(event.target.value)} />
        </div>
        {status && <div className="error">{status}</div>}
        <div className="actions">
          <Link className="button secondary" to={`/reports/${reportId}`}>返回报告</Link>
          <button className="button" disabled={submitting} onClick={submit}>{submitting ? "提交中..." : "提交反馈"}</button>
        </div>
      </section>
    </main>
  );
}
