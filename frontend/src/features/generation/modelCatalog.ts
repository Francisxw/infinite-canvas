export type OpenRouterRawModel = {
  id: string
  name?: string
  description?: string
  architecture?: {
    input_modalities?: string[]
    output_modalities?: string[]
  }
}

export type ModelFamily = 'image' | 'video'

export type RequestedModelOption = {
  id: string
  family: ModelFamily
  label: string
  subtitle: string
  eta: string
  available: boolean
  source: 'live' | 'curated'
}

type CuratedModelSpec = Omit<RequestedModelOption, 'available' | 'source'> & {
  matchers: string[]
}

const IMAGE_MODEL_SPECS: CuratedModelSpec[] = [
  {
    id: 'google/gemini-3-pro-image-preview',
    family: 'image',
    label: 'Banana Pro',
    subtitle: 'Gemini 3 Pro Image Preview',
    eta: '1min',
    matchers: ['google/gemini-3-pro-image-preview'],
  },
  {
    id: 'google/gemini-3.1-flash-image-preview',
    family: 'image',
    label: 'Banana 2',
    subtitle: 'Gemini 3.1 Flash Image Preview',
    eta: '1min',
    matchers: ['google/gemini-3.1-flash-image-preview'],
  },
  {
    id: 'google/gemini-2.5-flash-image',
    family: 'image',
    label: 'Banana',
    subtitle: 'Gemini 2.5 Flash Image',
    eta: '1min',
    matchers: ['google/gemini-2.5-flash-image'],
  },
  {
    id: 'black-forest-labs/flux.2-klein-4b',
    family: 'image',
    label: 'Flux 2 Klein 4B',
    subtitle: 'Black Forest Labs',
    eta: '1min',
    matchers: ['black-forest-labs/flux.2-klein-4b', 'flux.2-klein-4b', 'flux 2 klein 4b'],
  },
  {
    id: 'black-forest-labs/flux.2-pro',
    family: 'image',
    label: 'Flux 2 Pro',
    subtitle: 'Black Forest Labs',
    eta: '1min',
    matchers: ['black-forest-labs/flux.2-pro', 'flux.2-pro', 'flux 2 pro'],
  },
  {
    id: 'black-forest-labs/flux.2-flex',
    family: 'image',
    label: 'Flux 2 Flex',
    subtitle: 'Black Forest Labs',
    eta: '1min',
    matchers: ['black-forest-labs/flux.2-flex', 'flux.2-flex', 'flux 2 flex'],
  },
  {
    id: 'bytedance-seed/seedream-4.5',
    family: 'image',
    label: 'Seedream 4.5',
    subtitle: 'ByteDance Seed',
    eta: '1min',
    matchers: ['bytedance-seed/seedream-4.5', 'seedream-4.5', 'seedream 4.5'],
  },
  {
    id: 'sourceful/riverflow-v2-pro',
    family: 'image',
    label: 'Riverflow V2 Pro',
    subtitle: 'Sourceful',
    eta: '1min',
    matchers: ['riverflow-v2-pro', 'riverflow v2 pro'],
  },
  {
    id: 'sourceful/riverflow-v2-fast',
    family: 'image',
    label: 'Riverflow V2 Fast',
    subtitle: 'Sourceful',
    eta: '1min',
    matchers: ['riverflow-v2-fast', 'riverflow v2 fast'],
  },
  {
    id: 'openai/gpt-5-image',
    family: 'image',
    label: 'GPT-5 Image',
    subtitle: 'OpenAI',
    eta: '1min',
    matchers: ['openai/gpt-5-image'],
  },
  {
    id: 'openai/gpt-5-image-mini',
    family: 'image',
    label: 'GPT-5 Image Mini',
    subtitle: 'OpenAI',
    eta: '1min',
    matchers: ['openai/gpt-5-image-mini'],
  },
]

