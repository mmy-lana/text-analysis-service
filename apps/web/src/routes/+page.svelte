<script lang="ts">
  import { PaperCard, EditorialTextarea, EditorialButton } from '$lib/components/ui/index.ts';
  import SentimentBreakdown from '$lib/components/sentiment/SentimentBreakdown.svelte';
  import EmotionSpectrum from '$lib/components/sentiment/EmotionSpectrum.svelte';
  import { analysisStore } from '$lib/stores/analysisStore.svelte.ts';

  const store = analysisStore;
</script>

<div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
  <div class="lg:col-span-7 flex flex-col gap-6">
    <PaperCard title="Composition Pane" caption="Enter copy for grammatical and emotional grading">
      <div class="flex flex-col gap-4">
        <EditorialTextarea
          value={store.state.text}
          oninput={(val) => store.setText(val)}
          rows={14}
        />
        <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <EditorialButton
            variant="primary"
            onclick={() => void store.runAnalysis()}
            disabled={store.isAnalyzing || !store.state.text.trim()}
          >
            {store.isAnalyzing ? 'Evaluating Text...' : 'Run Analysis'}
          </EditorialButton>
          {#if store.state.error}
            <span class="font-mono text-xs text-vermilion-base">{store.state.error}</span>
          {/if}
        </div>
      </div>
    </PaperCard>
  </div>

  <div class="lg:col-span-5 flex flex-col gap-6">
    {#if store.state.sentiment}
      <PaperCard title="Sentiment Evaluation" caption="Lexical Valence & Intensity">
        <SentimentBreakdown result={store.state.sentiment} />
      </PaperCard>
    {/if}

    {#if store.state.sentiment}
      <PaperCard title="Emotion Spectrum" caption="Plutchik Eight-Vector Profile">
        <EmotionSpectrum emotions={store.state.sentiment.emotions} />
      </PaperCard>
    {/if}

    {#if store.state.readability}
      <PaperCard title="Readability Standard" caption="Algorithmic Index Consensus">
        <div class="flex flex-col gap-4">
          <div class="flex items-center justify-between">
            <span class="font-mono text-xs uppercase text-ink-500">CEFR Assessment</span>
            <span class="font-mono text-xs border border-paper-300 px-2 py-1 bg-cobalt-surface text-cobalt-base">
              {store.state.readability.cefrEquivalent}
            </span>
          </div>
          <p class="font-serif text-sm text-ink-700 italic">
            {store.state.readability.gradeLevelConsensus}
          </p>
        </div>
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
