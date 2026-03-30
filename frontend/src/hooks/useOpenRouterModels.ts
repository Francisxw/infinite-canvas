import { useEffect, useMemo, useState } from 'react'
import { fetchModels, getRequestErrorMessage } from '../services/api'
import { useAccountStore } from '../stores/accountStore'
import {
  buildRequestedImageModels,
  buildRequestedVideoModels,
  type OpenRouterRawModel,
  type RequestedModelOption,
} from '../features/generation/modelCatalog'

type ModelState = {
  imageModels: RequestedModelOption[]
  videoModels: RequestedModelOption[]
  loading: boolean
  error: string | null
}

type RawModelsResponse = {
  data?: OpenRouterRawModel[]
}

const emptyState: ModelState = {
  imageModels: buildRequestedImageModels([]),
  videoModels: buildRequestedVideoModels([]),
  loading: true,
  error: null,
}

/** Maximum number of retry attempts before surfacing the error. */
export const MAX_MODEL_RETRIES = 3
export const MODEL_RETRY_BASE_DELAY_MS = 500

export function getModelRetryDelay(retryCount: number): number | null {
  if (retryCount >= MAX_MODEL_RETRIES) {
    return null
  }

  return MODEL_RETRY_BASE_DELAY_MS * 2 ** retryCount
}

function sleep(delay: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, delay)
  })
}

export function useOpenRouterModels() {
  const [state, setState] = useState<ModelState>(emptyState)
  const preferredImageModel = useAccountStore((store) => store.profile?.openrouter?.preferred_models.image)
  const preferredVideoModel = useAccountStore((store) => store.profile?.openrouter?.preferred_models.video)
  const providerMode = useAccountStore((store) => store.profile?.openrouter?.mode)
  const hasCustomKey = useAccountStore((store) => store.profile?.openrouter?.has_custom_key)

  useEffect(() => {
    let active = true

    async function load() {
      let lastError: unknown = null

      for (let attempt = 0; attempt <= MAX_MODEL_RETRIES; attempt++) {
        if (!active) return
        try {
          const response = (await fetchModels('all', 'openrouter')) as RawModelsResponse
          const liveModels = Array.isArray(response?.data) ? response.data : []
          const preferredCandidates = [preferredImageModel, preferredVideoModel].filter((value): value is string => Boolean(value))
          const injected = preferredCandidates
            .filter((modelId) => !liveModels.some((model) => model.id === modelId))
            .map((modelId) => ({ id: modelId, name: modelId }))
          const withPreferred = [...injected, ...liveModels]
          if (!active) return
          setState({
            imageModels: buildRequestedImageModels(withPreferred),
            videoModels: buildRequestedVideoModels(withPreferred),
            loading: false,
            error: providerMode === 'custom' && !hasCustomKey ? '当前已切到自定义 OpenRouter，但尚未保存有效密钥。' : null,
          })
          return // success – exit retry loop
        } catch (error) {
          lastError = error
          const delay = getModelRetryDelay(attempt)
          if (delay === null || !active) {
            break
          }

          await sleep(delay)

          if (!active) return
        }
      }

      // All retries exhausted – surface the error via the same path as before
      if (!active) return
      setState({
        imageModels: buildRequestedImageModels([]),
        videoModels: buildRequestedVideoModels([]),
        loading: false,
        error: getRequestErrorMessage(lastError, '模型加载失败，请稍后重试。'),
      })
    }

    void load()

    return () => {
      active = false
    }
  }, [hasCustomKey, preferredImageModel, preferredVideoModel, providerMode])

  return useMemo(() => state, [state])
}
