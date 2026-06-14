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
  gender: string;
  collegeMajor: string;
  hometown?: string;
  mastersIntention: string;
  mastersPlan?: string;
  phdIntention: string;
  phdPlan?: string;
  educationPathReasons: string[];
  educationCertainty: number;
  fiveYearCity: string;
  fiveYearIncome: string;
  fiveYearIndustry: string;
  fiveYearRole: string;
  fiveYearFamilyStatus: string;
  fiveYearHousingPlan: string;
  fiveYearHobbiesSkills: string;
  tenYearCity: string;
  tenYearIncome: string;
  tenYearIndustry: string;
  tenYearRole: string;
  tenYearFamilyStatus: string;
  tenYearHousingPlan: string;
  tenYearHobbiesSkills: string;
  topValuesRanked: string[];
  abilityScores: AbilityScores;
  interestScores: InterestScores;
  currentPreparations: string[];
  missingResources: string[];
  majorOutcomeAwareness: string;
  targetJobAwareness: string;
  jobInfoChannels: string[];
  healthEnergyStatus: string;
  exerciseFrequency?: string;
  careerConfusions: string[];
  mainConfusionText?: string;
};
