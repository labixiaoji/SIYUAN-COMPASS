import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchAdminGenerationJob } from "../api/admin";
import type { AdminGenerationJob } from "../types/report";

function statusText(status: string) {
  const labels: Record<string, string> = {
    queued: "等待生成",
    running: "生成中",
    success: "成功",
    failed: "失败",
    cancelled: "已取消"
  };
  return labels[status] || status;
}

function statusClass(status: string) {
  if (status === "success") return "success";
  if (status === "failed") return "failed";
  if (status === "cancelled") return "warning";
  return "queued";
}

function stageText(stage: string) {
  const labels: Record<string, string> = {
    queued: "排队",
    preparing: "整理问卷",
    profile_generating: "生成画像",
    profile_validating: "校验画像",
    profile_retrying: "修正画像",
    profile_complete: "画像完成",
    report_generating: "生成报告",
    report_validating: "校验报告",
    report_retrying: "修正报告",
    saving: "保存结果",
    completed: "完成",
    profile_failed: "画像失败",
    report_failed: "报告失败",
    cancelled: "已取消",
    failed: "流程失败"
  };
  return labels[stage] || stage;
}

function formatTime(value?: string | null) {
  if (!value) return "时间未知";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "时间未知" : date.toLocaleString("zh-CN");
}

export function AdminGenerationJobDetailPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState<AdminGenerationJob | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!jobId) return;
    fetchAdminGenerationJob(jobId)
      .then(setJob)
      .catch((caught) => setError(caught instanceof Error ? caught.message : "生成任务加载失败。"));
  }, [jobId]);

  if (error) return <main className="shell page"><div className="error">{error}</div></main>;
  if (!job) return <main className="shell page"><div className="panel">生成任务加载中...</div></main>;

  const failure = job.failure || (job.status === "failed" ? {
    code: "LEGACY_ERROR",
    stage: job.stage,
    message: job.error || job.message || "未记录具体错误信息",
    retryable: false,
    traceId: job.jobId
  } : null);
  return (
    <main className="shell page admin-detail-page">
      <div className="page-title">
        <h1>生成任务详情</h1>
        <p>任务编号：{job.jobId}</p>
      </div>

      <section className="panel admin-detail-summary">
        <div className="admin-detail-title-row">
          <div>
            <h2>{job.student.displayName}</h2>
            <p className="hint">{job.student.username} · {formatTime(job.createdAt)}</p>
          </div>
          <span className={`job-status-pill ${statusClass(job.status)}`}>{statusText(job.status)}</span>
        </div>
        <div className="admin-detail-grid">
          <div><span>当前阶段</span><strong>{stageText(job.stage)}</strong></div>
          <div><span>处理进度</span><strong>{job.progress}%</strong></div>
          <div><span>尝试次数</span><strong>{job.attempts ?? 0}</strong></div>
          <div><span>最近更新</span><strong>{formatTime(job.updatedAt)}</strong></div>
        </div>
        <p className="admin-detail-message">{job.message}</p>
      </section>

      {failure && (
        <section className="panel admin-failure-detail" aria-labelledby="failure-title">
          <div className="admin-section-head">
            <div>
              <h2 id="failure-title">失败信息</h2>
              <p className="hint">以下内容已脱敏，仅用于管理员定位生成问题。</p>
            </div>
            <span className={`job-status-pill ${failure.retryable ? "warning" : "failed"}`}>
              {failure.retryable ? "建议稍后重试" : "需检查配置或数据"}
            </span>
          </div>
          <div className="admin-detail-grid failure-grid">
            <div><span>错误代码</span><strong>{failure.code}</strong></div>
            <div><span>失败阶段</span><strong>{failure.stage}</strong></div>
            <div><span>服务供应商</span><strong>{failure.provider || "未记录"}</strong></div>
            <div><span>供应商状态码</span><strong>{failure.providerStatus || "未记录"}</strong></div>
            <div><span>失败时间</span><strong>{formatTime(failure.occurredAt)}</strong></div>
            <div><span>追踪编号</span><strong>{failure.traceId || job.jobId}</strong></div>
          </div>
          <div className="admin-error-message">
            <span>错误说明</span>
            <p>{failure.message}</p>
          </div>
        </section>
      )}

      <section className="panel admin-detail-actions-panel">
        <h2>关联数据</h2>
        <div className="actions">
          {job.responseId && <Link className="button secondary" to={`/admin/assessments/${job.responseId}`}>查看已保存问卷</Link>}
          {job.draftAvailable && <Link className="button secondary" to={`/admin/generation-jobs/${job.jobId}/draft`}>查看失败任务问卷</Link>}
          {job.reportId && <Link className="button" to={`/reports/${job.reportId}`}>查看报告</Link>}
          <Link className="button secondary" to="/admin/generation-jobs">返回生成任务</Link>
        </div>
      </section>
    </main>
  );
}
