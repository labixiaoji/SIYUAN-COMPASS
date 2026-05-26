import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchAdminMetrics } from "../api/admin";
import type { AdminMetrics } from "../types/report";

export function AdminPage() {
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchAdminMetrics()
      .then(setMetrics)
      .catch((caught) => setError(caught instanceof Error ? caught.message : "后台指标加载失败。"));
  }, []);

  if (error) {
    return (
      <main className="shell page">
        <div className="error">{error}</div>
      </main>
    );
  }

  if (!metrics) {
    return (
      <main className="shell page">
        <div className="panel">指标加载中...</div>
      </main>
    );
  }

  return (
    <main className="shell page">
      <div className="page-title">
        <h1>后台总览</h1>
        <p>第一阶段轻量后台，用于观察填写、报告生成和反馈评分。</p>
      </div>
      <section className="metrics">
        <div className="panel stat"><strong>{metrics.assessmentCount}</strong><span>填写记录</span></div>
        <div className="panel stat"><strong>{metrics.reportSuccessCount}</strong><span>成功报告</span></div>
        <div className="panel stat"><strong>{metrics.reportFailedCount}</strong><span>失败报告</span></div>
        <div className="panel stat"><strong>{metrics.feedbackCount}</strong><span>反馈数量</span></div>
        <div className="panel stat"><strong>{metrics.averageUnderstandingScore}</strong><span>像我评分</span></div>
        <div className="panel stat"><strong>{metrics.averageInsightScore}</strong><span>洞察评分</span></div>
        <div className="panel stat"><strong>{metrics.averageActionScore}</strong><span>行动评分</span></div>
        <div className="panel stat"><strong>{metrics.averageRecommendScore}</strong><span>推荐评分</span></div>
      </section>
      <section className="panel" style={{ marginTop: 24 }}>
        <h2>最近报告</h2>
        {metrics.recentReports.length === 0 ? (
          <p className="hint">还没有报告。</p>
        ) : (
          metrics.recentReports.map((report) => (
            <p key={report.id}>
              <Link to={`/reports/${report.id}`}>{report.title}</Link> · {report.generationStatus} · {report.qualityStatus} · {new Date(report.createdAt).toLocaleString("zh-CN")}
            </p>
          ))
        )}
      </section>
    </main>
  );
}
