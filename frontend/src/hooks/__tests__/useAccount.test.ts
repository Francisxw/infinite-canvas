import { AxiosError } from 'axios'
import { describe, expect, it } from 'vitest'
import { partializeAccountState } from '../../stores/accountStore'
import { isUnauthorizedError } from '../../services/api'
import {
  BOOTSTRAP_MAX_RETRIES,
  BOOTSTRAP_RETRY_BASE_DELAY,
  getBootstrapRetryDelay,
  resolveBootstrapOutcome,
  shouldBootstrapAccountSession,
} from '../useAccount'

function createAxiosAuthError(status: number, code: string) {
  return new AxiosError(
    'request failed',
    AxiosError.ERR_BAD_REQUEST,
    undefined,
    undefined,
    {
      data: {
        error: {
          code,
        },
      },
      status,
      statusText: 'Request Failed',
      headers: {},
      config: {} as never,
    }
  )
}

describe('useAccount bootstrap helpers', () => {
  it('treats auth_required 401 failures as auth invalidation', () => {
    const outcome = resolveBootstrapOutcome([
      {
        status: 'rejected',
        reason: createAxiosAuthError(401, 'auth_required'),
      },
      {
        status: 'fulfilled',
        value: undefined,
      },
    ])

    expect(outcome.kind).toBe('auth')
  })

  it('keeps non-auth bootstrap failures recoverable', () => {
    const transientError = new Error('packages unavailable')
    const outcome = resolveBootstrapOutcome([
      {
        status: 'fulfilled',
        value: undefined,
      },
      {
        status: 'rejected',
        reason: transientError,
      },
    ])

    expect(outcome).toEqual({ kind: 'recoverable', error: transientError })
  })

  it('prefers auth invalidation when mixed failures include auth_required', () => {
    const outcome = resolveBootstrapOutcome([
      {
        status: 'rejected',
        reason: new Error('packages unavailable'),
      },
      {
        status: 'rejected',
        reason: createAxiosAuthError(401, 'auth_required'),
      },
    ])

    expect(outcome.kind).toBe('auth')
  })
})

describe('isUnauthorizedError', () => {
  it('returns true only for auth_required 401 responses', () => {
    expect(isUnauthorizedError(createAxiosAuthError(401, 'auth_required'))).toBe(true)
    expect(isUnauthorizedError(createAxiosAuthError(403, 'auth_required'))).toBe(false)
    expect(isUnauthorizedError(createAxiosAuthError(401, 'payment_not_configured'))).toBe(false)
    expect(isUnauthorizedError(new Error('network'))).toBe(false)
  })
})

describe('bootstrap retry helpers', () => {
  it('starts with the base delay at retry count 0', () => {
    expect(getBootstrapRetryDelay(0)).toBe(BOOTSTRAP_RETRY_BASE_DELAY)
  })

  it('applies exponential backoff for increasing retry counts', () => {
    expect(getBootstrapRetryDelay(0)).toBe(1500)
    expect(getBootstrapRetryDelay(1)).toBe(3000)
    expect(getBootstrapRetryDelay(2)).toBe(6000)
    expect(getBootstrapRetryDelay(3)).toBe(12000)
    expect(getBootstrapRetryDelay(4)).toBe(24000)
  })

  it('stops scheduling retries once the cap is exhausted', () => {
    expect(getBootstrapRetryDelay(BOOTSTRAP_MAX_RETRIES)).toBeNull()
  })

  it('produces increasing delays within the retry cap', () => {
    const delays = Array.from({ length: BOOTSTRAP_MAX_RETRIES }, (_, i) => getBootstrapRetryDelay(i))
    for (let i = 1; i < delays.length; i++) {
      expect(delays[i]).not.toBeNull()
      expect(delays[i - 1]).not.toBeNull()
      expect(delays[i] as number).toBeGreaterThan(delays[i - 1] as number)
    }
  })
})

describe('bootstrap session gating', () => {
  it('skips bootstrap when there is no persisted bearer token', () => {
    expect(shouldBootstrapAccountSession(null)).toBe(false)
    expect(shouldBootstrapAccountSession('')).toBe(false)
    expect(shouldBootstrapAccountSession('   ')).toBe(false)
  })

  it('allows bootstrap when a persisted bearer token exists', () => {
    expect(shouldBootstrapAccountSession('session-token')).toBe(true)
  })
})

describe('account store persistence shape', () => {
  it('persists only bearer session essentials during the transition', () => {
    expect(partializeAccountState({
      token: 'session-token',
      profile: {
        id: 'user-1',
        email: 'demo@example.com',
        display_name: 'Demo',
        points: 12,
        created_at: '2024-01-01T00:00:00Z',
      },
      ledger: [
        {
          id: 'ledger-1',
          type: 'signup_bonus',
          amount: 12,
          balance_after: 12,
          description: 'signup bonus',
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
      packages: [
        {
          id: 'pkg-1',
          label: 'Starter',
          credits: 100,
          bonus_credits: 10,
          total_credits: 110,
          price_cny: 9.9,
        },
      ],
      pendingRechargeOrder: {
        order: {
          id: 'order-1',
          user_id: 'user-1',
          package_id: 'pkg-1',
          provider: 'wechatpay_native',
          out_trade_no: 'trade-1',
          status: 'pending',
          amount_cny: 9.9,
          credits: 100,
          bonus_credits: 10,
          total_credits: 110,
          code_url: 'weixin://pay/demo',
          payment_reference: null,
          provider_payload: null,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          paid_at: null,
        },
        package: null,
        codeUrl: 'weixin://pay/demo',
      },
      setSession: () => undefined,
      setProfile: () => undefined,
      setLedger: () => undefined,
      setPackages: () => undefined,
      setPendingRechargeOrder: () => undefined,
      syncPoints: () => undefined,
      clearSession: () => undefined,
    })).toEqual({
      token: 'session-token',
      profile: {
        id: 'user-1',
        email: 'demo@example.com',
        display_name: 'Demo',
        points: 12,
        created_at: '2024-01-01T00:00:00Z',
      },
    })
  })
})
