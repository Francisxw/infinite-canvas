import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  fetchAccountSettings,
  createWeChatRechargeOrder,
  fetchAccountPackages,
  fetchAccountProfile,
  fetchWeChatRechargeOrder,
  getRequestErrorMessage,
  isUnauthorizedError,
  login as loginRequest,
  logout as logoutRequest,
  register as registerRequest,
  updateAccountSettings,
  type LoginPayload,
  type RegisterPayload,
  type UpdateAccountSettingsPayload,
} from '../services/api'
import { authBridge } from '../services/authBridge'
import { useAccountStore } from '../stores/accountStore'

type BootstrapOutcome =
  | { kind: 'success' }
  | { kind: 'auth'; error: unknown }
  | { kind: 'recoverable'; error: unknown }

export function resolveBootstrapOutcome(results: PromiseSettledResult<void>[]): BootstrapOutcome {
  const rejected = results.filter((result): result is PromiseRejectedResult => result.status === 'rejected')

  if (rejected.length === 0) {
    return { kind: 'success' }
  }

  const authFailure = rejected.find((result) => isUnauthorizedError(result.reason))
  if (authFailure) {
    return { kind: 'auth', error: authFailure.reason }
  }

  return { kind: 'recoverable', error: rejected[0].reason }
}

export const BOOTSTRAP_RETRY_BASE_DELAY = 1500
export const BOOTSTRAP_MAX_RETRIES = 5

export function getBootstrapRetryDelay(retryCount: number): number | null {
  if (retryCount >= BOOTSTRAP_MAX_RETRIES) {
    return null
  }

  return BOOTSTRAP_RETRY_BASE_DELAY * 2 ** retryCount
}

export function shouldBootstrapAccountSession(token: string | null): boolean {
  return typeof token === 'string' && token.trim().length > 0
}

