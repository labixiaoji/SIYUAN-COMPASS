import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchAdminAssessments, fetchAdminMetrics } from "../api/admin";
import type { AdminAssessmentRecord, AdminMetrics } from "../types/report";

function statusText(status: string) {
  const labels: Record<string, string> = {
    queued: "等待生成",
    running: "生成中",
    success: "已生成",
    failed: "生成失败",
    cancelled: "已取消",
    unknown: "未记录"
  };
  return labels[status] || status;
}

function statusClass(status: string) {
  if (status === "success") return "success";
  if (status === "failed") return "failed";
  if (status === "cancelled") return "warning";
  return "queued";
}

function formatTime(value?: string | null) {
  if (!value) return "时间未知";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "时间未知" : date.toLocaleString("zh-CN");
}

function failureText(item: AdminAssessmentRecord) {
  return item.failure?.message || item.error || "未记录具体错误信息";
}

export function AdminPage() {
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [recentFailures, setRecentFailures] = useState<AdminAssessmentRecord[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let closed = false;
    Promise.all([
      fetchAdminMetrics(),
      fetchAdminAssessments({ status: "failed", limit: 5, offset: 0 })
    ]).then(([nextMetrics, nextFailures]) => {
      if (closed) return;
      setMetrics(nextMetrics);
      setRecentFailures(nextFailures.items);
    }).catch((caught) => {
      if (!closed) setError(caught instanceof Error ? caught.message : "后台数据加载失败。");
    });
    return () => {
      closed = true;
    };
  }, []);

  if (error) {
    return <main className="shell page"><div className="error">{error}</div></main>;
  }

  if (!metrics) {
    return <main className="shell page"><div className="panel">后台数据加载中...</div></main>;
  }

  const failedCount = metrics.generationFailedCount ?? metrics.reportFailedCount;
  const runningCount = metrics.generationRunningCount ?? 0;
  const queuedCount = metrics.generationQueuedCount ?? 0;

  return (
    <main className="shell page admin-overview-page">
      <div className="page-title">
        <h1>管理员后台</h1>
        <p>填写记录集中展示问卷提交和生成进度，已生成报告使用卡片方式统一查看。</p>
      </div>

      <section className="metrics admin-metrics" aria-label="后台统计">
        <Link className="panel stat admin-metric-link" to="/admin/users">
          <strong>{metrics.userCount}</strong>
          <span>注册用户</span>
          <small>查看账号和使用情况</small>
        </Link>
        <Link className="panel stat admin-metric-link" to="/admin/assessments">
          <strong>{metrics.assessmentCount}</strong>
          <span>填写记录</span>
          <small>查看所有问卷提交</small>
        </Link>
        <Link className="panel stat admin-metric-link" to="/admin/reports">
          <strong>{metrics.reportSuccessCount}</strong>
          <span>已生成报告</span>
          <small>查看已生成报告</small>
        </Link>
        <Link className="panel stat admin-metric-link admin-metric-failed" to="/admin/assessments?status=failed">
          <strong>{failedCount}</strong>
          <span>失败记录</span>
          <small>查看阶段和报错信息</small>
        </Link>
        <Link className="panel stat admin-metric-link" to="/admin/assessments?status=running">
          <strong>{runningCount}</strong>
          <span>生成中记录</span>
          <small>查看当前处理进度</small>
        </Link>
        <Link className="panel stat admin-metric-link" to="/admin/assessments?status=queued">
          <strong>{queuedCount}</strong>
          <span>排队中记录</span>
          <small>等待 Worker 领取</small>
        </Link>
      </section>

      <section className="panel admin-score-panel">
        <div className="admin-section-head">
          <div>
            <h2>报告评分</h2>
            <p className="hint">四项平均分来自学生提交的报告反馈。</p>
          </div>
          <Link className="button secondary" to="/admin/reports">查看报告</Link>
        </div>
        <div className="score-metrics">
          <div><strong>{metrics.averageUnderstandingScore}</strong><span>平均理解度</span></div>
          <div><strong>{metrics.averageInsightScore}</strong><span>平均启发度</span></div>
          <div><strong>{metrics.averageActionScore}</strong><span>平均行动性</span></div>
          <div><strong>{metrics.averageRecommendScore}</strong><span>平均推荐度</span></div>
        </div>
        <div className="low-score-reports">
          <h3>低分报告列表</h3>
          {metrics.lowScoreReports.length === 0 ? (
            <p className="hint">暂无任一评分低于或等于 2 分的报告。</p>
          ) : (
            <div className="low-score-list">
              {metrics.lowScoreReports.map((reportId) => (
                <Link className="low-score-link" key={reportId} to={`/reports/${reportId}`}>
                  报告 {reportId.slice(0, 8)}
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="panel admin-overview-failures">
        <div className="admin-section-head">
          <div>
            <h2>最近失败记录</h2>
            <p className="hint">失败记录会保留脱敏问卷快照，填写记录页可查看失败阶段和定位信息。</p>
          </div>
          <Link className="button secondary" to="/admin/assessments?status=failed">查看全部</Link>
        </div>
        {recentFailures.length === 0 ? (
          <p className="hint">暂无失败记录。</p>
        ) : (
          <div className="admin-failure-list">
            {recentFailures.map((item) => {
              const detailPath = item.jobId
                ? `/admin/generation-jobs/${item.jobId}`
                : item.responseId
                  ? `/admin/assessments/${item.responseId}`
                  : "/admin/assessments";
              return (
                <Link className="admin-failure-row" key={item.recordId} to={detailPath}>
                  <div>
                    <strong>{item.student.displayName}</strong>
                    <span>{formatTime(item.submittedAt)} · {item.failure?.code || "UNKNOWN_ERROR"}</span>
                  </div>
                  <div className="admin-failure-row-detail">
                    <span className={`job-status-pill ${statusClass(item.taskStatus)}`}>{statusText(item.taskStatus)}</span>
                    <p>{failureText(item)}</p>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </section>

      <section className="panel admin-recent-reports">
        <div className="admin-section-head">
          <div>
            <h2>最近已生成报告</h2>
            <p className="hint">质量状态只表示报告校验结果，不等同于生成过程是否失败。</p>
          </div>
          <Link className="button secondary" to="/admin/reports">查看全部</Link>
        </div>
        {metrics.recentReports.length === 0 ? (
          <p className="hint">暂无已生成报告。</p>
        ) : (
          <div className="admin-recent-report-list">
            {metrics.recentReports.map((report) => (
              <Link className="admin-recent-report-row" key={report.id} to={`/reports/${report.id}`}>
                <div>
                  <strong>{report.title}</strong>
                  <span>{formatTime(report.createdAt)} · {report.wordCount} 字</span>
                </div>
                <span className={`job-status-pill ${report.qualityStatus === "failed" ? "failed" : report.qualityStatus === "warning" ? "warning" : "success"}`}>
                  {report.qualityStatus === "passed" ? "已通过" : report.qualityStatus === "warning" ? "有提醒" : report.qualityStatus === "failed" ? "需检查" : "未检查"}
                </span>
              </Link>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
