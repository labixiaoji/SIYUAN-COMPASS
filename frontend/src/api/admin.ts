import { apiRequest } from "./client";
import type { AdminMetrics, AdminRecord, CareerBlueprintReport } from "../types/report";

export function fetchAdminMetrics() {
  return apiRequest<AdminMetrics>("/admin/metrics");
}

export function fetchAdminRecords() {
  return apiRequest<{ records: AdminRecord[] }>("/admin/records");
}

export function updateAdminReport(reportId: string, title: string, content: string) {
  return apiRequest<CareerBlueprintReport>(`/admin/reports/${reportId}`, {
    method: "PUT",
    body: JSON.stringify({ title, content })
  });
}
