import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:18000'

export const api = axios.create({
  baseURL,
  timeout: 120000,
})

export interface GenerateImagePayload {
  provider?: 'openrouter' | 'openai'
  prompt: string
  model: string
  aspect_ratio: '1:1' | '16:9' | '9:16' | '4:3' | '3:4'
  image_size: '1K' | '2K' | '4K'
  num_images: number
  stream?: boolean
}

export interface GenerateVideoPayload {
  provider?: 'openrouter' | 'openai'
  prompt: string
  model: string
  aspect_ratio: '16:9' | '9:16' | '1:1'
  duration: '5s' | '10s'
  quality: '720p' | '1080p'
  speed: 'standard' | 'fast'
  stream?: boolean
}

export interface GenerateTextPayload {
  provider?: 'openrouter' | 'openai'
  prompt: string | Array<
    | {
        type: 'text'
        text: string
      }
    | {
        type: 'image_url'
        image_url: {
          url: string
          detail?: 'low' | 'high' | 'auto'
        }
      }
  >
  model: string
}

type ProviderImageLike = {
  url?: string
  image_url?: { url?: string }
  imageUrl?: { url?: string }
  b64_json?: string
}

type ProviderMessageLike = {
  images?: ProviderImageLike[]
  content?: Array<{
    images?: ProviderImageLike[]
    image_url?: { url?: string }
    imageUrl?: { url?: string }
  }>
}

export interface NormalizedGenerateImageResponse {
  provider?: string
  images: string[]
  raw: unknown
  choices?: Array<{
    message?: {
      images?: Array<{
        image_url?: {
          url?: string
        }
      }>
    }
  }>
}

export interface NormalizedGenerateTextResponse {
  provider?: string
  text: string
  raw: unknown
}

export interface NormalizedGenerateVideoResponse {
  provider?: string
  videos: string[]
  raw: unknown
}

export interface UploadResponse {
  success: boolean
  filename: string
  content_type: string
  size: number
  data_url?: string
  dataUrl?: string
}

export interface NormalizedUploadResponse {
  success: boolean
  filename: string
  contentType: string
  size: number
  mediaUrl: string | null
}

type RequestOptions = {
  signal?: AbortSignal
}

type ApiErrorPayload = {
  error?: {
    code?: string
    message?: string
  }
}

function normalizeImageCandidate(candidate: ProviderImageLike | undefined): string | null {
  if (!candidate) return null

  const isValidBase64 = (value: string): boolean => {
    if (value.length < 100) return false
    const base64Regex = /^[A-Za-z0-9+/]*={0,2}$/
    return base64Regex.test(value)
  }

  const normalizeUrlLike = (value: unknown): string | null => {
    if (typeof value !== 'string') return null
    const trimmed = value.trim()
    if (trimmed.length === 0) return null
    if (trimmed.startsWith('data:')) return trimmed
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) return trimmed
    if (trimmed.startsWith('gen-')) return null
    if (!isValidBase64(trimmed)) return null
    return `data:image/png;base64,${trimmed}`
  }

  const direct = normalizeUrlLike(candidate.url)
  if (direct) return direct

  const snake = normalizeUrlLike(candidate.image_url?.url)
  if (snake) return snake

  const camel = normalizeUrlLike(candidate.imageUrl?.url)
  if (camel) return camel

  if (typeof candidate.b64_json === 'string' && candidate.b64_json.trim().length > 0) {
    return `data:image/png;base64,${candidate.b64_json.trim()}`
  }

  return null
}

function compactUrls(urls: Array<string | null | undefined>): string[] {
  return urls.filter((url): url is string => typeof url === 'string' && url.length > 0)
}

export function normalizeGenerateVideoResponse(payload: unknown): NormalizedGenerateVideoResponse {
  const record = typeof payload === 'object' && payload !== null ? (payload as Record<string, unknown>) : {}
  const directVideos = Array.isArray(record.videos) ? record.videos.filter((value): value is string => typeof value === 'string' && value.length > 0) : []

  const choices = Array.isArray(record.choices) ? record.choices : []
  const collected = choices.flatMap((choice) => {
    const choiceRecord = typeof choice === 'object' && choice !== null ? (choice as Record<string, unknown>) : {}
    const nestedValues: string[] = []

    const collect = (value: unknown) => {
      if (!value) return
      if (Array.isArray(value)) {
        value.forEach(collect)
        return
      }

      if (typeof value === 'string' && value.length > 0) {
        nestedValues.push(value)
        return
      }

      if (typeof value !== 'object') return
      const recordValue = value as Record<string, unknown>
      const url = recordValue.url
      if (typeof url === 'string' && url.length > 0) {
        nestedValues.push(url)
      }

      collect(recordValue.video_url)
      collect(recordValue.videoUrl)
      collect(recordValue.videos)
      collect(recordValue.video_urls)
      collect(recordValue.videoUrls)
      collect(recordValue.content)
      collect(recordValue.message)
    }

    collect(choiceRecord)
    return nestedValues
  })

  return {
    provider: typeof record.provider === 'string' ? record.provider : undefined,
    videos: Array.from(new Set([...directVideos, ...collected])),
    raw: payload,
  }
}

