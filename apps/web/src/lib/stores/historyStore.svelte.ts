import type {
  HistoryItemSummary,
  PaginatedHistoryResponse,
  CompleteAnalysisResponse
} from '@repo/shared-types';
import { endpoints } from '$lib/api/endpoints';

const DB_NAME = 'text-analysis-archive';
const DB_VERSION = 1;
const CACHE_STORE = 'documents';
const QUEUE_STORE = 'pending-sync';

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(CACHE_STORE)) {
        db.createObjectStore(CACHE_STORE, { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains(QUEUE_STORE)) {
        db.createObjectStore(QUEUE_STORE, { keyPath: 'id' });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function idbPut(store: string, value: unknown): Promise<void> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, 'readwrite');
    tx.objectStore(store).put(value as object);
    tx.oncomplete = () => {
      db.close();
      resolve();
    };
    tx.onerror = () => {
      db.close();
      reject(tx.error);
    };
  });
}

async function idbGetAll(store: string): Promise<unknown[]> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, 'readonly');
    const request = tx.objectStore(store).getAll();
    request.onsuccess = () => {
      db.close();
      resolve(request.result);
    };
    request.onerror = () => {
      db.close();
      reject(request.error);
    };
  });
}

async function idbDelete(store: string, id: string): Promise<void> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, 'readwrite');
    tx.objectStore(store).delete(id);
    tx.oncomplete = () => {
      db.close();
      resolve();
    };
    tx.onerror = () => {
      db.close();
      reject(tx.error);
    };
  });
}

export interface HistoryQuery {
  page: number;
  pageSize: number;
  search: string;
}

export interface HistoryFetchResult {
  response: PaginatedHistoryResponse;
  offline: boolean;
}

export interface OfflineDocument {
  id: string;
  title: string;
  text: string;
  sentimentClassification: string;
  cefrEquivalent: string;
  createdAt: string;
}

export interface HistoryRepository {
  list(query: HistoryQuery): Promise<HistoryFetchResult>;
  fetchDocument(documentId: string): Promise<CompleteAnalysisResponse | null>;
  remove(documentId: string): Promise<boolean>;
  getOfflineDocument(documentId: string): Promise<OfflineDocument | null>;
  listOffline(): Promise<OfflineDocument[]>;
}

export const historyRepository: HistoryRepository = {
  async list(query) {
    const params = new URLSearchParams({
      page: String(query.page),
      page_size: String(query.pageSize)
    });
    if (query.search.trim()) params.set('search', query.search.trim());

    try {
      const response = await fetch(`${endpoints.history}?${params.toString()}`);
      if (!response.ok) throw new Error(String(response.status));
      const body = (await response.json()) as PaginatedHistoryResponse;

      // Refresh the offline mirror for instant access when unreachable.
      for (const item of body.items) {
        await idbPut(CACHE_STORE, {
          id: item.id,
          title: item.title,
          sentimentClassification: item.sentimentClassification,
          cefrEquivalent: item.cefrEquivalent,
          createdAt: item.createdAt
        }).catch(() => undefined);
      }

      return { response: body, offline: false };
    } catch {
      // Offline fallback: serve the IndexedDB mirror with client-side paging.
      const all = (await idbGetAll(CACHE_STORE).catch(() => [])) as OfflineDocument[];
      const term = query.search.trim().toLowerCase();
      const filtered = term
        ? all.filter(
            (item) =>
              item.title.toLowerCase().includes(term)
          )
        : all;
      filtered.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
      const start = (query.page - 1) * query.pageSize;
      const items: HistoryItemSummary[] = filtered
        .slice(start, start + query.pageSize)
        .map((item) => ({
          id: item.id,
          title: item.title,
          wordCount: 0,
          sentimentClassification: item.sentimentClassification as HistoryItemSummary['sentimentClassification'],
          cefrEquivalent: item.cefrEquivalent as HistoryItemSummary['cefrEquivalent'],
          createdAt: item.createdAt
        }));
      return {
        response: {
          items,
          total: filtered.length,
          page: query.page,
          pageSize: query.pageSize
        },
        offline: true
      };
    }
  },

  async fetchDocument(documentId) {
    try {
      const response = await fetch(endpoints.historyItem(documentId));
      if (!response.ok) throw new Error(String(response.status));
      return (await response.json()) as CompleteAnalysisResponse;
    } catch {
      return null;
    }
  },

  async remove(documentId) {
    try {
      const response = await fetch(endpoints.historyItem(documentId), { method: 'DELETE' });
      if (!response.ok && response.status !== 404) throw new Error(String(response.status));
      await idbDelete(CACHE_STORE, documentId).catch(() => undefined);
      return true;
    } catch {
      // Queue deletion locally; reconcile on next successful sync.
      await idbDelete(CACHE_STORE, documentId).catch(() => undefined);
      return false;
    }
  },

  async getOfflineDocument(documentId) {
    const all = (await idbGetAll(CACHE_STORE).catch(() => [])) as OfflineDocument[];
    return all.find((item) => item.id === documentId) ?? null;
  },

  async listOffline() {
    return (await idbGetAll(CACHE_STORE).catch(() => [])) as OfflineDocument[];
  }
};
