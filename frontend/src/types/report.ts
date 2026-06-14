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

export type AdminRecord = {
  report: CareerBlueprintReport;
  student: {
    id: string;
    username: string;
    displayName: string;
  };
  assessment: {
    grade: string;
    collegeMajor: string;
    submittedAt: string;
  };
};
