export interface StoredQueryHistoryItem {
  id: string;
  query: string;
  timestamp: string;
  result_count: number;
}

const STORAGE_KEY = 'deadlock_query_history';

export const getQueryHistory = (): StoredQueryHistoryItem[] => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch {
    return [];
  }
};

export const saveQueryHistoryItem = (query: string, result_count: number) => {
  try {
    const existing = getQueryHistory();
    const cleanQuery = query.trim();
    // Filter duplicates
    const filtered = existing.filter((item) => item.query.toLowerCase() !== cleanQuery.toLowerCase());
    const newItem: StoredQueryHistoryItem = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      query: cleanQuery,
      timestamp: new Date().toISOString(),
      result_count,
    };
    const updated = [newItem, ...filtered].slice(0, 10);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch (err) {
    console.error('Failed to persist query history:', err);
  }
};
