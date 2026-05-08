import { describe, expect, it } from 'vitest'
import {
  normalizeGenerateImageResponse,
  normalizeGenerateVideoResponse,
  normalizeUploadResponse,
} from '../api'

describe('api normalizers', () => {
  it('normalizeGenerateImageResponse collects nested and base64 images', () => {
    const response = normalizeGenerateImageResponse({
      provider: 'openrouter',
      choices: [
        {
          message: {
            images: [{ image_url: { url: 'https://example.com/a.png' } }],
            content: [
              { imageUrl: { url: 'https://example.com/b.png' } },
              { images: [{ b64_json: 'ZmFrZQ==' }] },
            ],
          },
        },
      ],
    })

    expect(response.provider).toBe('openrouter')
    expect(response.images).toEqual([
      'https://example.com/a.png',
      'https://example.com/b.png',
      'data:image/png;base64,ZmFrZQ==',
    ])
  })

  it('normalizeGenerateImageResponse accepts bare base64-like url fields', () => {
    const response = normalizeGenerateImageResponse({
      provider: 'openrouter',
      choices: [
        {
          message: {
            images: [{ url: ' iVBORw0KGgoAAAANSUhEUgAA ' }],
            content: [
              { image_url: { url: ' data:image/png;base64,abc123 ' } },
            ],
          },
        },
      ],
    })

    expect(response.images).toEqual([
      'data:image/png;base64,abc123',
    ])
  })

  it('normalizeUploadResponse supports snake_case and camelCase data urls', () => {
    expect(normalizeUploadResponse({
      success: true,
      filename: 'asset.png',
      content_type: 'image/png',
      size: 42,
      data_url: 'https://example.com/data-url.png',
    })).toEqual({
      success: true,
      filename: 'asset.png',
      contentType: 'image/png',
      size: 42,
      mediaUrl: 'https://example.com/data-url.png',
    })

    expect(normalizeUploadResponse({
      success: true,
      filename: 'asset.png',
      content_type: 'image/png',
      size: 42,
      dataUrl: 'https://example.com/camel.png',
    })).toEqual({
      success: true,
      filename: 'asset.png',
      contentType: 'image/png',
      size: 42,
      mediaUrl: 'https://example.com/camel.png',
    })
  })

  it('normalizeGenerateVideoResponse collects direct and nested video urls', () => {
    const response = normalizeGenerateVideoResponse({
      provider: 'openrouter',
      videos: ['https://example.com/direct.mp4'],
      choices: [
        {
          message: {
            videos: [{ url: 'https://example.com/message.mp4' }],
            content: [
              { video_url: { url: 'https://example.com/content.mp4' } },
            ],
          },
        },
      ],
    })

    expect(response.provider).toBe('openrouter')
    expect(response.videos).toEqual([
      'https://example.com/direct.mp4',
      'https://example.com/message.mp4',
      'https://example.com/content.mp4',
    ])
  })
})
