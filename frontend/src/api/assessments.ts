import { apiRequest } from "./client";
import type { AssessmentResponseInput } from "../types/assessment";

export type AssessmentSubmitResult = {
  userId: string;
  responseId: string;
  profileId: string;
  reportId: string;
  generationStatus: string;
};

export function submitAssessment(input: AssessmentResponseInput & { userId?: string }) {
  return apiRequest<AssessmentSubmitResult>("/assessments", {
    method: "POST",
    body: JSON.stringify(input)
  });
}
