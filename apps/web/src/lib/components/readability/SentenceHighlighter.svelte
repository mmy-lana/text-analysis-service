<script lang="ts">
  import type { SentenceComplexity } from '@repo/shared-types';

  interface Props {
    sentences: SentenceComplexity[];
    text: string;
  }

  let { sentences, text }: Props = $props();

  // Threshold under which ease is considered friction-heavy.
  const FRICTION_THRESHOLD = 50;

  let highlighted = $derived.by(() => {
    if (sentences.length === 0) return [{ text, tone: 'plain' as const }];
    const parts: { text: string; tone: 'plain' | 'hard' | 'extreme' }[] = [];
    let cursor = 0;
    for (const sentence of sentences) {
      const start = text.indexOf(sentence.text, cursor);
      if (start < 0) continue;
      if (start > cursor) {
        parts.push({ text: text.slice(cursor, start), tone: 'plain' });
      }
      parts.push({
        text: sentence.text,
        tone: sentence.isExtremelyLong ? 'extreme' : sentence.readingEase < FRICTION_THRESHOLD ? 'hard' : 'plain'
      });
      cursor = start + sentence.text.length;
    }
    if (cursor < text.length) parts.push({ text: text.slice(cursor), tone: 'plain' });
    return parts;
  });
</script>

<div class="border border-paper-300 bg-paper-100 p-4 sm:p-6">
  <div class="flex items-center justify-between mb-3 flex-wrap gap-2">
    <h3 class="font-serif text-lg text-ink-950">Sentence Friction Map</h3>
    <div class="flex items-center gap-3 font-mono text-[11px] uppercase text-ink-500">
      <span class="flex items-center gap-1">
        <span class="inline-block h-3 w-3 border border-paper-300 bg-paper-100"></span> Clear
      </span>
      <span class="flex items-center gap-1">
        <span class="inline-block h-3 w-3 border border-amber-border bg-amber-surface"></span> Dense
      </span>
      <span class="flex items-center gap-1">
        <span class="inline-block h-3 w-3 border border-vermilion-border bg-vermilion-surface"></span> Overlong
      </span>
    </div>
  </div>
  <p class="font-serif text-base sm:text-lg leading-relaxed text-ink-950 whitespace-pre-wrap">
    {#each highlighted as part, i (i)}
      {#if part.tone === 'hard'}
        <mark class="bg-amber-surface text-ink-950 border-b border-amber-border">{part.text}</mark>
      {:else if part.tone === 'extreme'}
        <mark class="bg-vermilion-surface text-ink-950 border-b border-vermilion-border">{part.text}</mark>
      {:else}
        {part.text}
      {/if}
    {/each}
  </p>
</div>
