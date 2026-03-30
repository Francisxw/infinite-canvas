import { AxiosError, AxiosHeaders } from 'axios'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api, fetchAccountProfile, fetchAccountSettings, generateText, login, normalizeGenerateImageResponse, normalizeGenerateVideoResponse, normalizeUploadResponse, updateAccountSettings } from '../api'
import { authBridge } from '../authBridge'

beforeEach(() => {
  authBridge.reset()
  vi.restoreAllMocks()
})

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

  it('injects bearer token through the existing request interceptor', async () => {
    authBridge.configure({
      getToken: () => 'token-demo',
    })

    const response = await api.get('/token-check', {
      adapter: async (config) => ({
        data: null,
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      }),
    })

    expect((response.config.headers as AxiosHeaders).get('Authorization')).toBe('Bearer token-demo')
  })

  it('syncs account points from header-based responses', async () => {
    const syncAccount = vi.fn()
    authBridge.configure({ onAccountSync: syncAccount })
    vi.spyOn(api, 'post').mockResolvedValue({
      data: { provider: 'openrouter', text: 'hello' },
      headers: { 'x-account-points': '42' },
    } as never)

    const response = await generateText({ provider: 'openrouter', prompt: 'hello', model: 'demo-model' })

    expect(response.points).toBe(42)
    expect(syncAccount).toHaveBeenCalledWith({ points: 42, refreshProfile: true })
  })

  it('syncs account points from body-based account responses', async () => {
    const syncAccount = vi.fn()
    authBridge.configure({ onAccountSync: syncAccount })
    vi.spyOn(api, 'get').mockResolvedValue({
      data: {
        user: {
          id: 'user-1',
          email: 'demo@example.com',
          display_name: 'Demo',
          points: 18,
          created_at: '2024-01-01T00:00:00Z',
        },
        ledger: [],
      },
    } as never)

    const response = await fetchAccountProfile()

    expect(response.user.points).toBe(18)
    expect(syncAccount).toHaveBeenCalledWith({ points: 18 })
  })

  it('supports account settings read and update helpers', async () => {
    const syncAccount = vi.fn()
    authBridge.configure({ onAccountSync: syncAccount })
    vi.spyOn(api, 'get').mockResolvedValue({
      data: {
        user: {
          id: 'user-1',
          email: 'demo@example.com',
          display_name: 'Demo',
          points: 18,
          created_at: '2024-01-01T00:00:00Z',
          openrouter: {
            mode: 'custom',
            has_custom_key: true,
            key_mask: 'sk-or-v1...1234',
            preferred_models: {
              text: 'google/gemini-3.1-flash',
              image: 'google/gemini-3.1-flash-image-preview',
              video: 'google/veo-3.1',
            },
          },
        },
        settings: {
          mode: 'custom',
          has_custom_key: true,
          key_mask: 'sk-or-v1...1234',
          preferred_models: {
            text: 'google/gemini-3.1-flash',
            image: 'google/gemini-3.1-flash-image-preview',
            video: 'google/veo-3.1',
          },
        },
      },
    } as never)
    vi.spyOn(api, 'patch').mockResolvedValue({
      data: {
        user: {
          id: 'user-1',
          email: 'demo@example.com',
          display_name: 'Demo',
          points: 18,
          created_at: '2024-01-01T00:00:00Z',
          openrouter: {
            mode: 'platform',
            has_custom_key: true,
            key_mask: 'sk-or-v1...1234',
            preferred_models: {
              text: null,
              image: null,
              video: null,
            },
          },
        },
        settings: {
          mode: 'platform',
          has_custom_key: true,
          key_mask: 'sk-or-v1...1234',
          preferred_models: {
            text: null,
            image: null,
            video: null,
          },
        },
      },
    } as never)

    const current = await fetchAccountSettings()
    const updated = await updateAccountSettings({ openrouter_mode: 'platform', preferred_models: { text: null, image: null, video: null } })

    expect(current.settings.mode).toBe('custom')
    expect(updated.settings.mode).toBe('platform')
    expect(syncAccount).toHaveBeenCalledWith({ points: 18 })
  })

  it('handles auth_required 401 responses through the response interceptor', async () => {
    const handleAuthFailure = vi.fn()
    authBridge.configure({ onAuthFailure: handleAuthFailure })

    await expect(api.get('/auth-required', {
      adapter: async (config) => {
        throw new AxiosError(
          'Unauthorized',
          AxiosError.ERR_BAD_REQUEST,
          config,
          undefined,
          {
            data: {
              error: {
                code: 'auth_required',
              },
            },
            status: 401,
            statusText: 'Unauthorized',
            headers: {},
            config,
          }
        )
      },
    })).rejects.toMatchObject({
      response: {
        status: 401,
      },
    })

    expect(handleAuthFailure).toHaveBeenCalledTimes(1)
  })

  it('keeps login request helpers unchanged while syncing points from the auth payload', async () => {
    const syncAccount = vi.fn()
    authBridge.configure({ onAccountSync: syncAccount })
    vi.spyOn(api, 'post').mockResolvedValue({
      data: {
        token: 'session-token',
        user: {
          id: 'user-1',
          email: 'demo@example.com',
          display_name: 'Demo',
          points: 27,
          created_at: '2024-01-01T00:00:00Z',
        },
        ledger: [],
      },
    } as never)

    const response = await login({ email: 'demo@example.com', password: 'secret' })

    expect(response.token).toBe('session-token')
    expect(syncAccount).toHaveBeenCalledWith({ points: 27 })
  })
})
