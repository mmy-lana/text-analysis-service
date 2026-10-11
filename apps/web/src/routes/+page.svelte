<script lang="ts">
  import EditorialButton from '$lib/components/ui/EditorialButton.svelte';
  import EditorialTextarea from '$lib/components/ui/EditorialTextarea.svelte';
  import PaperCard from '$lib/components/ui/PaperCard.svelte';
  import MetricGauge from '$lib/components/ui/MetricGauge.svelte';
  import StatusBadge from '$lib/components/ui/StatusBadge.svelte';
  import type { SentimentAnalysisResult, ReadabilityAnalysisResult } from '@repo/shared-types';

  let manuscript = $state('The clarity of the prose allows the argument to emerge with remarkable force. It is an impressive piece of scholarly writing that remains entirely accessible to the general reader.');
  let isAnalyzing = $state(false);
  let sentimentResult = $state<SentimentAnalysisResult | null>(null);
  let readabilityResult = $state<ReadabilityAnalysisResult | null>(null);
  let errorMessage = $state<string | null>(null);

  async function evaluateText() {
    if (!manuscript.trim()) return;
    isAnalyzing = true;
    errorMessage = null;

    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const [sentRes, readRes] = await Promise.all([
        fetch(`${baseUrl}/api/v1/sentiment/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: manuscript })
        }),
        fetch(`${baseUrl}/api/v1/readability/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: manuscript })
        })
      ]);

      if (!sentRes.ok || !readRes.ok) {
        throw new Error('Analysis service reported an unprocessable response.');
      }

      sentimentResult = await sentRes.json();
      readabilityResult = await readRes.json();
    } catch (err: unknown) {
      errorMessage = err instanceof Error ? err.message : 'Analysis failed';
    } finally {
      isAnalyzing = false;
    }
  }
</script>

<div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
  <div class="lg:col-span-7 flex flex-col gap-6">
    <PaperCard title="Composition Pane" caption="Enter copy for grammatical and emotional grading">
      <div class="flex flex-col gap-4">
        <EditorialTextarea
          value={manuscript}
          oninput={(val) => { manuscript = val; }}
          rows={14}
        />
        <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <EditorialButton
            variant="primary"
            onclick={evaluateText}
            disabled={isAnalyzing || !manuscript.trim()}
          >
            {isAnalyzing ? 'Evaluating Text...' : 'Run Analysis'}
          </EditorialButton>
          {#if errorMessage}
            <span class="font-mono text-xs text-vermilion-base">{errorMessage}</span>
          {/if}
        </div>
      </div>
    </PaperCard>
  </div>

  <div class="lg:col-span-5 flex flex-col gap-6">
    {#if sentimentResult}
      <PaperCard title="Sentiment Evaluation" caption="Lexical Valence & Intensity">
        <div class="flex flex-col gap-4">
          <div class="flex items-center justify-between">
            <span class="font-mono text-xs uppercase text-ink-500">Classification</span>
            <StatusBadge variant="positive">
              {sentimentResult.classification}
            </StatusBadge>
          </div>
          <MetricGauge
            label="Polarity Index"
            value={sentimentResult.polarity}
            min={-1}
            max={1}
            interpretation="Normalized compound valence metric"
          />
          <MetricGauge
            label="Subjectivity Ratio"
            value={sentimentResult.subjectivity * 100}
            min={0}
            max={100}
            unit="%"
            interpretation="Ratio of opinionated to objective terms"
          />
        </div>
      </PaperCard>
    {/if}

    {#if readabilityResult}
      <PaperCard title="Readability Standard" caption="Algorithmic Index Consensus">
        <div class="flex flex-col gap-4">
          <div class="flex items-center justify-between">
            <span class="font-mono text-xs uppercase text-ink-500">CEFR Assessment</span>
            <StatusBadge variant="accent">
              {readabilityResult.cefrEquivalent}
            </StatusBadge>
          </div>
          <MetricGauge
            label="Flesch Reading Ease"
            value={readabilityResult.fleschReadingEase}
            min={0}
            max={100}
            interpretation={readabilityResult.gradeLevelConsensus}
          />
          <MetricGauge
            label="Gunning Fog Index"
            value={readabilityResult.gunningFogIndex}
            min={0}
            max={20}
            interpretation="Years of formal education required"
          />
        </div>
      </PaperCard>
    {/if}

    {#if !sentimentResult && !readabilityResult}
      <PaperCard title="Diagnostic Console" caption="Awaiting Text Dispatch">
        <p class="font-serif text-sm text-ink-500 italic">
          Press 'Run Analysis' to stream readability metrics and emotional polarity breakdown.
        </p>
      </PaperCard>
    {/if}
  </div>
</div>
