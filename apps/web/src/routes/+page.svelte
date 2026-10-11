<script lang="ts">
  import { PaperCard, EditorialTextarea, EditorialButton } from '#lib/components/ui/index.ts';
  import SentimentBreakdown from '#lib/components/sentiment/SentimentBreakdown.svelte';
  import EmotionSpectrum from '#lib/components/sentiment/EmotionSpectrum.svelte';
  import GradeBandCard from '#lib/components/readability/GradeBandCard.svelte';
  import MetricGrid from '#lib/components/readability/MetricGrid.svelte';
  import SentenceHighlighter from '#lib/components/readability/SentenceHighlighter.svelte';
  import { analysisStore } from '#lib/stores/analysisStore.svelte.ts';
  import EditorialGuideModal from '#lib/components/layout/EditorialGuideModal.svelte';
  import type { AnalysisMode } from '#lib/types/index.ts';

  const store = analysisStore;

  let mode = $state<AnalysisMode>('both');
  let guideOpen = $state(false);

  const modes: { key: AnalysisMode; label: string }[] = [
    { key: 'sentiment', label: 'Sentiment' },
    { key: 'readability', label: 'Readability' },
    { key: 'both', label: 'Full Dispatch' }
  ];

  const showSentiment = $derived(mode !== 'readability');
  const showReadability = $derived(mode !== 'sentiment');
</script>

<div class="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8">
  <div class="lg:col-span-7 flex flex-col gap-6">
    <PaperCard title="Composition Pane" caption="Enter copy for grammatical and emotional grading">
      <div class="flex flex-col gap-4">
        <EditorialTextarea
          value={store.state.text}
          oninput={(val) => store.setText(val)}
          rows={14}
        />
        <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div class="flex flex-col sm:flex-row gap-3 flex-1">
            <EditorialButton
              variant="primary"
              onclick={() => void store.runAnalysis()}
              disabled={store.isAnalyzing || !store.state.text.trim()}
            >
              {store.isAnalyzing ? 'Evaluating Text...' : 'Run Analysis'}
            </EditorialButton>
            <EditorialButton variant="secondary" onclick={() => (guideOpen = true)}>
              Field Guide
            </EditorialButton>
          </div>
          {#if store.state.error}
            <span class="font-mono text-xs text-vermilion-base">{store.state.error}</span>
          {/if}
        </div>
      </div>
    </PaperCard>

    {#if store.state.readability}
      <SentenceHighlighter
        text={store.state.text}
        sentences={store.state.readability.sentenceBreakdown}
      />
    {/if}
  </div>

  <div class="lg:col-span-5 flex flex-col gap-6">
    <div
      class="grid grid-cols-3 gap-2"
      role="tablist"
      aria-label="Analysis mode"
    >
      {#each modes as m (m.key)}
        <button
          type="button"
          role="tab"
          aria-selected={mode === m.key}
          onclick={() => (mode = m.key)}
          class="min-h-[44px] px-3 font-mono text-xs uppercase tracking-wider border transition-colors
            {mode === m.key
              ? 'bg-ink-950 text-paper-50 border-ink-950'
              : 'bg-paper-100 text-ink-800 border-paper-300'}"
        >
          {m.label}
        </button>
      {/each}
    </div>

    {#if showSentiment && store.state.sentiment}
      <PaperCard title="Sentiment Evaluation" caption="Lexical Valence & Intensity">
        <SentimentBreakdown result={store.state.sentiment} />
      </PaperCard>
      <PaperCard title="Emotion Spectrum" caption="Plutchik Eight-Vector Profile">
        <EmotionSpectrum emotions={store.state.sentiment.emotions} />
      </PaperCard>
    {/if}

    {#if showReadability && store.state.readability}
      <PaperCard title="Readability Standard" caption="Algorithmic Index Consensus">
        <GradeBandCard
          gradeLevel={store.state.readability.gradeLevelConsensus}
          cefr={store.state.readability.cefrEquivalent}
          readingEase={store.state.readability.fleschReadingEase}
          fleschKincaid={store.state.readability.fleschKincaidGrade}
        />
      </PaperCard>
      <PaperCard title="Metric Grid" caption="Six-Index Diagnostics">
        <MetricGrid result={store.state.readability} />
      </PaperCard>
    {/if}

    {#if !store.state.sentiment && !store.state.readability}
      <PaperCard title="Diagnostic Console" caption="Awaiting Text Dispatch">
        <p class="font-serif text-sm text-ink-500 italic">
          Press 'Run Analysis' to stream readability metrics and emotional polarity breakdown.
        </p>
      </PaperCard>
    {/if}
  </div>
</div>

<EditorialGuideModal open={guideOpen} onclose={() => (guideOpen = false)} />
