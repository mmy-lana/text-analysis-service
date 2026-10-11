<script lang="ts">
  import { PaperCard, StatusBadge } from '#lib/components/ui/index.ts';
  import type { CompleteAnalysisResponse } from '@repo/shared-types';

  interface Props {
    data: { documentId: string; document: CompleteAnalysisResponse | null };
  }

  let { data }: Props = $props();
</script>

{#if data.document}
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <PaperCard title={data.document.title} caption="Archived Manuscript">
      <p class="font-serif text-base leading-relaxed text-ink-950 whitespace-pre-wrap">
        {data.document.statistics.characterCount} characters · {data.document.statistics.wordCount} words ·
        {data.document.statistics.sentenceCount} sentences
      </p>
    </PaperCard>
    <PaperCard title="Stored Evaluation" caption="Persisted Metrics">
      <div class="flex flex-col gap-3 font-mono text-xs text-ink-700">
        <div class="flex items-center justify-between">
          <span>SENTIMENT</span>
          <StatusBadge variant="neutral">{data.document.sentiment.classification.replaceAll('_', ' ')}</StatusBadge>
        </div>
        <div class="flex items-center justify-between">
          <span>CEFR</span>
          <StatusBadge variant="accent">{data.document.readability.cefrEquivalent}</StatusBadge>
        </div>
        <div class="flex justify-between border-b border-paper-200 py-1">
          <span>READING EASE</span>
          <span>{data.document.readability.fleschReadingEase}</span>
        </div>
        <div class="flex justify-between border-b border-paper-200 py-1">
          <span>POLARITY</span>
          <span>{data.document.sentiment.polarity}</span>
        </div>
      </div>
    </PaperCard>
  </div>
{:else}
  <PaperCard title="Document Unavailable" caption="Fetch Failed">
    <p class="font-serif text-sm text-ink-500 italic">
      This archived manuscript could not be retrieved. It may have been deleted or is
      unreachable while offline.
    </p>
  </PaperCard>
{/if}
