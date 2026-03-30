import { beforeEach, describe, expect, it, vi } from 'vitest'
import { authBridge } from '../authBridge'

beforeEach(() => {
  authBridge.reset()
})

describe('authBridge', () => {
  it('restores the previous bridge lifecycle after cleanup', () => {
    const firstSync = vi.fn()
    const secondSync = vi.fn()

    authBridge.configure({
      getToken: () => 'first-token',
      onAccountSync: firstSync,
    })

    const cleanup = authBridge.configure({
      getToken: () => 'second-token',
      onAccountSync: secondSync,
    })

    expect(authBridge.getToken()).toBe('second-token')
    authBridge.syncAccount({ points: 7 })
    expect(secondSync).toHaveBeenCalledWith({ points: 7 })
    expect(firstSync).not.toHaveBeenCalled()

    cleanup()

    expect(authBridge.getToken()).toBe('first-token')
    authBridge.syncAccount({ points: 5, refreshProfile: true })
    expect(firstSync).toHaveBeenCalledWith({ points: 5, refreshProfile: true })
  })

  it('resets back to inert defaults', () => {
    const onAuthFailure = vi.fn()

    authBridge.configure({
      getToken: () => 'token-demo',
      onAuthFailure,
    })

    authBridge.reset()

    expect(authBridge.getToken()).toBeNull()
    authBridge.handleAuthFailure()
    expect(onAuthFailure).not.toHaveBeenCalled()
  })
})
