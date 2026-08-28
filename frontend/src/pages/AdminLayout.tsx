import type { ReactNode } from "react";
import { AdminNavigation } from "../components/AdminNavigation";

export function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <div className="admin-layout">
      <div className="shell admin-layout-shell">
        <AdminNavigation />
      </div>
      {children}
    </div>
  );
}
