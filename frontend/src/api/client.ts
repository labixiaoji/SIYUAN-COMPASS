const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers
    }
  });
  const data = await response.json();

  if (!response.ok) {
    const detail = data.detail;
    const stagedError = detail?.stage && detail?.error ? `${detail.stage}：${detail.error}` : undefined;
    const message = stagedError || detail?.errors?.join("；") || detail?.error || data.error || "请求失败";
    throw new Error(message);
  }

  return data as T;
}
