import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchAdminRecords } from "../api/admin";
import type { AdminRecord, ReportFeedbackRecord } from "../types/report";

const recordsPerPage = 8;

function reportStatusText(record: AdminRecord) {
  if (record.report.qualityStatus === "failed") return "需检查";
  if (record.report.qualityStatus === "warning") return "有提醒";
  if (record.report.qualityStatus === "passed") return "已通过";
  return "未检查";
}

function reportStatusClass(record: AdminRecord) {
  if (record.report.qualityStatus === "failed") return "failed";
  if (record.report.qualityStatus === "warning") return "warning";
  if (record.report.qualityStatus === "passed") return "success";
  return "queued";
}

function averageFeedbackScore(feedback: ReportFeedbackRecord) {
  const total = feedback.understandingScore + feedback.insightScore + feedback.actionScore + feedback.recommendScore;
  return (total / 4).toFixed(1);
}

function compactWarningText(warning: string) {
  const moduleMatch = warning.match(/^模块超过建议上限：(.+?)\s+(\d+)\/(\d+)\s*字符$/);
  if (moduleMatch) {
    return `${moduleMatch[1]}：字数超出（${moduleMatch[2]}/${moduleMatch[3]}）`;
  }

  const reportTooLongMatch = warning.match(/^报告长度超过\s*\d+\s*字符建议范围：(\d+)$/);
  if (reportTooLongMatch) {
    return `报告总长度：字数超出（${reportTooLongMatch[1]}）`;
  }

  const reportTooShortMatch = warning.match(/^报告长度不足\s*\d+\s*字符建议范围：(\d+)$/);
  if (reportTooShortMatch) {
    return `报告总长度：字数不足（${reportTooShortMatch[1]}）`;
  }

  return warning;
}

