import type {
  ProblemDetails,
  SentimentAnalysisResult,
  ReadabilityAnalysisResult
} from '@repo/shared-types';
import { endpoints } from './endpoints';

export class ApiError extends Error {
  readonly status: number;
  readonly problem: ProblemDetails | null;

  constructor(status: number, problem: ProblemDetails | null) {
    super(problem?.detail || `API request failed with status ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.problem = problem;
  }
}

export interface RequestOptions {
  signal?: AbortSignal;
}

async function postJson<TResponse>(
  url: string,
  body: unknown,
  options: RequestOptions = {}
): Promise<TResponse> {
  let response: Response;
  try {
    response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: options.signal
    });
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err;
    throw new ApiError(0, {
      type: 'about:blank',
      title: 'Network Unreachable',
      status: 0,
      detail: 'The analysis service could not be reached. Check your connection.'
    });
  }

  if (!response.ok) {
    const problem = (await response.json().catch(() => null)) as ProblemDetails | null;
    throw new ApiError(response.status, problem);
  }
  return (await response.json()) as TResponse;
}

export interface AnalysisClient {
  analyzeSentiment(text: string, options?: RequestOptions): Promise<SentimentAnalysisResult>;
  analyzeReadability(text: string, options?: RequestOptions): Promise<ReadabilityAnalysisResult>;
}

export const api: AnalysisClient = {
  analyzeSentiment: (text, options) =>
    postJson<SentimentAnalysisResult>(endpoints.sentimentAnalyze, { text }, options),
  analyzeReadability: (text, options) =>
    postJson<ReadabilityAnalysisResult>(endpoints.readabilityAnalyze, { text }, options)
};
