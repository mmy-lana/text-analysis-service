import type {
  ReadabilityAnalysisResult,
  SentimentAnalysisResult
} from '@repo/shared-types';
import { api, ApiError } from '$lib/api/client';

export type AnalysisStatus = 'idle' | 'analyzing' | 'success' | 'error';

export interface AnalysisState {
  status: AnalysisStatus;
  text: string;
  sentiment: SentimentAnalysisResult | null;
  readability: ReadabilityAnalysisResult | null;
  error: string | null;
}

function initialState(): AnalysisState {
  return {
    status: 'idle',
    text: '',
    sentiment: null,
    readability: null,
    error: null
  };
}

/** Svelte 5 runes store encapsulating the analysis workbench state. */
class AnalysisStore {
  state = $state<AnalysisState>(initialState());

  get isAnalyzing(): boolean {
    return this.state.status === 'analyzing';
  }

  setText(text: string): void {
    this.state.text = text;
  }

  reset(): void {
    this.state = initialState();
  }

  async runAnalysis(text?: string): Promise<boolean> {
    const manuscript = (text ?? this.state.text).trim();
    if (!manuscript || this.isAnalyzing) return false;

    this.state.status = 'analyzing';
    this.state.error = null;

    try {
      const [sentiment, readability] = await Promise.all([
        api.analyzeSentiment(manuscript),
        api.analyzeReadability(manuscript)
      ]);
      this.state.sentiment = sentiment;
      this.state.readability = readability;
      this.state.status = 'success';
      return true;
    } catch (err: unknown) {
      this.state.error =
        err instanceof ApiError
          ? err.message
          : 'Analysis failed for an unexpected reason.';
      this.state.status = 'error';
      return false;
    }
  }
}

export const analysisStore = new AnalysisStore();
