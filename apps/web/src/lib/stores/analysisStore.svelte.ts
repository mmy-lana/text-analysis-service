import type {
  ReadabilityAnalysisResult,
  SentimentAnalysisResult
} from '@repo/shared-types';
import { api, ApiError } from '#lib/api/client';

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
  #abortController: AbortController | null = null;

  get isAnalyzing(): boolean {
    return this.state.status === 'analyzing';
  }

  setText(text: string): void {
    this.state.text = text;
  }

  reset(): void {
    this.abortInFlight();
    this.state = initialState();
  }

  abortInFlight(): void {
    if (this.#abortController) {
      this.#abortController.abort();
      this.#abortController = null;
    }
  }

  async runAnalysis(text?: string): Promise<boolean> {
    const manuscript = (text ?? this.state.text).trim();
    if (!manuscript) return false;

    // UI-02: cancel any in-flight analysis so stale responses can never
    // overwrite fresh results on rapid consecutive dispatches.
    this.abortInFlight();
    const controller = new AbortController();
    this.#abortController = controller;

    this.state.status = 'analyzing';
    this.state.error = null;

    try {
      const [sentiment, readability] = await Promise.all([
        api.analyzeSentiment(manuscript, { signal: controller.signal }),
        api.analyzeReadability(manuscript, { signal: controller.signal })
      ]);
      if (controller.signal.aborted) return false;
      this.state.sentiment = sentiment;
      this.state.readability = readability;
      this.state.status = 'success';
      return true;
    } catch (err: unknown) {
      if (controller.signal.aborted || (err instanceof DOMException && err.name === 'AbortError')) {
        return false;
      }
      this.state.error =
        err instanceof ApiError
          ? err.message
          : 'Analysis failed for an unexpected reason.';
      this.state.status = 'error';
      return false;
    } finally {
      if (this.#abortController === controller) {
        this.#abortController = null;
      }
    }
  }
}

export const analysisStore = new AnalysisStore();
