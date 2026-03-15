import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

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

export async function generateImage(payload: GenerateImagePayload) {
  const response = await api.post('/api/generate-image', {
    provider: 'openrouter',
    ...payload,
  })
  return response.data
}

export async function uploadAsset(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post('/api/upload', formData)
  return response.data
}

export async function fetchModels(
  outputModality = 'image',
  provider: 'openrouter' | 'openai' = 'openrouter'
) {
  const response = await api.get('/api/models', {
    params: { output_modality: outputModality, provider },
  })
  return response.data
}
