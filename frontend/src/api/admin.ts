import { apiRequest } from "./client";
import type { AdminMetrics } from "../types/report";

export function fetchAdminMetrics() {
  return apiRequest<AdminMetrics>("/admin/metrics");
}
