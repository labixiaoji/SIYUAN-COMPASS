import { apiRequest } from "./client";
import type { GenerationJobDraft } from "./assessments";
import type { AssessmentResponse } from "../types/assessment";
import type {
  AdminAssessmentRecord,
  AdminGenerationJob,
  AdminMetrics,
  AdminRecord,
  CareerBlueprintReport
} from "../types/report";

export type AdminAuditLog = {
  id: string;
  adminId: string;
  adminDisplayName: string;
  action: string;
  targetType: string;
  targetId: string;
  createdAt: string;
  details: Record<string, unknown>;
};

export function fetchAdminMetrics() {
  return apiRequest<AdminMetrics>("/admin/metrics");
}

export function fetchAdminRecords() {
  return apiRequest<{ records: AdminRecord[] }>("/admin/records");
}

function queryString(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") search.set(key, String(value));
  });
  const value = search.toString();
  return value ? `?${value}` : "";
}

export function fetchAdminAssessments(params: {
  status?: string;
  keyword?: string;
  limit?: number;
  offset?: number;
} = {}) {
  return apiRequest<{ total: number; items: AdminAssessmentRecord[] }>(
    `/admin/assessments${queryString(params)}`
  );
}

export function fetchAdminGenerationJobs(params: {
  status?: string;
  keyword?: string;
  limit?: number;
  offset?: number;
} = {}) {
  return apiRequest<{ total: number; items: AdminGenerationJob[] }>(
    `/admin/generation-jobs${queryString(params)}`
  );
}

export function fetchAdminGenerationJob(jobId: string) {
  return apiRequest<AdminGenerationJob>(`/admin/generation-jobs/${jobId}`);
}

export function fetchAdminGenerationJobDraft(jobId: string) {
  return apiRequest<GenerationJobDraft>(`/admin/generation-jobs/${jobId}/draft`);
}

export function fetchAdminAuditLogs(limit = 20, offset = 0) {
  return apiRequest<{ total: number; items: AdminAuditLog[] }>(
    `/admin/audit-logs?limit=${limit}&offset=${offset}`
  );
}

export function fetchAdminAssessment(responseId: string) {
  return apiRequest<AssessmentResponse>(`/admin/assessments/${responseId}`);
}

export function updateAdminReport(reportId: string, title: string, content: string) {
  return apiRequest<CareerBlueprintReport>(`/admin/reports/${reportId}`, {
    method: "PUT",
    body: JSON.stringify({ title, content })
  });
}
