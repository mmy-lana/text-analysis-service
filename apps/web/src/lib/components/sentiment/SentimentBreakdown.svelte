<script lang="ts">
  import type { SentimentAnalysisResult, SentimentCategory } from '@repo/shared-types';
  import { MetricGauge, StatusBadge } from '$lib/components/ui/index.ts';

  interface Props {
    result: SentimentAnalysisResult;
  }

  let { result }: Props = $props();

  const classificationVariant: Record<SentimentCategory, 'positive' | 'warning' | 'negative' | 'neutral' | 'accent'> = {
    strongly_positive: 'positive',
    positive: 'positive',
    neutral: 'neutral',
    negative: 'warning',
    strongly_negative: 'negative'
  };
</script>

<div class="flex flex-col gap-4">
  <div class="flex items-center justify-between">
    <span class="font-mono text-xs uppercase text-ink-500">Classification</span>
    <StatusBadge variant={classificationVariant[result.classification]}>
      {result.classification.replaceAll('_', ' ')}
    </StatusBadge>
  </div>

  <MetricGauge
    label="Polarity Index"
    value={result.polarity}
    min={-1}
    max={1}
    interpretation="Normalized compound valence metric"
  />
  <MetricGauge
    label="Subjectivity Ratio"
    value={result.subjectivity * 100}
    min={0}
    max={100}
    unit="%"
    interpretation="Ratio of opinionated to objective terms"
  />
  <div class="grid grid-cols-2 gap-3">
    <MetricGauge
      label="Positivity"
      value={result.positivityScore * 100}
      min={0}
      max={100}
      unit="%"
    />
    <MetricGauge
      label="Negativity"
      value={result.negativityScore * 100}
      min={0}
      max={100}
      unit="%"
    />
  </div>
</div>
