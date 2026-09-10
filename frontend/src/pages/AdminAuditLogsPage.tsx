import { useEffect, useState } from "react";
import { fetchAdminAuditLogs, type AdminAuditLog } from "../api/admin";

const pageSize = 30;

const actionLabels: Record<string, string> = {
  "report.update": "修改报告",
  "report.delete": "删除报告"
};

function formatTime(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "时间未知" : date.toLocaleString("zh-CN");
}

function detailText(details: Record<string, unknown>) {
  const changedFields = Array.isArray(details.changedFields)
    ? details.changedFields.filter((field): field is string => typeof field === "string")
    : [];
  const fieldLabels: Record<string, string> = {
    title: "标题",
    content: "正文"
  };
  const qualityLabels: Record<string, string> = {
    passed: "质量通过",
    warning: "有提醒",
    failed: "需检查",
    unchecked: "未检查"
  };
  const labels = changedFields.map((field) => fieldLabels[field] || field);
  const parts: string[] = [];
  if (labels.length > 0) parts.push(`修改：${labels.join("、")}`);
  if (typeof details.qualityStatus === "string") {
    parts.push(`质量状态：${qualityLabels[details.qualityStatus] || details.qualityStatus}`);
  }
  if (typeof details.wordCount === "number") parts.push(`字数：${details.wordCount}`);
  return parts.join(" · ") || "—";
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
        if (!closed) setError(caught instanceof Error ? caught.message : "报告修改记录加载失败。");
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
        <h1>报告修改记录</h1>
        <p>这里只记录管理员对报告的修改或删除，不记录普通查看操作。</p>
      </div>

      <section className="panel admin-list-panel">
        {error && <div className="error">{error}</div>}
        {loading ? (
          <p className="hint">报告修改记录加载中...</p>
        ) : items.length === 0 ? (
          <div className="empty-state"><p>暂无报告修改记录。</p></div>
        ) : (
          <div className="admin-table-wrap">
            <table className="admin-table admin-audit-table">
              <thead>
                <tr>
                  <th>时间</th>
                  <th>管理员</th>
                  <th>修改操作</th>
                  <th>报告</th>
                  <th>修改内容</th>
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
                    <td>{actionLabels[item.action] || "报告修改"}</td>
                    <td>
                      <strong>报告</strong>
                      <span className="admin-id-text">{item.targetId}</span>
                    </td>
                    <td>{detailText(item.details || {})}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <nav className="admin-pagination" aria-label="报告修改记录分页">
            <button className="button secondary" disabled={page === 1} onClick={() => setPage(page - 1)}>上一页</button>
            <span>第 {page} / {totalPages} 页 · 共 {total} 条</span>
            <button className="button secondary" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>下一页</button>
          </nav>
        )}
      </section>
    </main>
  );
}
