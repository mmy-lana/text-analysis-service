<script lang="ts">
  import type { EmotionSpectrum } from '@repo/shared-types';

  interface Props {
    emotions: EmotionSpectrum;
  }

  let { emotions }: Props = $props();

  const axes: { key: keyof EmotionSpectrum; label: string }[] = [
    { key: 'joy', label: 'Joy' },
    { key: 'trust', label: 'Trust' },
    { key: 'anticipation', label: 'Anticipation' },
    { key: 'surprise', label: 'Surprise' },
    { key: 'sadness', label: 'Sadness' },
    { key: 'anger', label: 'Anger' },
    { key: 'fear', label: 'Fear' },
    { key: 'disgust', label: 'Disgust' }
  ];

  // Pure-SVG radar spectrum: 8 axes on a 200x200 viewport, radius 80.
  const CENTER = 100;
  const RADIUS = 80;
  const RINGS = [0.25, 0.5, 0.75, 1.0];

  function axisPoint(index: number, ratio: number): { x: number; y: number } {
    const angle = (Math.PI * 2 * index) / axes.length - Math.PI / 2;
    return {
      x: CENTER + Math.cos(angle) * RADIUS * ratio,
      y: CENTER + Math.sin(angle) * RADIUS * ratio
    };
  }

  const chart = $derived(
    axes.map((axis, index) => {
      const ratio = Math.max(emotions[axis.key], 0.02);
      return {
        key: axis.key,
        label: axis.label,
        value: emotions[axis.key],
        point: axisPoint(index, ratio),
        vertex: axisPoint(index, 1)
      };
    })
  );

  const polygonPoints = $derived(
    chart.map((axis) => `${axis.point.x.toFixed(2)},${axis.point.y.toFixed(2)}`).join(' ')
  );

  const ringPolygons = $derived(
    RINGS.map((ring) =>
      axes
        .map((_, index) => {
          const p = axisPoint(index, ring);
          return `${p.x.toFixed(2)},${p.y.toFixed(2)}`;
        })
        .join(' ')
    )
  );
</script>

<div class="flex flex-col items-center gap-4">
  <svg
    viewBox="0 0 200 200"
    class="w-full max-w-[280px]"
    role="img"
    aria-label="Plutchik emotion spectrum radar chart"
  >
    {#each ringPolygons as ring, i (i)}
      <polygon points={ring} fill="none" stroke="var(--color-paper-300)" stroke-width="0.75" />
    {/each}

    {#each chart as axis (axis.key)}
      <line
        x1={CENTER}
        y1={CENTER}
        x2={axis.vertex.x}
        y2={axis.vertex.y}
        stroke="var(--color-paper-300)"
        stroke-width="0.75"
      />
    {/each}

    <polygon
      points={polygonPoints}
      fill="rgba(32, 69, 105, 0.25)"
      stroke="var(--color-cobalt-base)"
      stroke-width="1.5"
    />

    {#each chart as axis (axis.key)}
      <circle cx={axis.point.x} cy={axis.point.y} r="2" fill="var(--color-cobalt-base)" />
      <text
        x={axis.vertex.x * 1.14 - CENTER * 0.14 + CENTER}
        y={axis.vertex.y * 1.14 - CENTER * 0.14 + CENTER}
        text-anchor="middle"
        dominant-baseline="middle"
        font-family="var(--font-mono)"
        font-size="7.5"
        fill="var(--color-ink-700)"
      >
        {axis.label}
      </text>
    {/each}
  </svg>

  <dl class="grid w-full grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-4">
    {#each chart as axis (axis.key)}
      <div class="flex items-baseline justify-between gap-2 border-b border-paper-200 py-1">
        <dt class="font-mono text-[11px] uppercase tracking-wider text-ink-500">
          {axis.label}
        </dt>
        <dd class="font-mono text-[11px] text-ink-900">
          {(axis.value * 100).toFixed(0)}%
        </dd>
      </div>
    {/each}
  </dl>
</div>
