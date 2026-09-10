import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchAdminGenerationJobDraft } from "../api/admin";
import type { GenerationJobDraft } from "../api/assessments";
import { AdminAssessmentReader } from "./AdminAssessmentPage";

export function AdminGenerationJobDraftPage() {
  const { jobId } = useParams();
  const [draft, setDraft] = useState<GenerationJobDraft | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!jobId) return;
    fetchAdminGenerationJobDraft(jobId)
      .then(setDraft)
      .catch((caught) => setError(caught instanceof Error ? caught.message : "失败任务问卷加载失败。"));
  }, [jobId]);

  if (error) {
    return <main className="shell page"><div className="error">{error}</div></main>;
  }
  if (!draft) {
    return <main className="shell page"><div className="panel">失败任务问卷加载中...</div></main>;
  }

  return (
    <main className="shell page admin-detail-page">
      <div className="page-title">
        <h1>失败记录问卷草稿</h1>
        <p>任务编号：{draft.jobId} · 来源：{draft.source === "cloud_draft" ? "云端草稿" : "任务快照"}</p>
      </div>
      <div className="success admin-data-notice" role="status">
        这是失败任务保留的脱敏问卷内容，仅用于问题定位和恢复生成。更新时间：{draft.updatedAt ? new Date(draft.updatedAt).toLocaleString("zh-CN") : "未知"}
      </div>
      <AdminAssessmentReader assessment={{ ...draft.answers, submittedAt: draft.updatedAt }} />
      <div className="actions">
        <Link className="button secondary" to={`/admin/generation-jobs/${draft.jobId}`}>返回生成状态</Link>
        <Link className="button secondary" to="/admin/assessments">返回填写记录</Link>
      </div>
    </main>
  );
}
