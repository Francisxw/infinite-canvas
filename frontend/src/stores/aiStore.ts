import { create } from 'zustand'

export interface AIGenerationTask {
  id: string
  prompt: string
  status: 'idle' | 'running' | 'done' | 'error'
  resultImage?: string
  error?: string
}

interface AIState {
  tasks: AIGenerationTask[]
  addTask: (task: AIGenerationTask) => void
  updateTask: (id: string, updates: Partial<AIGenerationTask>) => void
  removeTask: (id: string) => void
}

export const useAIStore = create<AIState>((set) => ({
  tasks: [],
  addTask: (task) =>
    set((state) => ({
      tasks: [task, ...state.tasks],
    })),
  updateTask: (id, updates) =>
    set((state) => ({
      tasks: state.tasks.map((task) => (task.id === id ? { ...task, ...updates } : task)),
    })),
  removeTask: (id) =>
    set((state) => ({
      tasks: state.tasks.filter((task) => task.id !== id),
    })),
}))