export function useAccount() {
  const token = useAccountStore((state) => state.token)
  const profile = useAccountStore((state) => state.profile)
  const ledger = useAccountStore((state) => state.ledger)
  const packages = useAccountStore((state) => state.packages)
  const setSession = useAccountStore((state) => state.setSession)
  const setProfile = useAccountStore((state) => state.setProfile)
  const setLedger = useAccountStore((state) => state.setLedger)
  const setPackages = useAccountStore((state) => state.setPackages)
  const clearSession = useAccountStore((state) => state.clearSession)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const mountedRef = useRef(true)
  const bootstrappedRef = useRef(false)
  const refreshInFlightRef = useRef(false)
  const bootstrapRetryTimerRef = useRef<number | null>(null)
  const bootstrapRetryCountRef = useRef(0)
  const sessionVersionRef = useRef(0)
  const rechargePollInFlightRef = useRef(false)

  const clearBootstrapRetryTimer = useCallback(() => {
    if (bootstrapRetryTimerRef.current !== null) {
      window.clearTimeout(bootstrapRetryTimerRef.current)
      bootstrapRetryTimerRef.current = null
    }
  }, [])

  const bumpSessionVersion = useCallback(() => {
    sessionVersionRef.current += 1
    return sessionVersionRef.current
  }, [])

  const isActiveSessionVersion = useCallback((version: number) => sessionVersionRef.current === version, [])

  useEffect(() => () => {
    mountedRef.current = false
    clearBootstrapRetryTimer()
  }, [clearBootstrapRetryTimer])

  const refreshProfile = useCallback(async () => {
    const sessionVersion = sessionVersionRef.current
    refreshInFlightRef.current = true
    try {
      const result = await fetchAccountProfile()
      if (!isActiveSessionVersion(sessionVersion)) return
      setProfile(result.user)
      setLedger(result.ledger)
    } finally {
      if (isActiveSessionVersion(sessionVersion)) {
        refreshInFlightRef.current = false
      }
    }
  }, [isActiveSessionVersion, setLedger, setProfile])

  const refreshSettings = useCallback(async () => {
    const sessionVersion = sessionVersionRef.current
    const result = await fetchAccountSettings()
    if (!isActiveSessionVersion(sessionVersion)) return
    setProfile(result.user)
  }, [isActiveSessionVersion, setProfile])

  const refreshPackages = useCallback(async () => {
    const sessionVersion = sessionVersionRef.current
    const result = await fetchAccountPackages()
    if (!isActiveSessionVersion(sessionVersion)) return
    setPackages(result.packages)
    setProfile(result.user)
  }, [isActiveSessionVersion, setPackages, setProfile])

  const bootstrap = useCallback(async () => {
    if (bootstrappedRef.current) return
    if (!shouldBootstrapAccountSession(useAccountStore.getState().token)) {
      setError(null)
      return
    }

    const sessionVersion = sessionVersionRef.current
    bootstrappedRef.current = true
    clearBootstrapRetryTimer()

    const outcome = resolveBootstrapOutcome(await Promise.allSettled([refreshProfile(), refreshPackages(), refreshSettings()]))

    if (!mountedRef.current || !isActiveSessionVersion(sessionVersion)) {
      bootstrappedRef.current = false
      return
    }

    if (outcome.kind === 'success') {
      bootstrapRetryCountRef.current = 0
      setError(null)
      return
    }

    bootstrappedRef.current = false

    if (outcome.kind === 'auth') {
      bootstrapRetryCountRef.current = 0
      clearSession()
      setError('登录状态已失效，请重新登录。')
      return
    }

    console.error('account bootstrap failed', outcome.error)
    setError(getRequestErrorMessage(outcome.error, '账户初始化失败，请稍后重试。'))

    const delay = getBootstrapRetryDelay(bootstrapRetryCountRef.current)
    if (delay === null) {
      console.error(`account bootstrap retries exhausted after ${BOOTSTRAP_MAX_RETRIES} attempts`)
      return
    }

    bootstrapRetryCountRef.current += 1
    bootstrapRetryTimerRef.current = window.setTimeout(() => {
      bootstrapRetryTimerRef.current = null
      if (!mountedRef.current || !isActiveSessionVersion(sessionVersion)) return
      if (!useAccountStore.getState().profile) return
      void bootstrap()
    }, delay)
  }, [clearBootstrapRetryTimer, clearSession, isActiveSessionVersion, refreshPackages, refreshProfile, refreshSettings])

  useEffect(() => {
    bumpSessionVersion()
    bootstrappedRef.current = false
    bootstrapRetryCountRef.current = 0
    refreshInFlightRef.current = false
    clearBootstrapRetryTimer()

    void bootstrap()
  }, [bootstrap, bumpSessionVersion, clearBootstrapRetryTimer])

  useEffect(() => {
    return authBridge.configure({
      getToken: () => useAccountStore.getState().token,
      onAccountSync: (payload) => {
        if (typeof payload.points === 'number') {
          useAccountStore.getState().syncPoints(payload.points)
        }

        if (payload.refreshProfile && !refreshInFlightRef.current) {
          void refreshProfile().catch((err: unknown) => {
            console.error('refreshProfile failed in authBridge', err)
          })
        }
      },
      onAuthFailure: () => {
        if (!useAccountStore.getState().profile) return
        clearBootstrapRetryTimer()
        bumpSessionVersion()
        clearSession()
        setError('登录状态已失效，请重新登录。')
        bootstrappedRef.current = false
        bootstrapRetryCountRef.current = 0
        refreshInFlightRef.current = false
      },
    })
  }, [bumpSessionVersion, clearBootstrapRetryTimer, clearSession, refreshProfile])

  const login = useCallback(async (payload: LoginPayload) => {
    setBusy(true)
    try {
      const result = await loginRequest(payload)
      setSession({ token: result.token, profile: result.user, ledger: result.ledger })
      try {
        const packagesResult = await fetchAccountPackages()
        setPackages(packagesResult.packages)
      } catch (err) {
        console.error('fetchAccountPackages failed in login', err)
        setPackages([])
      }
      setError(null)
      return result
    } catch (nextError) {
      const message = getRequestErrorMessage(nextError, '登录失败，请稍后重试。')
      setError(message)
      throw nextError
    } finally {
      setBusy(false)
    }
  }, [setPackages, setSession])

  const register = useCallback(async (payload: RegisterPayload) => {
    setBusy(true)
    try {
      const result = await registerRequest(payload)
      setSession({ token: result.token, profile: result.user, ledger: result.ledger })
      try {
        const packagesResult = await fetchAccountPackages()
        setPackages(packagesResult.packages)
      } catch (err) {
        console.error('fetchAccountPackages failed in register', err)
        setPackages([])
      }
      setError(null)
      return result
    } catch (nextError) {
      const message = getRequestErrorMessage(nextError, '注册失败，请稍后重试。')
      setError(message)
      throw nextError
    } finally {
      setBusy(false)
    }
  }, [setPackages, setSession])

  const logout = useCallback(async () => {
    try {
      await logoutRequest()
    } finally {
      clearBootstrapRetryTimer()
      bumpSessionVersion()
      clearSession()
      setError(null)
      bootstrappedRef.current = false
      bootstrapRetryCountRef.current = 0
    }
  }, [bumpSessionVersion, clearBootstrapRetryTimer, clearSession])

  const startWeChatRecharge = useCallback(async (packageId: string) => {
    setBusy(true)
    try {
      const result = await createWeChatRechargeOrder({ package_id: packageId })
      setError(null)
      return result
    } catch (nextError) {
      const message = getRequestErrorMessage(nextError, '微信支付下单失败，请稍后重试。')
      setError(message)
      throw nextError
    } finally {
      setBusy(false)
    }
  }, [])

  const refreshWeChatRecharge = useCallback(async (orderId: string) => {
    if (rechargePollInFlightRef.current) {
      throw new Error('recharge poll already in flight')
    }
    rechargePollInFlightRef.current = true
    try {
      const result = await fetchWeChatRechargeOrder(orderId)
      if (result.ledger) {
        setLedger(result.ledger)
      }
      setProfile(result.user)
      return result
    } finally {
      rechargePollInFlightRef.current = false
    }
  }, [setLedger, setProfile])

  const saveSettings = useCallback(async (payload: UpdateAccountSettingsPayload) => {
    setBusy(true)
    try {
      const result = await updateAccountSettings(payload)
      setProfile(result.user)
      setError(null)
      return result
    } catch (nextError) {
      const message = getRequestErrorMessage(nextError, '账户设置保存失败，请稍后重试。')
      setError(message)
      throw nextError
    } finally {
      setBusy(false)
    }
  }, [setProfile])

  return useMemo(() => ({
    token,
    profile,
    ledger,
    packages,
    busy,
    error,
    isAuthenticated: Boolean(profile),
    login,
    register,
    refreshProfile,
    refreshPackages,
    refreshSettings,
    startWeChatRecharge,
    refreshWeChatRecharge,
    saveSettings,
    logout,
  }), [busy, error, ledger, login, logout, packages, profile, refreshPackages, refreshProfile, refreshSettings, refreshWeChatRecharge, register, saveSettings, startWeChatRecharge, token])
}
