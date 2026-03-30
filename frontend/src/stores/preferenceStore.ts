import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface PreferenceState {
  language: 'zh' | 'en'
  model: string
  imageSize: '1K' | '2K' | '4K'
  setLanguage: (language: 'zh' | 'en') => void
  setModel: (model: string) => void
  setImageSize: (imageSize: '1K' | '2K' | '4K') => void
}

export const usePreferenceStore = create<PreferenceState>()(
  persist(
    (set) => ({
      language: 'zh',
      model: 'google/gemini-3.1-flash-image-preview',
      imageSize: '1K',
      setLanguage: (language) => set({ language }),
      setModel: (model) => set({ model }),
      setImageSize: (imageSize) => set({ imageSize }),
    }),
    {
      name: 'infinite-canvas-preferences',
    }
  )
)
