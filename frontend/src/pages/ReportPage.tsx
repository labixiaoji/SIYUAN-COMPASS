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

  return (
    <main className="shell page">
      <div className="page-title">
        <h1>{report.title}</h1>
        <p>生成状态：{report.generationStatus} · 字数：{report.wordCount}</p>
      </div>
      <ReportRenderer content={report.content} />
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
