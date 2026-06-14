import { createContext, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { AuthResult, AuthUser } from "../api/auth";

const TOKEN_KEY = "siyuan_auth_token";
const USER_KEY = "siyuan_auth_user";

type AuthContextValue = {
  user: AuthUser | null;
  completeLogin: (result: AuthResult) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredUser(): AuthUser | null {
  try {
    const value = window.localStorage.getItem(USER_KEY);
    return value ? JSON.parse(value) : null;
  } catch {
    return null;
  }
}

export function getAuthToken() {
  return window.localStorage.getItem(TOKEN_KEY);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(readStoredUser);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    completeLogin(result) {
      window.localStorage.setItem(TOKEN_KEY, result.token);
      window.localStorage.setItem(USER_KEY, JSON.stringify(result.user));
      setUser(result.user);
    },
    logout() {
      window.localStorage.removeItem(TOKEN_KEY);
      window.localStorage.removeItem(USER_KEY);
      setUser(null);
    }
  }), [user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth 必须在 AuthProvider 中使用");
  return value;
}
