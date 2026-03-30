import { useCallback, useEffect, useRef, useState } from 'react'
import { useAccountStore } from '../stores/accountStore'
import type { WeChatRechargeOrderResponse } from '../services/api'

const POLL_INTERVAL_MS = 3000

type UseRechargePollingOptions = {
  onError?: (message: string) => void
}

export function useRechargePolling(options: UseRechargePollingOptions = {}) {
  const { onError } = options
  const pendingRechargeOrder = useAccountStore((state) => state.pendingRechargeOrder)
  const setPendingRechargeOrder = useAccountStore((state) => state.setPendingRechargeOrder)
  const pollInFlightRef = useRef(false)
  const [pollingError, setPollingError] = useState<string | null>(null)

  const refreshOrder = useCallback(async (): Promise<WeChatRechargeOrderResponse | null> => {
    if (!pendingRechargeOrder || pollInFlightRef.current) return null

    pollInFlightRef.current = true
    setPollingError(null)

    try {
      const { fetchWeChatRechargeOrder } = await import('../services/api')
      const result = await fetchWeChatRechargeOrder(pendingRechargeOrder.order.id)

      setPendingRechargeOrder({
        order: result.order,
        package: pendingRechargeOrder.package ?? result.package ?? null,
        codeUrl: pendingRechargeOrder.codeUrl ?? result.order.code_url ?? null,
      })

      return result
    } catch (err) {
      const message = err instanceof Error ? err.message : '刷新订单状态失败'
      setPollingError(message)
      onError?.(message)
      throw err
    } finally {
      pollInFlightRef.current = false
    }
  }, [onError, pendingRechargeOrder, setPendingRechargeOrder])

  useEffect(() => {
    if (!pendingRechargeOrder || pendingRechargeOrder.order.status !== 'pending') return

    const timer = window.setInterval(() => {
      void refreshOrder().catch((err: unknown) => {
        console.error('Recharge polling error:', err)
      })
    }, POLL_INTERVAL_MS)

    return () => window.clearInterval(timer)
  }, [pendingRechargeOrder, refreshOrder])

  return {
    pendingRechargeOrder,
    setPendingRechargeOrder,
    refreshOrder,
    pollingError,
    isPolling: pollInFlightRef.current,
  }
}