function reportWarnings(record: AdminRecord) {
  return (record.report.errorMessage || "")
    .split(/[；;]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .map(compactWarningText);
}

function formatTime(value?: string | null) {
  if (!value) return "时间未知";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "时间未知" : date.toLocaleString("zh-CN");
}

export function AdminReportsPage() {
  const [records, setRecords] = useState<AdminRecord[]>([]);
  const [error, setError] = useState("");
  const [keyword, setKeyword] = useState("");
  const [qualityStatus, setQualityStatus] = useState("all");
  const [grade, setGrade] = useState("all");
  const [page, setPage] = useState(1);

  useEffect(() => {
    let closed = false;
    fetchAdminRecords()
      .then((data) => {
        if (closed) return;
        setRecords(data.records);
        setError("");
      })
      .catch((caught) => {
        if (!closed) setError(caught instanceof Error ? caught.message : "报告加载失败。");
      });
    return () => {
      closed = true;
    };
  }, []);

  const gradeOptions = useMemo(
    () => Array.from(new Set(records.map((record) => record.assessment.grade).filter(Boolean))).sort(),
    [records]
  );

  const filteredRecords = useMemo(() => {
    const normalizedKeyword = keyword.trim().toLowerCase();
    return records.filter((record) => {
      if (record.report.generationStatus !== "success") return false;
      const searchableText = [
        record.student.displayName,
        record.student.username,
        record.student.school,
        record.student.studentNumber,
        record.assessment.collegeMajor,
        record.report.title
      ].filter(Boolean).join(" ").toLowerCase();
      return (
        (!normalizedKeyword || searchableText.includes(normalizedKeyword))
        && (qualityStatus === "all" || record.report.qualityStatus === qualityStatus)
        && (grade === "all" || record.assessment.grade === grade)
      );
    });
  }, [grade, keyword, qualityStatus, records]);

  const totalPages = Math.max(1, Math.ceil(filteredRecords.length / recordsPerPage));
  const currentPage = Math.min(page, totalPages);
  const displayedRecords = filteredRecords.slice((currentPage - 1) * recordsPerPage, currentPage * recordsPerPage);

  function resetPage(setter: (value: string) => void, value: string) {
    setter(value);
    setPage(1);
  }

  return (
    <main className="shell page admin-list-page">
      <div className="page-title">
        <h1>已生成报告</h1>
        <p>宽版卡片展示已成功保存的报告、问卷信息、质量状态和学生反馈。</p>
      </div>

      <section className="admin-records">
        <div className="admin-section-head">
          <div>
            <h2>报告记录</h2>
            <p className="hint">可按姓名、学院或专业模糊搜索，也可按报告状态和年级筛选。</p>
          </div>
          <span>{filteredRecords.length} / {records.length} 条</span>
        </div>

        <div className="admin-record-filters" aria-label="报告记录筛选">
          <label className="admin-filter-keyword">
            <span>搜索姓名、学院或专业</span>
            <input
              value={keyword}
              onChange={(event) => resetPage(setKeyword, event.target.value)}
              placeholder="输入姓名、学院或专业关键词"
            />
          </label>
          <label>
            <span>报告状态</span>
            <select value={qualityStatus} onChange={(event) => resetPage(setQualityStatus, event.target.value)}>
              <option value="all">全部</option>
              <option value="passed">已通过</option>
              <option value="warning">有提醒</option>
              <option value="failed">需检查</option>
              <option value="unchecked">未检查</option>
            </select>
          </label>
          <label>
            <span>年级</span>
            <select value={grade} onChange={(event) => resetPage(setGrade, event.target.value)}>
              <option value="all">全部</option>
              {gradeOptions.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>
        </div>

        {error && <div className="error">{error}</div>}
        {records.length === 0 && !error ? (
          <div className="panel empty-state"><p>暂无已生成报告。</p></div>
        ) : filteredRecords.length === 0 ? (
          <div className="panel empty-state"><p>没有符合当前筛选条件的报告。</p></div>
        ) : (
          <>
            <div className="admin-record-list">
              {displayedRecords.map((record) => {
                const feedbacks = record.feedbacks ?? [];
                const warnings = reportWarnings(record);
                return (
                  <article className="panel admin-record-card" id={`report-${record.report.id}`} key={record.report.id}>
                    <div className="admin-record-top">
                      <div>
                        <div className="admin-record-title">
                          <h3>{record.report.title}</h3>
                          <span className={`job-status-pill ${reportStatusClass(record)}`}>{reportStatusText(record)}</span>
                          {record.report.editedAt && <span className="admin-edit-pill">已人工修改</span>}
                        </div>
                        <p className="hint">{formatTime(record.report.createdAt)} · {record.report.wordCount} 字</p>
                      </div>
                      <div className="admin-record-actions">
                        <Link className="button secondary" to={`/reports/${record.report.id}`}>查看</Link>
                        <Link className="button" to={`/admin/reports/${record.report.id}/edit`}>编辑</Link>
                      </div>
                    </div>

                    <div className="admin-record-grid">
                      <div className="admin-record-block">
                        <span className="admin-block-label">学生</span>
                        <strong>{record.student.displayName}</strong>
                        <p>{record.student.username}</p>
                        {record.student.school && <p>学院：{record.student.school}</p>}
                        {record.student.studentNumber && <p>{record.student.studentNumber}</p>}
                      </div>
                      <div className="admin-record-block">
                        <span className="admin-block-label">问卷内容</span>
                        <strong>{record.assessment.educationStage || "-"} · {record.assessment.grade || "-"}</strong>
                        <p>学院 / 专业：{record.assessment.collegeMajor || "-"}</p>
                        <Link className="button secondary admin-block-button" to={`/admin/assessments/${record.report.responseId}`}>
                          查看完整问卷
                        </Link>
                      </div>
                      <div className="admin-record-block">
                        <span className="admin-block-label">报告状态</span>
                        <strong>{reportStatusText(record)}</strong>
                        <p>模型：{record.report.modelName || "-"}</p>
                        <p>版本：{record.report.promptVersion || "-"}</p>
                        {warnings.length > 0 && (
                          <details className="admin-warning-details">
                            <summary>查看提醒内容</summary>
                            <ul>
                              {warnings.map((warning) => <li key={warning}>{warning}</li>)}
                            </ul>
                          </details>
                        )}
                      </div>
                    </div>

                    <div className="admin-feedback-section">
                      <div className="admin-feedback-head">
                        <strong>反馈记录</strong>
                        <span>{feedbacks.length} 条</span>
                      </div>
                      {feedbacks.length === 0 ? (
                        <p className="hint">这个报告还没有学生反馈。</p>
                      ) : (
                        <div className="admin-feedback-list">
                          {feedbacks.map((feedback) => (
                            <div className="admin-feedback-item" key={feedback.id}>
                              <div className="admin-feedback-item-head">
                                <strong>{averageFeedbackScore(feedback)} 分</strong>
                                <span>{formatTime(feedback.createdAt)}</span>
                              </div>
                              <div className="admin-feedback-scores">
                                <span>理解 {feedback.understandingScore}</span>
                                <span>启发 {feedback.insightScore}</span>
                                <span>行动 {feedback.actionScore}</span>
                                <span>推荐 {feedback.recommendScore}</span>
                              </div>
                              <p>{feedback.comment?.trim() || "未填写文字反馈。"}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </article>
                );
              })}
            </div>
            {totalPages > 1 && (
              <nav className="admin-pagination" aria-label="已生成报告分页">
                <button className="button secondary" disabled={currentPage === 1} onClick={() => setPage(currentPage - 1)}>上一页</button>
                <span>第 {currentPage} / {totalPages} 页</span>
                <button className="button secondary" disabled={currentPage === totalPages} onClick={() => setPage(currentPage + 1)}>下一页</button>
              </nav>
            )}
          </>
        )}
      </section>
    </main>
  );
}
