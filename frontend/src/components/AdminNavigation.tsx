import { NavLink } from "react-router-dom";

const links = [
  { to: "/admin", label: "总览", end: true },
  { to: "/admin/assessments", label: "填写记录" },
  { to: "/admin/reports", label: "已生成报告" },
  { to: "/admin/audit-logs", label: "报告修改记录" }
];

export function AdminNavigation() {
  return (
    <nav className="admin-navigation" aria-label="管理员导航">
      {links.map((link) => (
        <NavLink
          className={({ isActive }) => `admin-navigation-link ${isActive ? "active" : ""}`}
          end={link.end}
          key={link.to}
          to={link.to}
        >
          {link.label}
        </NavLink>
      ))}
    </nav>
  );
}
