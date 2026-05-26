export type AbilityScores = {
  logic: number;
  expression: number;
  spatialDesign: number;
  interpersonal: number;
};

export type InterestScores = {
  handsOn: number;
  research: number;
  creation: number;
  helping: number;
  leadership: number;
  detail: number;
};

export type AssessmentResponseInput = {
  grade: string;
  collegeMajor: string;
  hometown?: string;
  preferredCity: string;
  careerConfusions: string[];
  mainConfusionText?: string;
  educationPath: string;
  educationPathReasons: string[];
  educationCertainty: number;
  phdIntention: string;
  phdReasons: string[];
  fiveYearPriorities: string[];
  targetIndustries: string[];
  futureRoleType: string;
  lifePreference: string;
  tenYearSelfDescription?: string;
  topValuesRanked: string[];
  abilityScores: AbilityScores;
  interestScores: InterestScores;
  currentPreparations: string[];
  missingResources: string[];
  majorOutcomeAwareness: string;
  targetJobAwareness: string;
  healthEnergyStatus: string;
  exerciseFrequency?: string;
};
