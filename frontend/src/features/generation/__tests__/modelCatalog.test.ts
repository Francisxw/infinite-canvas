import { describe, expect, it } from 'vitest'
import { buildRequestedImageModels, buildRequestedVideoModels } from '../modelCatalog'

describe('model catalog unique live mapping', () => {
  it('keeps image option ids unique when matcher substrings overlap', () => {
    const models = [
      {
        id: 'openai/gpt-5-image-mini',
        name: 'openai/gpt-5-image-mini',
      },
      {
        id: 'openai/gpt-5-image',
        name: 'openai/gpt-5-image',
      },
    ]

    const options = buildRequestedImageModels(models)
    const ids = options.map((item) => item.id)
    expect(new Set(ids).size).toBe(ids.length)
  })

  it('keeps video option ids unique under broad matcher collisions', () => {
    const models = [
      {
        id: 'ltx/ltx2-pro',
        name: 'LTX2 Pro',
      },
      {
        id: 'ltx/ltx2-fast',
        name: 'LTX2 Fast',
      },
    ]

    const options = buildRequestedVideoModels(models)
    const ids = options.map((item) => item.id)
    expect(new Set(ids).size).toBe(ids.length)
  })
})
