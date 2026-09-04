import { Link, NavLink, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ProtectedRoute } from "../auth/ProtectedRoute";
import { AppFooter } from "../components/AppFooter";
import { AdminAssessmentPage } from "../pages/AdminAssessmentPage";
import { AdminAssessmentsPage } from "../pages/AdminAssessmentsPage";
import { AdminAuditLogsPage } from "../pages/AdminAuditLogsPage";
import { AdminGenerationJobDetailPage } from "../pages/AdminGenerationJobDetailPage";
import { AdminGenerationJobDraftPage } from "../pages/AdminGenerationJobDraftPage";
import { AdminLayout } from "../pages/AdminLayout";
import { AdminPage } from "../pages/AdminPage";
import { AdminReportsPage } from "../pages/AdminReportsPage";
import { AdminReportEditPage } from "../pages/AdminReportEditPage";
import { AssessmentPage } from "../pages/AssessmentPage";
import { FeedbackPage } from "../pages/FeedbackPage";
import { HomePage } from "../pages/HomePage";
import { LoginPage } from "../pages/LoginPage";
import { MyReportsPage } from "../pages/MyReportsPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { PrivacyPage } from "../pages/PrivacyPage";
import { RegisterPage } from "../pages/RegisterPage";
import { ReportPage } from "../pages/ReportPage";

function GenerationJobsRedirect() {
  const location = useLocation();
  return <Navigate to={{ pathname: "/admin/assessments", search: location.search }} replace />;
}

export function App() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="shell topbar-inner">
          <Link className="brand" to="/">交小航——你的AI生涯伙伴</Link>
          <nav className="nav">
            {user?.role === "student" && <NavLink to="/assessment">开始填写</NavLink>}
            {user?.role === "student" && <NavLink to="/my-reports">我的报告</NavLink>}
            {user?.role === "admin" && <NavLink to="/admin">管理员后台</NavLink>}
            {user ? (
              <>
                <span className="nav-user">{user.displayName}</span>
                <button className="nav-button nav-logout" onClick={logout}>退出</button>
              </>
            ) : (
              <NavLink to="/login">登录</NavLink>
            )}
          </nav>
        </div>
      </header>
      <div className="app-content">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/assessment" element={<ProtectedRoute role="student"><AssessmentPage /></ProtectedRoute>} />
          <Route path="/my-reports" element={<ProtectedRoute role="student"><MyReportsPage /></ProtectedRoute>} />
          <Route path="/reports/:reportId" element={<ProtectedRoute><ReportPage /></ProtectedRoute>} />
          <Route path="/reports/:reportId/feedback" element={<ProtectedRoute role="student"><FeedbackPage /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute role="admin"><AdminLayout><AdminPage /></AdminLayout></ProtectedRoute>} />
          <Route path="/admin/assessments" element={<ProtectedRoute role="admin"><AdminLayout><AdminAssessmentsPage /></AdminLayout></ProtectedRoute>} />
          <Route path="/admin/assessments/:responseId" element={<ProtectedRoute role="admin"><AdminLayout><AdminAssessmentPage /></AdminLayout></ProtectedRoute>} />
          <Route path="/admin/generation-jobs" element={<ProtectedRoute role="admin"><GenerationJobsRedirect /></ProtectedRoute>} />
          <Route path="/admin/generation-jobs/:jobId/draft" element={<ProtectedRoute role="admin"><AdminLayout><AdminGenerationJobDraftPage /></AdminLayout></ProtectedRoute>} />
          <Route path="/admin/generation-jobs/:jobId" element={<ProtectedRoute role="admin"><AdminLayout><AdminGenerationJobDetailPage /></AdminLayout></ProtectedRoute>} />
          <Route path="/admin/reports" element={<ProtectedRoute role="admin"><AdminLayout><AdminReportsPage /></AdminLayout></ProtectedRoute>} />
          <Route path="/admin/reports/:reportId/edit" element={<ProtectedRoute role="admin"><AdminLayout><AdminReportEditPage /></AdminLayout></ProtectedRoute>} />
          <Route path="/admin/audit-logs" element={<ProtectedRoute role="admin"><AdminLayout><AdminAuditLogsPage /></AdminLayout></ProtectedRoute>} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </div>
      <AppFooter />
    </div>
  );
}
