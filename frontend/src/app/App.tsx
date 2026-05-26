import { Link, NavLink, Route, Routes } from "react-router-dom";
import { AdminPage } from "../pages/AdminPage";
import { AssessmentPage } from "../pages/AssessmentPage";
import { FeedbackPage } from "../pages/FeedbackPage";
import { HomePage } from "../pages/HomePage";
import { ReportPage } from "../pages/ReportPage";

export function App() {
  return (
    <>
      <header className="topbar">
        <div className="shell topbar-inner">
          <Link className="brand" to="/">思源 Compass</Link>
          <nav className="nav">
            <NavLink to="/assessment">开始填写</NavLink>
            <NavLink to="/admin">后台</NavLink>
          </nav>
        </div>
      </header>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/assessment" element={<AssessmentPage />} />
        <Route path="/reports/:reportId" element={<ReportPage />} />
        <Route path="/reports/:reportId/feedback" element={<FeedbackPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </>
  );
}
