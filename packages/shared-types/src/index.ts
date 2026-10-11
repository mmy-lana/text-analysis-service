export type SentimentCategory =
  | 'strongly_negative'
  | 'negative'
  | 'neutral'
  | 'positive'
  | 'strongly_positive';

export type CEFRLevel = 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2';

export interface ApiErrorDetail {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  errors?: ApiErrorDetail[];
}

export interface EmotionSpectrum {
  joy: number;
  sadness: number;
  anger: number;
  fear: number;
  trust: number;
  surprise: number;
  disgust: number;
  anticipation: number;
}

export interface SentimentAnalysisResult {
  polarity: number;
  subjectivity: number;
  classification: SentimentCategory;
  positivityScore: number;
  negativityScore: number;
  neutralityScore: number;
  compoundScore: number;
  emotions: EmotionSpectrum;
}

export interface SentenceComplexity {
  index: number;
  text: string;
  wordCount: number;
  syllableCount: number;
  characterCount: number;
  complexWordCount: number;
  readingEase: number;
  isExtremelyLong: boolean;
}

export interface ReadabilityAnalysisResult {
  fleschReadingEase: number;
  fleschKincaidGrade: number;
  gunningFogIndex: number;
  colemanLiauIndex: number;
  smogIndex: number;
  automatedReadabilityIndex: number;
  readingTimeSeconds: number;
  speakingTimeSeconds: number;
  syllableCount: number;
  complexWordCount: number;
  gradeLevelConsensus: string;
  cefrEquivalent: CEFRLevel;
  sentenceBreakdown: SentenceComplexity[];
}

export interface DocumentTextStatistics {
  characterCount: number;
  wordCount: number;
  sentenceCount: number;
  paragraphCount: number;
}

export interface CompleteAnalysisRequest {
  title?: string;
  text: string;
  storeResult?: boolean;
}

export interface CompleteAnalysisResponse {
  documentId?: string;
  title: string;
  statistics: DocumentTextStatistics;
  sentiment: SentimentAnalysisResult;
  readability: ReadabilityAnalysisResult;
  processedAt: string;
}

export interface HistoryItemSummary {
  id: string;
  title: string;
  wordCount: number;
  sentimentClassification: SentimentCategory;
  cefrEquivalent: CEFRLevel;
  createdAt: string;
}

export interface PaginatedHistoryResponse {
  items: HistoryItemSummary[];
  total: number;
  page: number;
  pageSize: number;
}
