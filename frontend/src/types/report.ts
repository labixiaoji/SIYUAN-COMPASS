import type { AssessmentResponseInput } from "./assessment";

export type CareerBlueprintReport = {
  id: string;
  userId: string;
  responseId: string;
  profileId: string;
  title: string;
  content: string;
  wordCount: number;
  generationStatus: "pending" | "success" | "failed";
  qualityStatus: "unchecked" | "passed" | "warning" | "failed";
  errorMessage?: string;
  modelName: string;
  promptVersion: string;
  retryCount: number;
  createdAt: string;
  updatedAt: string;
  editedAt?: string;
  editedBy?: string;
  inputSnapshot?: {
    response?: Partial<AssessmentResponseInput> & Record<string, unknown>;
  };
};

export type AdminMetrics = {
  assessmentCount: number;
  reportSuccessCount: number;
  reportFailedCount: number;
  feedbackCount: number;
  averageUnderstandingScore: number;
  averageInsightScore: number;
  averageActionScore: number;
  averageRecommendScore: number;
  lowScoreReports: string[];
  recentReports: CareerBlueprintReport[];
};

export type ReportFeedbackRecord = {
  id: string;
  reportId: string;
  userId: string;
  understandingScore: number;
  insightScore: number;
  actionScore: number;
  recommendScore: number;
  comment?: string;
  createdAt: string;
};

export type AdminRecord = {
  report: CareerBlueprintReport;
  student: {
    id: string;
    username: string;
    displayName: string;
    school?: string;
    studentNumber?: string;
    contactInfo?: string;
  };
  assessment: {
    educationStage?: string;
    grade: string;
    collegeMajor: string;
    careerConfusions?: string[];
    submittedAt: string;
  };
  feedbacks: ReportFeedbackRecord[];
};