export function normalizeGenerateImageResponse(payload: unknown): NormalizedGenerateImageResponse {
  const record = typeof payload === 'object' && payload !== null ? (payload as Record<string, unknown>) : {}
  const choices = Array.isArray(record.choices) ? record.choices : []

  const collected = choices.flatMap((choice) => {
    const choiceRecord = typeof choice === 'object' && choice !== null ? (choice as Record<string, unknown>) : {}
    const message = typeof choiceRecord.message === 'object' && choiceRecord.message !== null
      ? (choiceRecord.message as ProviderMessageLike)
      : undefined

    const directImages = Array.isArray(message?.images) ? message.images : []
    const contentImages = Array.isArray(message?.content)
      ? message.content.flatMap((item) => {
          const nestedImages = Array.isArray(item.images) ? item.images : []
          const singular: ProviderImageLike[] = []
          if (item.image_url) singular.push({ image_url: item.image_url })
          if (item.imageUrl) singular.push({ imageUrl: item.imageUrl })
          return [...nestedImages, ...singular]
        })
      : []

    const contentArray = Array.isArray(choiceRecord.content)
      ? choiceRecord.content.flatMap((item) => {
          const itemRecord = typeof item === 'object' && item !== null ? (item as Record<string, unknown>) : {}
          const nestedImages = Array.isArray(itemRecord.images) ? (itemRecord.images as ProviderImageLike[]) : []
          const singular: ProviderImageLike[] = []
          if (typeof itemRecord.image_url === 'object' && itemRecord.image_url !== null) {
            singular.push({ image_url: itemRecord.image_url as { url?: string } })
          }
          if (typeof itemRecord.imageUrl === 'object' && itemRecord.imageUrl !== null) {
            singular.push({ imageUrl: itemRecord.imageUrl as { url?: string } })
          }
          return [...nestedImages, ...singular]
        })
      : []

    return compactUrls([...directImages, ...contentImages, ...contentArray].map(normalizeImageCandidate))
  })

  const images = Array.from(new Set(collected))

  return {
    provider: typeof record.provider === 'string' ? record.provider : undefined,
    images,
    raw: payload,
    choices: record.choices as NormalizedGenerateImageResponse['choices'] | undefined,
  }
}

export function normalizeUploadResponse(payload: UploadResponse): NormalizedUploadResponse {
  return {
    success: payload.success,
    filename: payload.filename,
    contentType: payload.content_type,
    size: payload.size,
    mediaUrl: payload.data_url ?? payload.dataUrl ?? null,
  }
}

export async function generateImage(payload: GenerateImagePayload, options?: RequestOptions) {
  const response = await api.post('/api/generate-image', payload, { signal: options?.signal })
  return normalizeGenerateImageResponse(response.data)
}

export async function generateVideo(payload: GenerateVideoPayload, options?: RequestOptions) {
  const response = await api.post('/api/generate-video', payload, { signal: options?.signal })
  return normalizeGenerateVideoResponse(response.data)
}

export async function generateText(payload: GenerateTextPayload, options?: RequestOptions) {
  const response = await api.post('/api/generate-text', payload, { signal: options?.signal })
  const record = typeof response.data === 'object' && response.data !== null ? (response.data as Record<string, unknown>) : {}
  return {
    provider: typeof record.provider === 'string' ? record.provider : undefined,
    text: typeof record.text === 'string' ? record.text : '',
    raw: response.data,
  } satisfies NormalizedGenerateTextResponse
}

export async function uploadAsset(file: File, options?: RequestOptions) {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post<UploadResponse>('/api/upload', formData, { signal: options?.signal })
  return normalizeUploadResponse(response.data)
}

export function getRequestErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError<ApiErrorPayload>(error)) {
    const message = error.response?.data?.error?.message
    if (typeof message === 'string' && message.length > 0) return message
  }

  if (error instanceof Error && error.message.length > 0) {
    return error.message
  }

  return fallback
}

export function isRequestCanceled(error: unknown) {
  return axios.isCancel(error)
}

export async function fetchModels(
  outputModality: 'image' | 'video' | 'text' | 'text,image' | 'all' = 'image',
  provider: 'openrouter' | 'openai' = 'openrouter'
) {
  const response = await api.get('/api/models', {
    params: { output_modality: outputModality, provider },
  })
  return response.data
}
