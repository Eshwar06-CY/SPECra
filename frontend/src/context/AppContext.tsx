import React, { createContext, useContext, useState, useEffect } from 'react';
import { getAIHealth } from '../api/intelligence';
import type { AIHealthResponse } from '../types/api';
import type { QueryResponse } from '../api/query';

interface AppContextType {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  selectedJobId: string | null;
  setSelectedJobId: (jobId: string | null) => void;
  selectedProductId: string | null;
  setSelectedProductId: (productId: string | null) => void;
  aiStatus: AIHealthResponse | null;
  refreshAIHealth: () => void;
  activeQuery: string | null;
  setActiveQuery: (query: string | null) => void;
  queryResults: QueryResponse | null;
  setQueryResults: (res: QueryResponse | null) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const getInitialTab = (): string => {
    try {
      const hash = window.location.hash.replace('#/', '').replace('#', '');
      if (hash) return hash;
      const stored = localStorage.getItem('specra_active_tab');
      if (stored) return stored;
    } catch {}
    return 'landing';
  };

  const [activeTab, setActiveTabState] = useState<string>(getInitialTab);

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#/', '').replace('#', '').split('?')[0];
      if (hash) {
        setActiveTabState(hash);
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);
  const [selectedJobId, setSelectedJobIdState] = useState<string | null>(() => {
    try {
      return localStorage.getItem('specra_selected_job_id');
    } catch {
      return null;
    }
  });

  const setActiveTab = (tab: string) => {
    setActiveTabState(tab);
    try {
      localStorage.setItem('specra_active_tab', tab);
      window.location.hash = `/${tab}`;
    } catch {}
  };

  const setSelectedJobId = (jobId: string | null) => {
    setSelectedJobIdState(jobId);
    try {
      if (jobId) {
        localStorage.setItem('specra_selected_job_id', jobId);
      } else {
        localStorage.removeItem('specra_selected_job_id');
      }
    } catch {}
  };

  const [selectedProductId, setSelectedProductId] = useState<string | null>(
    'b17feefb-5796-4b91-b487-dd6eb9bad9f7'
  );
  const [aiStatus, setAiStatus] = useState<AIHealthResponse | null>(null);
  const [activeQuery, setActiveQuery] = useState<string | null>(null);
  const [queryResults, setQueryResults] = useState<QueryResponse | null>(null);

  const refreshAIHealth = async () => {
    try {
      const data = await getAIHealth();
      setAiStatus(data);
    } catch {
      setAiStatus({
        status: 'unavailable',
        model: 'gemini-3.7-flash',
        provider: 'gemini',
        api_key_configured: true,
      });
    }
  };

  useEffect(() => {
    refreshAIHealth();
  }, []);

  return (
    <AppContext.Provider
      value={{
        activeTab,
        setActiveTab,
        selectedJobId,
        setSelectedJobId,
        selectedProductId,
        setSelectedProductId,
        aiStatus,
        refreshAIHealth,
        activeQuery,
        setActiveQuery,
        queryResults,
        setQueryResults,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = (): AppContextType => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
