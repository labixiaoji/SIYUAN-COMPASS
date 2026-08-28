import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { fetchAdminRecords } from "../api/admin";
import type { AdminRecord } from "../types/report";

function qualityText(status: string) {
  if (status === "passed") return "已通过";
  if (status === "warning") return "有提醒";
  if (status === "failed") return "需检查";
  return "未检查";
}

function qualityClass(status: string) {
  if (status === "passed") return "success";
  if (status === "warning") return "warning";
  if (status === "failed") return "failed";
  return "queued";
}

function formatTime(value?: string | null) {
  if (!value) return "时间未知";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "时间未知" : date.toLocaleString("zh-CN");
}

export function AdminReportsPage() {
  const [searchParams] = useSearchParams();
  const [records, setRecords] = useState<AdminRecord[]>([]);
  const [keyword, setKeyword] = useState("");
  const [qualityStatus, setQualityStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchAdminRecords()
      .then((data) => setRecords(data.records))
      .catch((caught) => setError(caught instanceof Error ? caught.message : "报告加载失败。"))
      .finally(() => setLoading(false));
  }, []);

  const filteredRecords = useMemo(() => {
    const normalizedKeyword = keyword.trim().toLowerCase();
    return records.filter((record) => {
      const searchable = [
        record.report.title,
        record.student.displayName,
        record.student.username,
        record.assessment.collegeMajor
      ].filter(Boolean).join(" ").toLowerCase();
      return (
        (!normalizedKeyword || searchable.includes(normalizedKeyword))
        && (qualityStatus === "all" || record.report.qualityStatus === qualityStatus)
      );
    });
  }, [keyword, qualityStatus, records]);

  return (
    <main className="shell page admin-list-page">
      <div className="page-title">
        <h1>成功报告</h1>
        <p>查看已经生成的报告、质量检查结果、学生反馈和原始问卷入口。</p>
      </div>

      <section className="panel admin-list-panel">
        <div className="admin-record-filters">
          <label className="admin-filter-keyword">
            <span>搜索</span>
            <input value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="报告标题、学生、账号或专业" />
          </label>
          <label>
            <span>质量状态</span>
            <select value={qualityStatus} onChange={(event) => setQualityStatus(event.target.value)}>
              <option value="all">全部</option>
              <option value="passed">已通过</option>
              <option value="warning">有提醒</option>
              <option value="failed">需检查</option>
              <option value="unchecked">未检查</option>
            </select>
          </label>
        </div>

        {searchParams.get("status") === "success" && <p className="hint admin-filter-hint">当前显示成功生成的报告；“需检查”表示报告质量状态，不代表任务生成失败。</p>}
        {error && <div className="error">{error}</div>}
        {loading ? (
          <p className="hint">报告加载中...</p>
        ) : filteredRecords.length === 0 ? (
          <div className="empty-state"><p>暂无符合条件的报告。</p></div>
        ) : (
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>报告</th>
                  <th>学生</th>
                  <th>生成时间</th>
                  <th>质量状态</th>
                  <th>反馈</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {filteredRecords.map((record) => (
                  <tr key={record.report.id}>
                    <td>
                      <strong>{record.report.title}</strong>
                      <span>{record.report.wordCount} 字 · {record.report.promptVersion || "版本未知"}</span>
                    </td>
                    <td>
                      <strong>{record.student.displayName}</strong>
                      <span>{record.student.username}</span>
                      <span>{record.assessment.collegeMajor || "专业未填写"}</span>
                    </td>
                    <td>{formatTime(record.report.createdAt)}</td>
                    <td>
                      <span className={`job-status-pill ${qualityClass(record.report.qualityStatus)}`}>{qualityText(record.report.qualityStatus)}</span>
                      {record.report.errorMessage && <span className="admin-report-warning">{record.report.errorMessage}</span>}
                    </td>
                    <td>{record.feedbacks?.length || 0} 条</td>
                    <td>
                      <div className="admin-actions-cell">
                        <Link className="button secondary" to={`/reports/${record.report.id}`}>查看</Link>
                        <Link className="button" to={`/admin/reports/${record.report.id}/edit`}>编辑</Link>
                        <Link className="button secondary" to={`/admin/assessments/${record.report.responseId}`}>问卷</Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
