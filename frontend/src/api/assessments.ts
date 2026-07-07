import { apiRequest } from "./client";
import type { AssessmentResponseInput } from "../types/assessment";

export type AssessmentSubmitResult = {
  userId: string;
  responseId: string;
  profileId: string;
  reportId: string;
  generationStatus: string;
};

export type GenerationJobStatus = {
  jobId: string;
  status: "queued" | "running" | "success" | "failed" | "cancelled";
  stage: string;
  progress: number;
  message: string;
  userId?: string;
  responseId?: string;
  profileId?: string;
  reportId?: string;
  generationStatus?: string;
  error?: string;
  createdAt?: string;
  updatedAt?: string;
};

export function submitAssessment(input: AssessmentResponseInput & { userId?: string }) {
  return apiRequest<AssessmentSubmitResult>("/assessments", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export function createAssessmentJob(input: AssessmentResponseInput & { userId?: string }) {
  return apiRequest<{ jobId: string; status: "queued" }>("/assessment-jobs", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export function fetchAssessmentJob(jobId: string) {
  return apiRequest<GenerationJobStatus>(`/assessment-jobs/${jobId}`);
}

export function cancelAssessmentJob(jobId: string) {
  return apiRequest<GenerationJobStatus>(`/assessment-jobs/${jobId}/cancel`, {
    method: "POST"
  });
}
