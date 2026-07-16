import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchReport } from "../api/reports";
import { useAuth } from "../auth/AuthContext";
import { ReportRenderer } from "../components/ReportRenderer";
import type { CareerBlueprintReport } from "../types/report";

export function ReportPage() {
  const { user } = useAuth();
  const { reportId } = useParams();
  const [report, setReport] = useState<CareerBlueprintReport | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!reportId) return;
    fetchReport(reportId)
      .then(setReport)
      .catch((caught) => setError(caught instanceof Error ? caught.message : "报告加载失败。"));
  }, [reportId]);

  if (error) {
    return (
      <main className="shell page">
        <div className="error">{error}</div>
      </main>
    );
  }

  if (!report) {
    return (
      <main className="shell page">
        <div className="panel">报告加载中...</div>
      </main>
    );
  }

  const snapshotStudentName = report.inputSnapshot?.response?.studentName;
  const studentName = typeof snapshotStudentName === "string" ? snapshotStudentName.trim() : "";
  const currentAccountName = user?.id === report.userId ? user.displayName.trim() : "";
  const displayName = studentName || report.accountDisplayName?.trim() || currentAccountName || "学生";

  function exportPdf() {
    const previousTitle = document.title;
    document.title = `${displayName}的生涯蓝图`;
    window.print();
    document.title = previousTitle;
  }

  return (
    <main className="shell page">
      <div className="page-title report-page-header">
        <div>
          <h1>{displayName}的生涯蓝图</h1>
          <p>生成状态：{report.generationStatus} · 字数：{report.wordCount}</p>
        </div>
        <button className="button secondary print-hidden" type="button" onClick={exportPdf}>导出 PDF</button>
      </div>
      <ReportRenderer content={report.content} />
      {user?.role !== "admin" && (
        <section className="feedback-cta">
          <div>
            <h2>请为本报告评分</h2>
            <p>你的评分会帮助我们判断报告是否真的理解了你的困惑，并继续改进后续建议。</p>
          </div>
          <Link className="button" to={`/reports/${report.id}/feedback`}>去评分</Link>
        </section>
      )}
      <div className="actions">
        {user?.role === "admin" ? (
          <>
            <Link className="button secondary" to="/admin">返回后台</Link>
            <Link className="button" to={`/admin/reports/${report.id}/edit`}>编辑报告</Link>
          </>
        ) : (
          <>
            <Link className="button secondary" to="/assessment">重新填写</Link>
            <Link className="button" to={`/reports/${report.id}/feedback`}>提交反馈</Link>
          </>
        )}
      </div>
    </main>
  );
}
