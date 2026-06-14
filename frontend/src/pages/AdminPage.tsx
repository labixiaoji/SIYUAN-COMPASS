import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchAdminMetrics, fetchAdminRecords } from "../api/admin";
import type { AdminMetrics, AdminRecord } from "../types/report";

export function AdminPage() {
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [records, setRecords] = useState<AdminRecord[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([fetchAdminMetrics(), fetchAdminRecords()])
      .then(([nextMetrics, nextRecords]) => {
        setMetrics(nextMetrics);
        setRecords(nextRecords.records);
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "后台数据加载失败。"));
  }, []);

  if (error) {
    return <main className="shell page"><div className="error">{error}</div></main>;
  }

  if (!metrics) {
    return <main className="shell page"><div className="panel">后台数据加载中...</div></main>;
  }

  return (
    <main className="shell page">
      <div className="page-title">
        <h1>管理员后台</h1>
        <p>查看学生生成记录，并对报告内容进行人工修订。</p>
      </div>
      <section className="metrics">
        <div className="panel stat"><strong>{metrics.assessmentCount}</strong><span>填写记录</span></div>
        <div className="panel stat"><strong>{metrics.reportSuccessCount}</strong><span>成功报告</span></div>
        <div className="panel stat"><strong>{metrics.feedbackCount}</strong><span>反馈数量</span></div>
        <div className="panel stat"><strong>{metrics.averageRecommendScore}</strong><span>推荐评分</span></div>
      </section>

      <section className="panel admin-records">
        <div className="admin-section-head">
          <div>
            <h2>学生生成记录</h2>
            <p className="hint">历史匿名数据仍会保留，但没有可登录的学生账号。</p>
          </div>
          <span>{records.length} 条</span>
        </div>
        {records.length === 0 ? (
          <p className="hint">暂无报告记录。</p>
        ) : (
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>学生</th>
                  <th>年级 / 专业</th>
                  <th>生成时间</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr key={record.report.id}>
                    <td>
                      <strong>{record.student.displayName}</strong>
                      <span>{record.student.username}</span>
                    </td>
                    <td>{record.assessment.grade || "-"} / {record.assessment.collegeMajor || "-"}</td>
                    <td>{new Date(record.assessment.submittedAt).toLocaleString("zh-CN")}</td>
                    <td>{record.report.qualityStatus}{record.report.editedAt ? " · 已人工修改" : ""}</td>
                    <td className="admin-actions-cell">
                      <Link to={`/reports/${record.report.id}`}>查看</Link>
                      <Link to={`/admin/reports/${record.report.id}/edit`}>编辑</Link>
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
