import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../api/auth";
import { useAuth } from "../auth/AuthContext";

export function RegisterPage() {
  const navigate = useNavigate();
  const { completeLogin } = useAuth();
  const [displayName, setDisplayName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event?: FormEvent) {
    event?.preventDefault();
    const nextDisplayName = displayName.trim();
    const nextUsername = username.trim();
    if (!nextDisplayName) {
      setError("请填写姓名或昵称。");
      return;
    }
    if (nextUsername.length < 3) {
      setError("用户名至少需要 3 位。");
      return;
    }
    if (!/^[A-Za-z0-9_-]+$/.test(nextUsername)) {
      setError("用户名只能包含字母、数字、下划线和连字符。");
      return;
    }
    if (password.length < 8) {
      setError("密码至少需要 8 位。");
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      const result = await register(nextUsername, password, nextDisplayName);
      completeLogin(result);
      navigate("/assessment", { replace: true });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "注册失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="shell auth-page">
      <form className="panel auth-card" onSubmit={submit}>
        <h1>注册学生账号</h1>
        <div className="field">
          <label>姓名或昵称</label>
          <input className="input" value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
        </div>
        <div className="field">
          <label>用户名</label>
          <input className="input" autoComplete="username" placeholder="至少3位，可用字母、数字、_、-" value={username} onChange={(event) => setUsername(event.target.value)} />
        </div>
        <div className="field">
          <label>密码</label>
          <input className="input" autoComplete="new-password" placeholder="至少8位" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
        </div>
        {error && <div className="error">{error}</div>}
        <button className="button auth-submit" disabled={submitting} type="submit">
          {submitting ? "注册中..." : "注册并登录"}
        </button>
        <p className="auth-switch">已有账号？<Link to="/login">返回登录</Link></p>
      </form>
    </main>
  );
}
