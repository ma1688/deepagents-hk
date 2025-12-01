import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { UserConfig, ModelOption } from '@/types';

interface ConfigState {
  config: UserConfig | null;
  availableModels: ModelOption[];
  isLoading: boolean;
  error: string | null;
  
  // UI state
  isConfigPanelOpen: boolean;
  
  // Actions
  setConfig: (config: UserConfig) => void;
  setAvailableModels: (models: ModelOption[]) => void;
  setIsLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  toggleConfigPanel: () => void;
  setConfigPanelOpen: (open: boolean) => void;
}

export const useConfigStore = create<ConfigState>()(
  persist(
    (set) => ({
      config: null,
      availableModels: [],
      isLoading: false,
      error: null,
      isConfigPanelOpen: false,
      
      setConfig: (config) => set({ config }),
      setAvailableModels: (models) => set({ availableModels: models }),
      setIsLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),
      toggleConfigPanel: () => set((state) => ({ 
        isConfigPanelOpen: !state.isConfigPanelOpen 
      })),
      setConfigPanelOpen: (open) => set({ isConfigPanelOpen: open }),
    }),
    {
      name: 'hkex-config-storage',
      partialize: (state) => ({
        // Only persist UI preferences, not actual config data
        isConfigPanelOpen: state.isConfigPanelOpen,
      }),
    }
  )
);

