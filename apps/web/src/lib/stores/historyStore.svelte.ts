import type {
  HistoryItemSummary,
  PaginatedHistoryResponse,
  CompleteAnalysisResponse
} from '@repo/shared-types';
import { endpoints, identityHeaders } from '#lib/api/endpoints';

const DB_NAME = 'text-analysis-archive';
const DB_VERSION = 1;
const CACHE_STORE = 'documents';
const QUEUE_STORE = 'pending-sync';

export interface OfflineDocument {
  id: string;
  title: string;
  wordCount: number;
  characterCount: number;
  sentenceCount: number;
  paragraphCount: number;
  sentimentClassification: string;
  cefrEquivalent: string;
  createdAt: string;
}

let dbPromise: Promise<IDBDatabase> | null = null;

/** DATA-02: one shared connection promise instead of open/close per write. */
function openDatabase(): Promise<IDBDatabase> {
  if (!dbPromise) {
    dbPromise = new Promise((resolve, reject) => {
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
      request.onsuccess = () => {
        const db = request.result;
        db.onclose = () => {
          dbPromise = null;
        };
        resolve(db);
      };
      request.onerror = () => {
        dbPromise = null;
        reject(request.error);
      };
    });
  }
  return dbPromise;
}

async function idbGetAll(store: string): Promise<unknown[]> {
  const db = await openDatabase();
  return new Promise<unknown[]>((resolve, reject) => {
    const tx = db.transaction(store, 'readonly');
    const request = tx.objectStore(store).getAll();
    request.onsuccess = () => resolve(request.result);
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error);
  });
}

async function idbGet(store: string, id: string): Promise<unknown> {
  const db = await openDatabase();
  return new Promise<unknown>((resolve, reject) => {
    const tx = db.transaction(store, 'readonly');
    const request = tx.objectStore(store).get(id);
    request.onsuccess = () => resolve(request.result);
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error);
  });
}

async function putMany(store: string, values: object[]): Promise<void> {
  const db = await openDatabase();
  return new Promise<void>((resolve, reject) => {
    const tx = db.transaction(store, 'readwrite');
    const objectStore = tx.objectStore(store);
    for (const value of values) {
      objectStore.put(value);
    }
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error);
  });
}

