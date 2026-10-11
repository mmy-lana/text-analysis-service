<script lang="ts">
  import { PaperCard, EditorialButton, StatusBadge } from '#lib/components/ui/index.ts';
  import { historyRepository } from '#lib/stores/historyStore.svelte.ts';
  import type { HistoryFetchResult } from '#lib/stores/historyStore.svelte.ts';
  import type { HistoryItemSummary } from '@repo/shared-types';

  interface Props {
    data: { archive: HistoryFetchResult };
  }

  let { data }: Props = $props();

  let archive = $derived(data.archive);
  let searchInput = $state('');
  let deletingId = $state<string | null>(null);

  const classificationVariant = (classification: string) =>
    classification.startsWith('strongly_positive') || classification === 'positive'
      ? 'positive'
      : classification === 'negative' || classification.startsWith('strongly_negative')
        ? 'negative'
        : 'neutral';

  async function refresh(page = archive.response.page, search = searchInput) {
    const next = await historyRepository.list({ page, pageSize: archive.response.pageSize, search });
    data.archive = next;
    archive = next;
  }

  async function runSearch() {
    await refresh(1, searchInput);
  }

  async function removeItem(item: HistoryItemSummary) {
    deletingId = item.id;
    await historyRepository.remove(item.id);
    await refresh(archive.response.page);
    deletingId = null;
  }

  function formatDate(iso: string): string {
    return new Date(iso).toLocaleString();
  }
</script>

<div class="flex flex-col gap-6">
  <PaperCard
    title="Historical Archive"
    caption={archive.offline ? 'Offline Mirror (IndexedDB)' : 'Persistent Turso Archive'}
  >
    <form
      class="flex flex-col sm:flex-row gap-3 mb-6"
      onsubmit={(e) => {
        e.preventDefault();
        void runSearch();
      }}
    >
      <input
        type="search"
        bind:value={searchInput}
        placeholder="Search archived manuscripts by keyword..."
        aria-label="Search archive"
        class="min-h-[44px] flex-1 border border-paper-300 bg-paper-50 px-3 font-serif text-base text-ink-950 placeholder-ink-500 outline-none"
      />
      <EditorialButton variant="secondary" type="submit">Search</EditorialButton>
    </form>

    {#if archive.offline}
      <div class="mb-4">
        <StatusBadge variant="warning">Offline — Cached Copy</StatusBadge>
      </div>
    {/if}

    {#if archive.response.items.length === 0}
      <p class="font-serif text-sm text-ink-500 italic">
        No archived manuscripts found for this view.
      </p>
    {:else}
      <div class="overflow-x-auto">
        <table class="w-full border-collapse font-serif text-sm">
          <thead>
            <tr class="border-b border-paper-300 font-mono text-[11px] uppercase tracking-wider text-ink-500 text-left">
              <th class="py-2 pr-3">Title</th>
              <th class="py-2 pr-3">Words</th>
              <th class="py-2 pr-3">Sentiment</th>
              <th class="py-2 pr-3">CEFR</th>
              <th class="py-2 pr-3">Archived</th>
              <th class="py-2"><span class="sr-only">Actions</span></th>
            </tr>
          </thead>
          <tbody>
            {#each archive.response.items as item (item.id)}
              <tr class="border-b border-paper-200 text-ink-900">
                <td class="py-3 pr-3">
                  <a
                    href={`/${item.id}`}
                    class="underline decoration-paper-400 underline-offset-4 hover:decoration-ink-950"
                  >
                    {item.title}
                  </a>
                </td>
                <td class="py-3 pr-3 font-mono text-xs">{item.wordCount}</td>
                <td class="py-3 pr-3">
                  <StatusBadge variant={classificationVariant(item.sentimentClassification)}>
                    {item.sentimentClassification.replaceAll('_', ' ')}
                  </StatusBadge>
                </td>
                <td class="py-3 pr-3 font-mono text-xs">{item.cefrEquivalent}</td>
                <td class="py-3 pr-3 font-mono text-xs text-ink-500">{formatDate(item.createdAt)}</td>
                <td class="py-3">
                  <EditorialButton
                    variant="danger"
                    disabled={deletingId === item.id}
                    onclick={() => void removeItem(item)}
                  >
                    {deletingId === item.id ? '...' : 'Delete'}
                  </EditorialButton>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      <nav class="mt-6 flex items-center justify-between gap-3" aria-label="Archive pagination">
        <EditorialButton
          variant="secondary"
          disabled={archive.response.page <= 1}
          onclick={() => void refresh(archive.response.page - 1)}
        >
          Previous
        </EditorialButton>
        <span class="font-mono text-xs text-ink-500">
          Page {archive.response.page} · {archive.response.total} total
        </span>
        <EditorialButton
          variant="secondary"
          disabled={archive.response.page * archive.response.pageSize >= archive.response.total}
          onclick={() => void refresh(archive.response.page + 1)}
        >
          Next
        </EditorialButton>
      </nav>
    {/if}
  </PaperCard>
</div>
