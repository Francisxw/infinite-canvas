import { create } from 'zustand'

export type DockPanel = 'create' | 'history' | 'assets' | 'profile' | null

type GenerationRecord = {
  id: string
  kind: 'image' | 'video' | 'text'
  prompt: string
  createdAt: number
  status: 'running' | 'done' | 'error' | 'unsupported' | 'cancelled'
}

type AssetRecord = {
  id: string
  kind: 'image' | 'video' | 'text'
  name: string
  createdAt: number
  url?: string
}

type CanvasDockState = {
  activePanel: DockPanel
  history: GenerationRecord[]
  assets: AssetRecord[]
  setActivePanel: (panel: DockPanel) => void
  addHistory: (record: GenerationRecord) => void
  updateHistory: (id: string, patch: Partial<GenerationRecord>) => void
  removeHistory: (id: string) => void
  clearHistory: () => void
  addAsset: (asset: AssetRecord) => void
  removeAsset: (id: string) => void
  clearAssets: () => void
}

export const useCanvasDockStore = create<CanvasDockState>((set) => ({
  activePanel: null,
  history: [],
  assets: [],
  setActivePanel: (panel) => set({ activePanel: panel }),
  addHistory: (record) => set((state) => ({ history: [record, ...state.history].slice(0, 24) })),
  updateHistory: (id, patch) =>
    set((state) => ({
      history: state.history.map((item) => (item.id === id ? { ...item, ...patch } : item)),
    })),
  removeHistory: (id) =>
    set((state) => ({
      history: state.history.filter((item) => item.id !== id),
    })),
  clearHistory: () => set({ history: [] }),
  addAsset: (asset) => set((state) => ({ assets: [asset, ...state.assets].slice(0, 48) })),
  removeAsset: (id) =>
    set((state) => ({
      assets: state.assets.filter((item) => item.id !== id),
    })),
  clearAssets: () => set({ assets: [] }),
}))
