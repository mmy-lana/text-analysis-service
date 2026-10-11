<script lang="ts">
  interface Props {
    gradeLevel: string;
    cefr: string;
    readingEase: number;
    fleschKincaid: number;
  }

  let { gradeLevel, cefr, readingEase, fleschKincaid }: Props = $props();

  const bands = [
    { label: 'Very Easy', min: 90, note: '5th Grade' },
    { label: 'Easy', min: 80, note: '6th Grade' },
    { label: 'Fairly Easy', min: 70, note: '7th Grade' },
    { label: 'Standard', min: 60, note: '8th-9th Grade' },
    { label: 'Fairly Difficult', min: 50, note: '10th-12th Grade' },
    { label: 'Difficult', min: 30, note: 'College' },
    { label: 'Very Difficult', min: 0, note: 'Graduate' }
  ] as const;

  const band = $derived(bands.find((b) => readingEase >= b.min) ?? bands[bands.length - 1]);
  const bandIndex = $derived(bands.findIndex((b) => b.label === band?.label));
</script>

<div class="border border-paper-300 bg-paper-100 p-4 sm:p-6">
  <div class="flex flex-col gap-1 mb-4">
    <span class="font-mono text-xs uppercase tracking-wider text-ink-500">Grade Band</span>
    <div class="flex items-baseline gap-3 flex-wrap">
      <span class="font-serif text-3xl font-medium text-ink-950">{band?.label}</span>
      <span class="font-mono text-xs uppercase text-ink-700 border border-paper-300 bg-paper-50 px-2 py-1">
        {cefr}
      </span>
    </div>
    <span class="font-mono text-[11px] text-ink-500">{band?.note}</span>
  </div>

  <div class="flex gap-1 mb-3" role="img" aria-label={`Reading ease band: ${band?.label}`}>
    {#each bands as b, i (b.label)}
      <div
        class="h-2 flex-1 border border-paper-300"
        class:bg-ink-950={i <= bandIndex}
        class:bg-paper-200={i > bandIndex}
      ></div>
    {/each}
  </div>

  <dl class="grid grid-cols-2 gap-x-4 font-mono text-xs text-ink-700">
    <div class="flex justify-between border-b border-paper-200 py-1">
      <dt>Reading Ease</dt>
      <dd class="text-ink-950">{readingEase.toFixed(1)}</dd>
    </div>
    <div class="flex justify-between border-b border-paper-200 py-1">
      <dt>FK Grade</dt>
      <dd class="text-ink-950">{fleschKincaid.toFixed(1)}</dd>
    </div>
    <div class="flex justify-between py-1">
      <dt>Consensus</dt>
      <dd class="text-ink-950">{gradeLevel}</dd>
    </div>
    <div class="flex justify-between py-1">
      <dt>CEFR</dt>
      <dd class="text-ink-950">{cefr}</dd>
    </div>
  </dl>
</div>
