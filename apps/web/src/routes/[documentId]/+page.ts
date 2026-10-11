import { historyRepository } from '$lib/stores/historyStore.svelte.ts';
import type { CompleteAnalysisResponse } from '@repo/shared-types';

export const load = async ({
  params
}: {
  params: { documentId: string };
}): Promise<{ documentId: string; document: CompleteAnalysisResponse | null }> => {
  const document = await historyRepository.fetchDocument(params.documentId);
  return { documentId: params.documentId, document };
};
