// Central endpoint registry for the FastAPI v1 surface.
// Resolves the public API base from SvelteKit's canonical PUBLIC_*
// environment namespace; the Vite dev proxy handles same-origin /api
// requests when PUBLIC_API_BASE_URL is unset.
export const API_BASE_URL: string =
  import.meta.env.PUBLIC_API_BASE_URL || 'http://localhost:8005';

export const endpoints = {
  sentimentAnalyze: `${API_BASE_URL}/api/v1/sentiment/analyze`,
  sentimentBatch: `${API_BASE_URL}/api/v1/sentiment/batch`,
  readabilityAnalyze: `${API_BASE_URL}/api/v1/readability/analyze`,
  readabilityBatch: `${API_BASE_URL}/api/v1/readability/batch`,
  history: `${API_BASE_URL}/api/v1/history`,
  historyItem: (documentId: string) => `${API_BASE_URL}/api/v1/history/${documentId}`
} as const;

export const SESSION_STORAGE_KEY = 'tas-session-id';

// Anonymous multitenancy identity (SEC-01): a client-generated UUID bound to
// every archive request via the X-Session-ID header.
export function getSessionId(): string {
  if (typeof localStorage === 'undefined') return '';
  let sessionId = localStorage.getItem(SESSION_STORAGE_KEY);
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  }
  return sessionId;
}

export function identityHeaders(): Record<string, string> {
  const sessionId = getSessionId();
  return sessionId ? { 'X-Session-ID': sessionId } : {};
}
