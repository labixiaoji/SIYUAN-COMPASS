import type { AssessmentResponseInput } from "./assessment";
import type { GenerationFailure, GenerationJobStatus } from "../api/assessments";

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
  accountDisplayName?: string;
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
  generationFailedCount?: number;
  generationRunningCount?: number;
  generationQueuedCount?: number;
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

export type AdminGenerationJob = GenerationJobStatus & {
  draftAvailable: boolean;
  student: {
    id: string;
    username: string;
    displayName: string;
  };
};

export type AdminAssessmentRecord = {
  recordId: string;
  jobId?: string | null;
  responseId?: string | null;
  student: {
    id: string;
    username: string;
    displayName: string;
  };
  submittedAt?: string | null;
  educationStage?: string;
  grade?: string;
  collegeMajor?: string;
  taskStatus: string;
  reportStatus?: string | null;
  reportId?: string | null;
  draftAvailable: boolean;
  failure?: GenerationFailure | null;
  error?: string | null;
};
