import { useEffect, useState } from 'react'
import { CheckCircle2 } from 'lucide-react'
import QRCode from 'qrcode'
import type { AccountPackage, RechargeOrder } from '../../services/api'

type PendingRechargeOrder = {
  order: RechargeOrder
  package: AccountPackage | null
  codeUrl: string | null
}

type PanelProfileRechargeProps = {
  account: {
    packages: AccountPackage[]
    busy: boolean
  }
  pendingRechargeOrder: PendingRechargeOrder | null
  setPendingRechargeOrder: (order: PendingRechargeOrder | null) => void
  startRecharge: (packageId: string) => Promise<void>
  refreshRechargeStatus: () => Promise<void>
  rechargeError: string | null
  pollingError: string | null
}

function paymentStatusLabel(status: string) {
  if (status === 'paid') return '已支付'
  if (status === 'failed') return '支付失败'
  if (status === 'expired') return '已失效'
  return '待支付'
}

export function PanelProfileRecharge({
  account,
  pendingRechargeOrder,
  setPendingRechargeOrder,
  startRecharge,
  refreshRechargeStatus,
  rechargeError,
  pollingError,
}: PanelProfileRechargeProps) {
  const [wechatQrDataUrl, setWechatQrDataUrl] = useState<string | null>(null)

  useEffect(() => {
    const codeUrl = pendingRechargeOrder?.codeUrl ?? pendingRechargeOrder?.order.code_url ?? null
    if (!codeUrl) {
      setWechatQrDataUrl(null)
      return
    }

    let cancelled = false
    void QRCode.toDataURL(codeUrl, {
      margin: 1,
      width: 220,
      color: {
        dark: '#f5f7fb',
        light: '#111214',
      },
    })
      .then((value: string) => {
        if (!cancelled) {
          setWechatQrDataUrl(value)
        }
      })
      .catch((err: unknown) => {
        console.error('QRCode generation failed:', err)
        if (!cancelled) {
          setWechatQrDataUrl(null)
        }
      })

    return () => {
      cancelled = true
    }
  }, [pendingRechargeOrder])

  return (
    <div className="space-y-3">
      <div className="grid gap-3 md:grid-cols-3">
        {(account.packages.length > 0 ? account.packages : []).map((pkg) => (
          <div key={pkg.id} className="rounded-[20px] border border-white/10 bg-white/[0.04] p-4">
            <div className="mb-2 flex items-center justify-between gap-2">
              <div className="text-sm text-white/88">{pkg.label}</div>
              <div className="rounded-full bg-emerald-400/14 px-2 py-1 text-[11px] text-emerald-100/82">
                +{pkg.total_credits}
              </div>
            </div>
            <div className="text-xs text-white/52">
              基础 {pkg.credits} / 赠送 {pkg.bonus_credits}
            </div>
            <div className="mt-4 text-2xl font-semibold text-white">¥{pkg.price_cny}</div>
            <button
              type="button"
              disabled={account.busy}
              onClick={() => void startRecharge(pkg.id)}
              className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-2xl border border-white/12 bg-white/[0.06] px-4 py-2 text-sm text-white/84 transition hover:bg-white/[0.12] disabled:cursor-not-allowed disabled:opacity-55"
            >
              <CheckCircle2 className="h-4 w-4" /> 立即充值
            </button>
          </div>
        ))}
      </div>

      {rechargeError ? (
        <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 px-3 py-2 text-xs text-rose-100/85">{rechargeError}</div>
      ) : null}

      {pollingError ? (
        <div className="rounded-2xl border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-xs text-amber-100/85">轮询错误: {pollingError}</div>
      ) : null}

      {pendingRechargeOrder ? (
        <div className="grid gap-3 rounded-[22px] border border-emerald-400/14 bg-[radial-gradient(circle_at_top,rgba(103,232,249,0.14),rgba(255,255,255,0.03)_70%)] p-4 lg:grid-cols-[220px_1fr]">
          <div className="rounded-[20px] border border-white/10 bg-[#111214] p-3">
            {wechatQrDataUrl ? (
              <img
                src={wechatQrDataUrl}
                alt="wechat pay qr"
                className="mx-auto h-[190px] w-[190px] rounded-2xl"
              />
            ) : (
              <div className="flex h-[190px] items-center justify-center rounded-2xl border border-dashed border-white/12 text-xs text-white/42">等待二维码</div>
            )}
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-sm text-white/88">微信支付订单</div>
                <div className="text-xs text-white/45">订单号 {pendingRechargeOrder.order.out_trade_no}</div>
              </div>
              <div
                className={`rounded-full px-3 py-1 text-xs ${
                  pendingRechargeOrder.order.status === 'paid'
                    ? 'bg-emerald-500/18 text-emerald-100/85'
                    : pendingRechargeOrder.order.status === 'pending'
                      ? 'bg-sky-500/18 text-sky-100/85'
                      : 'bg-amber-500/18 text-amber-100/85'
                }`}
              >
                {paymentStatusLabel(pendingRechargeOrder.order.status)}
              </div>
            </div>
            <div className="grid gap-2 text-sm text-white/74 md:grid-cols-3">
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-3">
                套餐 {pendingRechargeOrder.package?.label ?? pendingRechargeOrder.order.package_id}
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-3">
                金额 ¥{pendingRechargeOrder.order.amount_cny}
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-3">
                到账 {pendingRechargeOrder.order.total_credits} 积分
              </div>
            </div>
            <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-white/66">
              {pendingRechargeOrder.order.status === 'pending'
                ? '请使用微信扫码完成支付，面板会自动轮询并在支付成功后立即到账。'
                : null}
              {pendingRechargeOrder.order.status === 'paid' ? '支付成功，积分已到账。你现在可以直接继续生成内容。' : null}
              {pendingRechargeOrder.order.status === 'failed' ? '支付失败，请重新发起充值订单。' : null}
              {pendingRechargeOrder.order.status === 'expired' ? '订单已失效，请重新发起新的微信支付订单。' : null}
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setPendingRechargeOrder(null)}
                className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-white/72 transition hover:bg-white/[0.08]"
              >
                关闭订单
              </button>
              {pendingRechargeOrder.order.status === 'pending' ? (
                <button
                  type="button"
                  onClick={() => void refreshRechargeStatus()}
                  className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-white/72 transition hover:bg-white/[0.08]"
                >
                  刷新状态
                </button>
              ) : null}
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-[20px] border border-white/8 bg-white/[0.03] px-4 py-8 text-sm text-white/50">
          选择上方套餐即可创建新的微信支付订单。
        </div>
      )}
    </div>
  )
}
