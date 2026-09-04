import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { fetchAdminAssessments } from "../api/admin";
import type { AdminAssessmentRecord } from "../types/report";

const pageSize = 20;
const validStatuses = ["all", "queued", "running", "success", "failed", "cancelled"];

function statusText(status?: string | null) {
  const labels: Record<string, string> = {
    queued: "等待生成",
    running: "生成中",
    success: "已生成",
    failed: "生成失败",
    cancelled: "已取消",
    unknown: "未记录"
  };
  return labels[status || "unknown"] || status || "未记录";
}

function statusClass(status?: string | null) {
  if (status === "success") return "success";
  if (status === "failed") return "failed";
  if (status === "cancelled") return "warning";
  return "queued";
}

function stageText(stage?: string | null) {
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
    validation_failed: "问卷校验失败",
    cancelled: "已取消",
    failed: "流程失败"
  };
  return labels[stage || ""] || stage || "未记录";
}

function formatTime(value?: string | null) {
  if (!value) return "时间未知";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "时间未知" : date.toLocaleString("zh-CN");
}

function failureText(item: AdminAssessmentRecord) {
  return item.failure?.message || item.error || "未记录具体错误信息";
}

function initialStatusFromUrl(searchParams: URLSearchParams) {
  const value = searchParams.get("status") || "all";
  return validStatuses.includes(value) ? value : "all";
}

export function AdminAssessmentsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState<AdminAssessmentRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [keyword, setKeyword] = useState("");
  const [status, setStatus] = useState(() => initialStatusFromUrl(searchParams));
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let closed = false;
    setLoading(true);
    fetchAdminAssessments({
      keyword: keyword.trim() || undefined,
      status,
      limit: pageSize,
      offset: (page - 1) * pageSize
    }).then((data) => {
      if (closed) return;
      setItems(data.items);
      setTotal(data.total);
      setError("");
    }).catch((caught) => {
      if (!closed) setError(caught instanceof Error ? caught.message : "填写记录加载失败。");
    }).finally(() => {
      if (!closed) setLoading(false);
    });
    return () => {
      closed = true;
    };
  }, [keyword, page, status]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  function updateKeyword(value: string) {
    setKeyword(value);
    setPage(1);
  }

  function updateStatus(value: string) {
    setStatus(value);
    setPage(1);
    setSearchParams(value === "all" ? {} : { status: value });
  }

  return (
    <main className="shell page admin-list-page">
      <div className="page-title">
        <h1>填写记录</h1>
        <p>所有问卷提交、报告生成进度、失败原因和可恢复草稿都在这里查看。</p>
      </div>

      <section className="panel admin-list-panel">
        <div className="admin-record-filters">
          <label className="admin-filter-keyword">
            <span>搜索</span>
            <input value={keyword} onChange={(event) => updateKeyword(event.target.value)} placeholder="姓名、账号、专业或记录编号" />
          </label>
          <label>
            <span>记录状态</span>
            <select value={status} onChange={(event) => updateStatus(event.target.value)}>
              <option value="all">全部</option>
              <option value="queued">等待生成</option>
              <option value="running">生成中</option>
              <option value="success">已生成</option>
              <option value="failed">生成失败</option>
              <option value="cancelled">已取消</option>
            </select>
          </label>
        </div>

        {error && <div className="error">{error}</div>}
        {loading ? (
          <p className="hint">填写记录加载中...</p>
        ) : items.length === 0 ? (
          <div className="empty-state"><p>暂无符合条件的填写记录。</p></div>
        ) : (
          <div className="admin-table-wrap">
            <table className="admin-table admin-assessment-table">
              <thead>
                <tr>
                  <th>学生 / 提交时间</th>
                  <th>教育信息</th>
                  <th>生成状态</th>
                  <th>当前阶段</th>
                  <th>失败信息</th>
                  <th>草稿</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => {
                  const progress = Math.max(0, Math.min(item.progress ?? 0, 100));
                  return (
                    <tr key={item.recordId}>
                      <td>
                        <strong>{item.student.displayName}</strong>
                        <span>{item.student.username}</span>
                        <span>{formatTime(item.submittedAt)}</span>
                      </td>
                      <td>
                        <strong>{item.educationStage || "未填写"} · {item.grade || "未填写"}</strong>
                        <span>{item.collegeMajor || "专业未填写"}</span>
                      </td>
                      <td>
                        <span className={`job-status-pill ${statusClass(item.taskStatus)}`}>{statusText(item.taskStatus)}</span>
                        <div className="admin-progress-track" aria-label={`生成进度 ${progress}%`}>
                          <span style={{ width: `${progress}%` }} />
                        </div>
                        <span>{progress}% · {item.message || "暂无进度说明"}</span>
                      </td>
                      <td>
                        <strong>{stageText(item.stage)}</strong>
                        {item.attempts !== undefined && <span>{item.attempts} 次尝试</span>}
                      </td>
                      <td className="admin-error-cell">
                        {item.failure ? (
                          <>
                            <strong>{item.failure.code}</strong>
                            <span>{failureText(item)}</span>
                          </>
                        ) : item.taskStatus === "failed" ? (
                          <span>未记录具体错误信息</span>
                        ) : <span>—</span>}
                      </td>
                      <td>{item.draftAvailable ? <span className="admin-draft-available">可恢复</span> : <span>—</span>}</td>
                      <td>
                        <div className="admin-actions-cell">
                          {item.responseId && (
                            <Link className="button secondary" to={`/admin/assessments/${item.responseId}`}>查看问卷</Link>
                          )}
                          {item.jobId && (
                            <Link className="button secondary" to={`/admin/generation-jobs/${item.jobId}`}>生成详情</Link>
                          )}
                          {item.jobId && item.draftAvailable && (
                            <Link className="button" to={`/admin/generation-jobs/${item.jobId}/draft`}>查看草稿</Link>
                          )}
                          {item.reportId && item.taskStatus === "success" && (
                            <Link className="button" to={`/reports/${item.reportId}`}>查看报告</Link>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <nav className="admin-pagination" aria-label="填写记录分页">
            <button className="button secondary" disabled={page === 1} onClick={() => setPage(page - 1)}>上一页</button>
            <span>第 {page} / {totalPages} 页 · 共 {total} 条</span>
            <button className="button secondary" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>下一页</button>
          </nav>
        )}
      </section>
    </main>
  );
}
