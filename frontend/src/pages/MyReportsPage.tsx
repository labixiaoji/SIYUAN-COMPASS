import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchMyReports } from "../api/reports";
import type { CareerBlueprintReport } from "../types/report";

export function MyReportsPage() {
  const [reports, setReports] = useState<CareerBlueprintReport[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMyReports()
      .then((data) => setReports(data.reports))
      .catch((caught) => setError(caught instanceof Error ? caught.message : "报告加载失败"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="shell page">
      <div className="page-title">
        <h1>我的报告</h1>
        <p>查看当前账号生成过的生涯规划报告。</p>
      </div>
      {error && <div className="error">{error}</div>}
      {loading ? (
        <div className="panel">报告加载中...</div>
      ) : reports.length === 0 ? (
        <section className="panel empty-state">
          <p>你还没有生成报告。</p>
          <Link className="button" to="/assessment">开始填写问卷</Link>
        </section>
      ) : (
        <section className="report-history">
          {reports.map((report) => (
            <article className="panel report-history-card" key={report.id}>
              <div>
                <h2>{report.title}</h2>
                <p className="hint">{new Date(report.createdAt).toLocaleString("zh-CN")} · {report.wordCount} 字</p>
              </div>
              <Link className="button secondary" to={`/reports/${report.id}`}>查看报告</Link>
            </article>
          ))}
        </section>
      )}
    </main>
  );
}
