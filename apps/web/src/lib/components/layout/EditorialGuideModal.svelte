<script lang="ts">
  interface Props {
    open: boolean;
    onclose: () => void;
  }

  let { open, onclose }: Props = $props();

  const metrics = [
    {
      name: 'Flesch Reading Ease',
      range: '0-100',
      meaning:
        'Textual accessibility on a 0-100 scale. Higher scores read easier: 90+ is very easy (5th grade), 60-69 is standard prose (8th-9th grade), and below 30 is graduate-level difficulty.'
    },
    {
      name: 'CEFR Grade Consensus',
      range: 'A1-C2',
      meaning:
        'The Common European Framework equivalent of the consensus grade level, from A1 (beginner) to C2 (mastery). Derived from the Flesch-Kincaid grade.'
    },
    {
      name: 'Gunning Fog Index',
      range: 'Years',
      meaning:
        'Formal education years a reader needs to comprehend a passage on first reading. It weights complex words (three or more syllables) heavily.'
    },
    {
      name: 'Polarity Compound Score',
      range: '-1.0 to +1.0',
      meaning:
        'Normalized emotional valence. Negative values trend critical or sorrowful, values near zero are neutral or mixed, and positive values trend favorable.'
    },
    {
      name: 'Plutchik Emotion Radar',
      range: '8 vectors',
      meaning:
        'An eight-axis radar of joy, trust, anticipation, surprise, sadness, anger, fear, and disgust. Stronger axes push the cobalt polygon toward that rim.'
    }
  ];

  const friction = [
    {
      tone: 'Clear',
      note: 'Unmarked prose reads at a comfortable ease with no structural flags.',
      swatch: 'bg-paper-100 border-paper-300'
    },
    {
      tone: 'Dense',
      note: 'Amber-marked sentences fall below a 50 reading ease; consider splitting them.',
      swatch: 'bg-amber-surface border-amber-border'
    },
    {
      tone: 'Overlong',
      note: 'Vermilion-marked sentences run 30 or more words and strain the reader.',
      swatch: 'bg-vermilion-surface border-vermilion-border'
    }
  ];

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape' && open) {
      onclose();
    }
  }

  function handleBackdropClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      onclose();
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
  <div
    class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-ink-950/40 p-0 sm:p-6"
    onclick={handleBackdropClick}
    role="presentation"
  >
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Editorial Reader's Field Guide"
      class="max-h-[92vh] w-full sm:max-w-2xl overflow-y-auto border border-paper-300 bg-paper-100 p-5 sm:p-8 shadow-2xl"
    >
      <div class="flex items-start justify-between gap-4 mb-5">
        <div>
          <h2 class="font-serif text-2xl text-ink-950">Reader's Field Guide</h2>
          <p class="font-mono text-xs uppercase tracking-widest text-ink-500 mt-1">
            The Manuscript Review · Editorial Desk Reference
          </p>
        </div>
        <button
          type="button"
          onclick={onclose}
          aria-label="Close field guide"
          class="min-h-[44px] min-w-[44px] inline-flex items-center justify-center border border-paper-300 bg-paper-50 font-mono text-sm text-ink-800"
        >
          X
        </button>
      </div>

      <section class="mb-6">
        <h3 class="font-mono text-xs uppercase tracking-wider text-ink-500 border-b border-paper-200 pb-2 mb-3">
          Purpose
        </h3>
        <p class="font-serif text-base leading-relaxed text-ink-900">
          This desk evaluates manuscripts for linguistic friction and emotional valence.
          The workbench measures how hard a passage is to read and which emotions its
          word choices evoke; the archive keeps every graded dispatch for later review.
        </p>
      </section>

      <section class="mb-6">
        <h3 class="font-mono text-xs uppercase tracking-wider text-ink-500 border-b border-paper-200 pb-2 mb-3">
          Navigating the Desk
        </h3>
        <ul class="flex flex-col gap-2 font-serif text-base text-ink-900 list-disc pl-5">
          <li>
            <strong class="text-ink-950">Workbench:</strong> compose or paste text, choose a
            mode tab (Sentiment, Readability, or Full Dispatch), then press Run Analysis.
          </li>
          <li>
            <strong class="text-ink-950">Archive:</strong> search previously analyzed
            manuscripts by keyword, page through results, and delete superseded entries.
          </li>
          <li>
            <strong class="text-ink-950">Offline synchronization:</strong> when the service
            is unreachable, the archive falls back to a local IndexedDB mirror and a badge
            marks the cached copy until the connection returns.
          </li>
        </ul>
      </section>

      <section class="mb-6">
        <h3 class="font-mono text-xs uppercase tracking-wider text-ink-500 border-b border-paper-200 pb-2 mb-3">
          Metrics Interpretation
        </h3>
        <dl class="flex flex-col gap-3">
          {#each metrics as metric (metric.name)}
            <div class="border border-paper-300 bg-paper-50 p-3">
              <dt class="flex items-baseline justify-between gap-3 flex-wrap">
                <span class="font-serif text-base text-ink-950">{metric.name}</span>
                <span class="font-mono text-[11px] uppercase text-ink-500">{metric.range}</span>
              </dt>
              <dd class="mt-1 font-serif text-sm leading-relaxed text-ink-700">
                {metric.meaning}
              </dd>
            </div>
          {/each}
        </dl>
      </section>

      <section>
        <h3 class="font-mono text-xs uppercase tracking-wider text-ink-500 border-b border-paper-200 pb-2 mb-3">
          Friction Markers
        </h3>
        <ul class="flex flex-col gap-2">
          {#each friction as marker (marker.tone)}
            <li class="flex items-start gap-3">
              <span class="mt-1 inline-block h-4 w-4 border {marker.swatch} flex-shrink-0"></span>
              <span class="font-serif text-sm text-ink-700">
                <strong class="text-ink-950">{marker.tone}:</strong> {marker.note}
              </span>
            </li>
          {/each}
        </ul>
      </section>
    </div>
  </div>
{/if}
