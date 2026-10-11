<script lang="ts">
  interface MetricGaugeProps {
    label: string;
    value: number;
    min?: number;
    max?: number;
    unit?: string;
    interpretation?: string;
  }

  let {
    label,
    value,
    min = 0,
    max = 100,
    unit = '',
    interpretation = ''
  }: MetricGaugeProps = $props();

  let percentage = $derived(
    Math.min(Math.max(((value - min) / (max - min)) * 100, 0), 100)
  );
</script>

<div class="border border-paper-300 bg-paper-50 p-4">
  <div class="flex items-baseline justify-between mb-2">
    <span class="font-mono text-xs uppercase tracking-wider text-ink-500">{label}</span>
    <span class="font-serif text-2xl font-medium text-ink-950">
      {value.toFixed(1)}{unit}
    </span>
  </div>
  <div class="relative h-2 w-full bg-paper-200 overflow-hidden border border-paper-300">
    <div
      class="h-full bg-ink-950 transition-all duration-300 ease-out"
      style="width: {percentage}%"
    ></div>
  </div>
  {#if interpretation}
    <p class="mt-2 font-mono text-[11px] text-ink-700 tracking-tight">{interpretation}</p>
  {/if}
</div>
