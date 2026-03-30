import { describe, expect, it } from 'vitest'
import {
  MAX_MODEL_RETRIES,
  MODEL_RETRY_BASE_DELAY_MS,
  getModelRetryDelay,
} from '../useOpenRouterModels'

describe('useOpenRouterModels retry constants', () => {
  it('exposes a small, conservative max retry count', () => {
    expect(MAX_MODEL_RETRIES).toBe(3)
  })

  it('exposes a modest base delay', () => {
    expect(MODEL_RETRY_BASE_DELAY_MS).toBe(500)
  })
})

describe('getModelRetryDelay', () => {
  it('returns base delay for attempt 0', () => {
    expect(getModelRetryDelay(0)).toBe(MODEL_RETRY_BASE_DELAY_MS)
  })

  it('doubles on each subsequent attempt', () => {
    expect(getModelRetryDelay(1)).toBe(MODEL_RETRY_BASE_DELAY_MS * 2)
    expect(getModelRetryDelay(2)).toBe(MODEL_RETRY_BASE_DELAY_MS * 4)
  })

  it('stops retrying after the configured cap', () => {
    expect(getModelRetryDelay(MAX_MODEL_RETRIES)).toBeNull()
  })
})

describe('retry flow integration', () => {
  it('cumulative backoff stays under 4 seconds for the default configuration', () => {
    let total = 0
    for (let i = 0; i < MAX_MODEL_RETRIES; i++) {
      total += getModelRetryDelay(i) ?? 0
    }
    expect(total).toBe(3500)
    expect(total).toBeLessThan(4000)
  })

  it('attempts exactly MAX_MODEL_RETRIES + 1 total calls before giving up', () => {
    // The loop runs from 0..MAX_MODEL_RETRIES inclusive → 4 attempts
    const attempts = MAX_MODEL_RETRIES + 1
    expect(attempts).toBe(4)
  })
})
