import { historyRepository } from '$lib/stores/historyStore.svelte.ts';
import type { HistoryFetchResult } from '$lib/stores/historyStore.svelte.ts';

export const load = async ({ url }: { url: URL }): Promise<{ archive: HistoryFetchResult }> => {
  const page = Math.max(1, Number(url.searchParams.get('page') ?? '1') || 1);
  const search = url.searchParams.get('q') ?? '';
  const archive = await historyRepository.list({ page, pageSize: 20, search });
  return { archive };
};

export type PageData = Awaited<ReturnType<typeof load>>;