const VIDEO_MODEL_SPECS: CuratedModelSpec[] = [
  { id: 'google/veo-3.1', family: 'video', label: 'Veo 3.1', subtitle: 'Google', eta: '2min', matchers: ['veo 3.1', 'veo-3.1'] },
  { id: 'google/veo-3.1-fast', family: 'video', label: 'Veo 3.1 Fast', subtitle: 'Google', eta: '1min', matchers: ['veo 3.1 fast', 'veo-3.1-fast'] },
  { id: 'kuaishou/kling', family: 'video', label: 'Kling', subtitle: 'Kuaishou / Hailuo', eta: '2min', matchers: ['kling', 'hailuo'] },
  { id: 'wan/wan-2.2-t2v', family: 'video', label: 'Wan 2.2 T2V', subtitle: 'Wan', eta: '2min', matchers: ['wan2.2', 'wan 2.2', 'wan-2.2'] },
  { id: 'wan/wan-2.2-i2v', family: 'video', label: 'Wan 2.2 I2V', subtitle: 'Wan', eta: '2min', matchers: ['wan2.2', 'wan 2.2', 'wan-2.2'] },
  { id: 'ltx/ltx2-pro', family: 'video', label: 'LTX2 Pro', subtitle: 'LTX', eta: '2min', matchers: ['ltx2 pro', 'ltx2-pro', 'ltx'] },
  { id: 'ltx/ltx2-fast', family: 'video', label: 'LTX2 Fast', subtitle: 'LTX', eta: '1min', matchers: ['ltx2 fast', 'ltx2-fast', 'ltx'] },
  { id: 'tencent/hunyuan-video-1.5', family: 'video', label: 'Hunyuan Video 1.5', subtitle: 'Tencent', eta: '2min', matchers: ['hunyuan video', 'hunyuan-video'] },
  { id: 'luma/ray3', family: 'video', label: 'Luma Ray3', subtitle: 'Luma / Dream Machine', eta: '2min', matchers: ['luma', 'ray3', 'dream machine'] },
  { id: 'minimax/video', family: 'video', label: 'MiniMax Video', subtitle: 'MiniMax', eta: '2min', matchers: ['minimax video', 'minimax'] },
  { id: 'bytedance/seedance', family: 'video', label: 'Seedance', subtitle: 'ByteDance', eta: '2min', matchers: ['seedance', 'bytedance video'] },
]

function normalizeText(value: string | undefined): string {
  return (value ?? '').toLowerCase()
}

function modelHaystack(model: OpenRouterRawModel): string {
  return [model.id, model.name, model.description].map(normalizeText).join(' ')
}

function scoreModelMatch(model: OpenRouterRawModel, spec: CuratedModelSpec): number {
  const matcherSet = new Set(spec.matchers.map((matcher) => normalizeText(matcher)))
  const id = normalizeText(model.id)
  const name = normalizeText(model.name)

  if (matcherSet.has(id) || (name.length > 0 && matcherSet.has(name))) {
    return 2
  }

  const haystack = modelHaystack(model)
  return spec.matchers.some((matcher) => haystack.includes(matcher.toLowerCase())) ? 1 : 0
}

function mapSpecsToUniqueLiveModels(models: OpenRouterRawModel[], specs: CuratedModelSpec[]): Array<OpenRouterRawModel | undefined> {
  const consumedIds = new Set<string>()

  return specs.map((spec) => {
    const rankedMatches = models
      .filter((model) => !consumedIds.has(model.id))
      .map((model) => ({ model, score: scoreModelMatch(model, spec) }))
      .filter((entry) => entry.score > 0)
      .sort((a, b) => b.score - a.score)

    const match = rankedMatches[0]?.model

    if (match) consumedIds.add(match.id)
    return match
  })
}

export function buildRequestedImageModels(models: OpenRouterRawModel[]): RequestedModelOption[] {
  const uniqueMatches = mapSpecsToUniqueLiveModels(models, IMAGE_MODEL_SPECS)

  return IMAGE_MODEL_SPECS.map((spec, index) => {
    const live = uniqueMatches[index]
    const isExplicitlyIntegrated = [
      'bytedance-seed/seedream-4.5',
      'black-forest-labs/flux.2-pro',
      'black-forest-labs/flux.2-flex',
      'black-forest-labs/flux.2-klein-4b',
    ].includes(spec.id)

    return {
      id: live?.id ?? spec.id,
      family: spec.family,
      label: spec.label,
      subtitle: live?.name ?? spec.subtitle,
      eta: spec.eta,
      available: Boolean(live) || isExplicitlyIntegrated,
      source: live ? 'live' : isExplicitlyIntegrated ? 'live' : 'curated',
    }
  })
}

export function buildRequestedVideoModels(models: OpenRouterRawModel[]): RequestedModelOption[] {
  const uniqueMatches = mapSpecsToUniqueLiveModels(models, VIDEO_MODEL_SPECS)

  return VIDEO_MODEL_SPECS.map((spec, index) => {
    const live = uniqueMatches[index]
    return {
      id: live?.id ?? spec.id,
      family: spec.family,
      label: spec.label,
      subtitle: live?.name ?? `${spec.subtitle} · OpenRouter 未开放`,
      eta: spec.eta,
      available: Boolean(live),
      source: live ? 'live' : 'curated',
    }
  })
}
