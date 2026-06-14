import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";

export function ProtectedRoute({
  children,
  role
}: {
  children: ReactNode;
  role?: "student" | "admin";
}) {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) {
    return <Navigate replace state={{ from: location.pathname }} to="/login" />;
  }
  if (role && user.role !== role) {
    return <Navigate replace to={user.role === "admin" ? "/admin" : "/assessment"} />;
  }
  return children;
}
