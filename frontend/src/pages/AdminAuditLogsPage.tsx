import { useEffect, useState } from "react";
import { fetchAdminAuditLogs, type AdminAuditLog } from "../api/admin";

const pageSize = 30;

const actionLabels: Record<string, string> = {
  "admin.metrics.read": "查看统计指标",
  "admin.records.read": "查看生成记录",
  "admin.assessments.read": "查看填写记录",
  "admin.generation_jobs.read": "查看生成任务",
  "generation_job.read": "查看任务详情",
  "generation_job.draft.read": "查看任务问卷",
  "admin.audit.read": "查看审计日志",
  "assessment.read": "查看完整问卷",
  "report.read": "查看报告",
  "report.update": "修改报告",
  "report.delete": "删除报告"
};

function formatTime(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "时间未知" : date.toLocaleString("zh-CN");
}

export function AdminAuditLogsPage() {
  const [items, setItems] = useState<AdminAuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let closed = false;
    setLoading(true);
    fetchAdminAuditLogs(pageSize, (page - 1) * pageSize)
      .then((data) => {
        if (closed) return;
        setItems(data.items);
        setTotal(data.total);
        setError("");
      })
      .catch((caught) => {
        if (!closed) setError(caught instanceof Error ? caught.message : "审计日志加载失败。");
      })
      .finally(() => {
        if (!closed) setLoading(false);
      });
    return () => {
      closed = true;
    };
  }, [page]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <main className="shell page admin-list-page">
      <div className="page-title">
        <h1>审计日志</h1>
        <p>单独查看管理员对学生问卷、生成任务、报告和隐私数据的敏感操作。</p>
      </div>

      <section className="panel admin-list-panel">
        {error && <div className="error">{error}</div>}
        {loading ? (
          <p className="hint">审计日志加载中...</p>
        ) : items.length === 0 ? (
          <div className="empty-state"><p>暂无管理员操作记录。</p></div>
        ) : (
          <div className="admin-table-wrap">
            <table className="admin-table admin-audit-table">
              <thead>
                <tr>
                  <th>时间</th>
                  <th>管理员</th>
                  <th>操作</th>
                  <th>目标</th>
                  <th>附加信息</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>{formatTime(item.createdAt)}</td>
                    <td>
                      <strong>{item.adminDisplayName}</strong>
                      <span>{item.adminId}</span>
                    </td>
                    <td>{actionLabels[item.action] || item.action}</td>
                    <td>
                      <strong>{item.targetType}</strong>
                      <span>{item.targetId === "all" ? "全部记录" : item.targetId}</span>
                    </td>
                    <td>{Object.keys(item.details || {}).length > 0 ? JSON.stringify(item.details) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <nav className="admin-pagination" aria-label="审计日志分页">
            <button className="button secondary" disabled={page === 1} onClick={() => setPage(page - 1)}>上一页</button>
            <span>第 {page} / {totalPages} 页 · 共 {total} 条</span>
            <button className="button secondary" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>下一页</button>
          </nav>
        )}
      </section>
    </main>
  );
}
