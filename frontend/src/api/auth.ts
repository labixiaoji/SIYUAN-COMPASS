import { apiRequest } from "./client";

export type AuthUser = {
  id: string;
  username: string;
  displayName: string;
  role: "student" | "admin";
};

export type AuthResult = {
  token: string;
  user: AuthUser;
};

export function login(username: string, password: string) {
  return apiRequest<AuthResult>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password })
  });
}

export function register(username: string, password: string, displayName: string) {
  return apiRequest<AuthResult>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password, displayName })
  });
}

export function fetchCurrentUser() {
  return apiRequest<AuthUser>("/auth/me");
}

export function changePassword(currentPassword: string, newPassword: string) {
  return apiRequest<{ message: string }>("/auth/change-password", {
    method: "POST",
    body: JSON.stringify({ currentPassword, newPassword })
  });
}