async function deleteMany(store: string, ids: string[]): Promise<void> {
  const db = await openDatabase();
  return new Promise<void>((resolve, reject) => {
    const tx = db.transaction(store, 'readwrite');
    const objectStore = tx.objectStore(store);
    for (const id of ids) {
      objectStore.delete(id);
    }
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error);
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

export interface HistoryRepository {
  list(query: HistoryQuery): Promise<HistoryFetchResult>;
  fetchDocument(documentId: string): Promise<CompleteAnalysisResponse | null>;
  remove(documentId: string): Promise<boolean>;
  getOfflineDocument(documentId: string): Promise<OfflineDocument | null>;
  listOffline(): Promise<OfflineDocument[]>;
}

function asOfflineDocument(value: unknown): OfflineDocument | null {
  if (typeof value !== 'object' || value === null) return null;
  const record = value as Record<string, unknown>;
  if (typeof record['id'] !== 'string' || typeof record['title'] !== 'string') return null;
  return {
    id: record['id'],
    title: record['title'],
    wordCount: typeof record['wordCount'] === 'number' ? record['wordCount'] : 0,
    characterCount: typeof record['characterCount'] === 'number' ? record['characterCount'] : 0,
    sentenceCount: typeof record['sentenceCount'] === 'number' ? record['sentenceCount'] : 0,
    paragraphCount: typeof record['paragraphCount'] === 'number' ? record['paragraphCount'] : 0,
    sentimentClassification:
      typeof record['sentimentClassification'] === 'string'
        ? record['sentimentClassification']
        : 'neutral',
    cefrEquivalent: typeof record['cefrEquivalent'] === 'string' ? record['cefrEquivalent'] : 'A1',
    createdAt: typeof record['createdAt'] === 'string' ? record['createdAt'] : ''
  };
}

export const historyRepository: HistoryRepository = {
  async list(query) {
    const params = new URLSearchParams({
      page: String(query.page),
      page_size: String(query.pageSize)
    });
    if (query.search.trim()) params.set('search', query.search.trim());

    try {
      const response = await fetch(`${endpoints.history}?${params.toString()}`, {
        headers: identityHeaders()
      });
      if (!response.ok) throw new Error(String(response.status));
      const body = (await response.json()) as PaginatedHistoryResponse;

      // DATA-02: mirror the page into IndexedDB in one batched readwrite
      // transaction instead of one connection cycle per row.
      if (body.items.length > 0) {
        await putMany(
          CACHE_STORE,
          body.items.map((item) => ({
            id: item.id,
            title: item.title,
            wordCount: item.wordCount,
            sentimentClassification: item.sentimentClassification,
            cefrEquivalent: item.cefrEquivalent,
            createdAt: item.createdAt
          }))
        ).catch(() => undefined);
      }

      return { response: body, offline: false };
    } catch {
      // Offline fallback: serve the IndexedDB mirror with client-side paging.
      const cached = await idbGetAll(CACHE_STORE).catch(() => [] as unknown[]);
      const all = cached
        .map(asOfflineDocument)
        .filter((item): item is OfflineDocument => item !== null);
      const term = query.search.trim().toLowerCase();
      const filtered = term
        ? all.filter((item) => item.title.toLowerCase().includes(term))
        : all;
      filtered.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
      const start = (query.page - 1) * query.pageSize;
      const items: HistoryItemSummary[] = filtered
        .slice(start, start + query.pageSize)
        .map((item) => ({
          id: item.id,
          title: item.title,
          wordCount: item.wordCount,
          sentimentClassification: item
            .sentimentClassification as HistoryItemSummary['sentimentClassification'],
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
      const response = await fetch(endpoints.historyItem(documentId), {
        headers: identityHeaders()
      });
      if (!response.ok) throw new Error(String(response.status));
      const document = (await response.json()) as CompleteAnalysisResponse;
      // DATA-03: persist the full statistical metadata alongside the record.
      await putMany(CACHE_STORE, [
        {
          id: documentId,
          title: document.title,
          wordCount: document.statistics.wordCount,
          characterCount: document.statistics.characterCount,
          sentenceCount: document.statistics.sentenceCount,
          paragraphCount: document.statistics.paragraphCount,
          sentimentClassification: document.sentiment.classification,
          cefrEquivalent: document.readability.cefrEquivalent,
          createdAt: document.processedAt
        }
      ]).catch(() => undefined);
      return document;
    } catch {
      const offline = await historyRepository.getOfflineDocument(documentId);
      if (!offline) return null;
      return {
        documentId: offline.id,
        title: offline.title,
        statistics: {
          characterCount: offline.characterCount,
          wordCount: offline.wordCount,
          sentenceCount: offline.sentenceCount,
          paragraphCount: offline.paragraphCount
        },
        sentiment: null as unknown as CompleteAnalysisResponse['sentiment'],
        readability: null as unknown as CompleteAnalysisResponse['readability'],
        processedAt: offline.createdAt
      };
    }
  },

  async remove(documentId) {
    try {
      const response = await fetch(endpoints.historyItem(documentId), {
        method: 'DELETE',
        headers: identityHeaders()
      });
      if (!response.ok && response.status !== 404) throw new Error(String(response.status));
      await deleteMany(CACHE_STORE, [documentId]).catch(() => undefined);
      return true;
    } catch {
      // Offline: remove from the local mirror and queue the reconciliation.
      await deleteMany(CACHE_STORE, [documentId]).catch(() => undefined);
      await putMany(QUEUE_STORE, [{ id: documentId, kind: 'delete' }]).catch(() => undefined);
      return false;
    }
  },

  async getOfflineDocument(documentId) {
    try {
      const record = await idbGet(CACHE_STORE, documentId);
      return asOfflineDocument(record);
    } catch {
      return null;
    }
  },

  async listOffline() {
    const cached = await idbGetAll(CACHE_STORE).catch(() => [] as unknown[]);
    return cached
      .map(asOfflineDocument)
      .filter((item): item is OfflineDocument => item !== null);
  }
};
