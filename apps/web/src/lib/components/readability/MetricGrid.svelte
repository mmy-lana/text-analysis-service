<script lang="ts">
  import type { ReadabilityAnalysisResult } from '@repo/shared-types';
  import { MetricGauge } from '$lib/components/ui/index.ts';

  interface Props {
    result: ReadabilityAnalysisResult;
  }

  let { result }: Props = $props();

  function formatDuration(seconds: number): string {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const rest = seconds % 60;
    return rest === 0 ? `${minutes}m` : `${minutes}m ${rest}s`;
  }
</script>

<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
  <MetricGauge
    label="Flesch Reading Ease"
    value={result.fleschReadingEase}
    min={0}
    max={100}
    interpretation="Higher scores indicate easier reading"
  />
  <MetricGauge
    label="Flesch-Kincaid Grade"
    value={result.fleschKincaidGrade}
    min={0}
    max={20}
    interpretation="US school grade level equivalent"
  />
  <MetricGauge
    label="Gunning Fog Index"
    value={result.gunningFogIndex}
    min={0}
    max={20}
    interpretation="Years of formal education required"
  />
  <MetricGauge
    label="Coleman-Liau Index"
    value={result.colemanLiauIndex}
    min={0}
    max={20}
    interpretation="Character-based grade estimation"
  />
  <MetricGauge
    label="SMOG Index"
    value={result.smogIndex}
    min={0}
    max={20}
    interpretation="Polysyllable-based grade estimation"
  />
  <MetricGauge
    label="Automated Readability"
    value={result.automatedReadabilityIndex}
    min={0}
    max={20}
    interpretation="Character and word length based grade"
  />

  <div class="sm:col-span-2 grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
    <div class="border border-paper-300 bg-paper-50 p-3">
      <p class="uppercase tracking-wider text-ink-500">Reading Time</p>
      <p class="mt-1 font-serif text-lg text-ink-950">
        {formatDuration(result.readingTimeSeconds)}
      </p>
    </div>
    <div class="border border-paper-300 bg-paper-50 p-3">
      <p class="uppercase tracking-wider text-ink-500">Speaking Time</p>
      <p class="mt-1 font-serif text-lg text-ink-950">
        {formatDuration(result.speakingTimeSeconds)}
      </p>
    </div>
    <div class="border border-paper-300 bg-paper-50 p-3">
      <p class="uppercase tracking-wider text-ink-500">Syllables</p>
      <p class="mt-1 font-serif text-lg text-ink-950">{result.syllableCount}</p>
    </div>
    <div class="border border-paper-300 bg-paper-50 p-3">
      <p class="uppercase tracking-wider text-ink-500">Complex Words</p>
      <p class="mt-1 font-serif text-lg text-ink-950">{result.complexWordCount}</p>
    </div>
  </div>
</div>
