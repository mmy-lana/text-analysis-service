// Central endpoint registry for the FastAPI v1 surface.

export const API_BASE_URL: string =
  import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const endpoints = {
  sentimentAnalyze: `${API_BASE_URL}/api/v1/sentiment/analyze`,
  sentimentBatch: `${API_BASE_URL}/api/v1/sentiment/batch`,
  readabilityAnalyze: `${API_BASE_URL}/api/v1/readability/analyze`,
  readabilityBatch: `${API_BASE_URL}/api/v1/readability/batch`,
  history: `${API_BASE_URL}/api/v1/history`,
  historyItem: (documentId: string) => `${API_BASE_URL}/api/v1/history/${documentId}`
} as const;
