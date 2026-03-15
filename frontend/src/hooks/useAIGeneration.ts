import { useCallback } from 'react'
import { generateImage, type GenerateImagePayload } from '../services/api'
import { useAIStore } from '../stores/aiStore'

function createTaskId() {
  return `task_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

export function useAIGeneration() {
  const addTask = useAIStore((state) => state.addTask)
  const updateTask = useAIStore((state) => state.updateTask)

  const runGeneration = useCallback(
    async (payload: GenerateImagePayload) => {
      const taskId = createTaskId()
      addTask({ id: taskId, prompt: payload.prompt, status: 'running' })

      try {
        const result = await generateImage(payload)
        const firstImage =
          result?.choices?.[0]?.message?.images?.[0]?.image_url?.url ||
          result?.choices?.[0]?.message?.images?.[0]?.imageUrl?.url

        updateTask(taskId, {
          status: 'done',
          resultImage: firstImage,
        })

        return { taskId, result }
      } catch (error) {
        updateTask(taskId, {
          status: 'error',
          error: error instanceof Error ? error.message : 'Unknown error',
        })
        throw error
      }
    },
    [addTask, updateTask]
  )

  return { runGeneration }
}
