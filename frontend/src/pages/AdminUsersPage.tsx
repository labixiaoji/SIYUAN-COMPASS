import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchAdminUsers, type AdminUser } from "../api/admin";

const pageSize = 20;

function formatTime(value?: string | null) {
  if (!value) return "时间未知";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "时间未知" : date.toLocaleString("zh-CN");
}

function roleText(role: AdminUser["role"]) {
  return role === "admin" ? "管理员" : "学生";
}

export function AdminUsersPage() {
  const [items, setItems] = useState<AdminUser[]>([]);
  const [summary, setSummary] = useState({ total: 0, studentCount: 0, adminCount: 0 });
  const [total, setTotal] = useState(0);
  const [keyword, setKeyword] = useState("");
  const [role, setRole] = useState("all");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let closed = false;
    setLoading(true);
    fetchAdminUsers({
      keyword: keyword.trim() || undefined,
      role,
      limit: pageSize,
      offset: (page - 1) * pageSize
    }).then((data) => {
      if (closed) return;
      setItems(data.items);
      setSummary(data.summary);
      setTotal(data.total);
      setError("");
    }).catch((caught) => {
      if (!closed) setError(caught instanceof Error ? caught.message : "用户列表加载失败。");
    }).finally(() => {
      if (!closed) setLoading(false);
    });
    return () => {
      closed = true;
    };
  }, [keyword, page, role]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  function updateKeyword(value: string) {
    setKeyword(value);
    setPage(1);
  }

  function updateRole(value: string) {
    setRole(value);
    setPage(1);
  }

  return (
    <main className="shell page admin-list-page admin-users-page">
      <div className="page-title">
        <h1>用户管理</h1>
        <p>查看已注册账号数量、角色和使用情况。此页面仅提供查询，不会修改用户数据。</p>
      </div>

      <section className="metrics user-summary-metrics" aria-label="用户统计">
        <div className="panel stat">
          <strong>{summary.total}</strong>
          <span>全部用户</span>
        </div>
        <div className="panel stat">
          <strong>{summary.studentCount}</strong>
          <span>学生账号</span>
        </div>
        <div className="panel stat">
          <strong>{summary.adminCount}</strong>
          <span>管理员账号</span>
        </div>
      </section>

      <section className="panel admin-list-panel admin-users-panel">
        <div className="admin-section-head">
          <div>
            <h2>账号列表</h2>
            <p className="hint">当前筛选条件下共 {total} 个账号。</p>
          </div>
        </div>
        <div className="admin-record-filters">
          <label className="admin-filter-keyword">
            <span>搜索</span>
            <input
              value={keyword}
              onChange={(event) => updateKeyword(event.target.value)}
              placeholder="账号、昵称或用户 ID"
            />
          </label>
          <label>
            <span>用户角色</span>
            <select value={role} onChange={(event) => updateRole(event.target.value)}>
              <option value="all">全部</option>
              <option value="student">学生</option>
              <option value="admin">管理员</option>
            </select>
          </label>
        </div>

        {error && <div className="error">{error}</div>}
        {loading ? (
          <p className="hint">用户列表加载中...</p>
        ) : items.length === 0 ? (
          <div className="empty-state"><p>暂无符合条件的用户。</p></div>
        ) : (
          <div className="admin-table-wrap">
            <table className="admin-table admin-users-table">
              <thead>
                <tr>
                  <th>用户</th>
                  <th>角色</th>
                  <th>注册时间</th>
                  <th>最后活动</th>
                  <th>问卷</th>
                  <th>生成任务</th>
                  <th>报告</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <Link
                        className="admin-user-link"
                        to={`/admin/assessments?keyword=${encodeURIComponent(item.username)}`}
                      >
                        {item.displayName}
                      </Link>
                      <span>{item.username}</span>
                      <span className="admin-id-text">{item.id}</span>
                    </td>
                    <td><span className={`admin-role-pill ${item.role}`}>{roleText(item.role)}</span></td>
                    <td>{formatTime(item.createdAt)}</td>
                    <td>{formatTime(item.lastActivityAt)}</td>
                    <td><strong>{item.assessmentCount}</strong></td>
                    <td><strong>{item.generationJobCount}</strong></td>
                    <td><strong>{item.reportCount}</strong></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <nav className="admin-pagination" aria-label="用户列表分页">
            <button className="button secondary" disabled={page === 1} onClick={() => setPage(page - 1)}>上一页</button>
            <span>第 {page} / {totalPages} 页 · 共 {total} 个</span>
            <button className="button secondary" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>下一页</button>
          </nav>
        )}
      </section>
    </main>
  );
}
