import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { fetchAdminGenerationJobs } from "../api/admin";
import type { AdminGenerationJob } from "../types/report";

const pageSize = 20;

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

function failureText(job: AdminGenerationJob) {
  return job.failure?.message || job.error || "未记录具体错误信息";
}

export function AdminGenerationJobsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialStatus = searchParams.get("status") || "all";
  const [items, setItems] = useState<AdminGenerationJob[]>([]);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState(initialStatus);
  const [keyword, setKeyword] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let closed = false;
    setLoading(true);
    fetchAdminGenerationJobs({
      status,
      keyword: keyword.trim() || undefined,
      limit: pageSize,
      offset: (page - 1) * pageSize
    }).then((data) => {
      if (closed) return;
      setItems(data.items);
      setTotal(data.total);
      setError("");
    }).catch((caught) => {
      if (!closed) setError(caught instanceof Error ? caught.message : "生成任务加载失败。");
    }).finally(() => {
      if (!closed) setLoading(false);
    });
    return () => {
      closed = true;
    };
  }, [keyword, page, status]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  function updateStatus(value: string) {
    setStatus(value);
    setPage(1);
    setSearchParams(value === "all" ? {} : { status: value });
  }

  function updateKeyword(value: string) {
    setKeyword(value);
    setPage(1);
  }

  return (
    <main className="shell page admin-list-page">
      <div className="page-title">
        <h1>生成任务</h1>
        <p>集中查看任务状态、失败阶段、错误信息和可恢复的问卷草稿。</p>
      </div>

      <section className="panel admin-list-panel">
        <div className="admin-record-filters">
          <label className="admin-filter-keyword">
            <span>搜索</span>
            <input value={keyword} onChange={(event) => updateKeyword(event.target.value)} placeholder="学生、任务编号、错误代码" />
          </label>
          <label>
            <span>任务状态</span>
            <select value={status} onChange={(event) => updateStatus(event.target.value)}>
              <option value="all">全部</option>
              <option value="queued">等待生成</option>
              <option value="running">生成中</option>
              <option value="success">成功</option>
              <option value="failed">失败</option>
              <option value="cancelled">已取消</option>
            </select>
          </label>
        </div>

        {error && <div className="error">{error}</div>}
        {loading ? (
          <p className="hint">生成任务加载中...</p>
        ) : items.length === 0 ? (
          <div className="empty-state"><p>暂无符合条件的生成任务。</p></div>
        ) : (
          <div className="admin-table-wrap">
            <table className="admin-table admin-job-table">
              <thead>
                <tr>
                  <th>学生 / 任务</th>
                  <th>状态</th>
                  <th>阶段</th>
                  <th>时间</th>
                  <th>失败信息</th>
                  <th>草稿</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {items.map((job) => (
                  <tr key={job.jobId}>
                    <td>
                      <strong>{job.student.displayName}</strong>
                      <span>{job.student.username}</span>
                      <span className="admin-id-text">{job.jobId.slice(0, 12)}</span>
                    </td>
                    <td>
                      <span className={`job-status-pill ${statusClass(job.status)}`}>{statusText(job.status)}</span>
                      <span>{job.progress}% · {job.attempts ?? 0} 次尝试</span>
                    </td>
                    <td>{stageText(job.stage)}</td>
                    <td>
                      <strong>{formatTime(job.updatedAt)}</strong>
                      <span>创建于 {formatTime(job.createdAt)}</span>
                    </td>
                    <td className="admin-error-cell">
                      {job.failure ? (
                        <>
                          <strong>{job.failure.code}</strong>
                          <span>{failureText(job)}</span>
                        </>
                      ) : job.status === "failed" ? (
                        <span>未记录具体错误信息</span>
                      ) : <span>—</span>}
                    </td>
                    <td>{job.draftAvailable ? <span className="admin-draft-available">可恢复</span> : <span>—</span>}</td>
                    <td>
                      <div className="admin-actions-cell">
                        <Link className="button secondary" to={`/admin/generation-jobs/${job.jobId}`}>详情</Link>
                        {job.draftAvailable && <Link className="button" to={`/admin/generation-jobs/${job.jobId}/draft`}>问卷</Link>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <nav className="admin-pagination" aria-label="生成任务分页">
            <button className="button secondary" disabled={page === 1} onClick={() => setPage(page - 1)}>上一页</button>
            <span>第 {page} / {totalPages} 页 · 共 {total} 条</span>
            <button className="button secondary" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>下一页</button>
          </nav>
        )}
      </section>
    </main>
  );
}
