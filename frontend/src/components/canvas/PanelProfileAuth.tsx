import { useState } from 'react'
import { Coins, ShieldCheck, UserCircle2 } from 'lucide-react'
import { useAccount } from '../../hooks/useAccount'

export function PanelProfileAuth() {
  const account = useAccount()
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')

  return (
    <div className="grid gap-3 lg:grid-cols-[0.92fr_1.08fr]">
      <div className="space-y-3 rounded-[22px] border border-white/10 bg-white/[0.03] p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-full bg-white/12 text-white/82">
            <UserCircle2 className="h-6 w-6" />
          </div>
          <div>
            <div className="text-sm text-white/90">欢迎来到 Infinite Studio</div>
            <div className="text-xs text-white/45">登录后可管理积分、支付订单和默认模型配置</div>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs text-white/72">
          <div className="rounded-2xl border border-white/8 bg-white/[0.04] px-3 py-3">
            <div className="mb-1 flex items-center gap-2 text-white/86">
              <Coins className="h-4 w-4 text-amber-300" /> 注册奖励
            </div>
            <div className="text-white/55">新账户直接获得 120 积分</div>
          </div>
          <div className="rounded-2xl border border-white/8 bg-white/[0.04] px-3 py-3">
            <div className="mb-1 flex items-center gap-2 text-white/86">
              <ShieldCheck className="h-4 w-4 text-emerald-300" /> 本地会话
            </div>
            <div className="text-white/55">当前浏览器会记住登录状态</div>
          </div>
        </div>
        <div className="rounded-[20px] border border-sky-400/14 bg-[radial-gradient(circle_at_top,rgba(103,232,249,0.12),rgba(255,255,255,0.03)_70%)] px-4 py-3 text-xs text-white/68">
          账户中心已整合充值订单、积分流水和 OpenRouter 偏好设置，正式上线前仍需补齐微信支付商户参数与回调 HTTPS 地址。
        </div>
      </div>

      <div className="rounded-[22px] border border-white/10 bg-white/[0.03] p-4">
        <div className="mb-3 flex items-center justify-between gap-2">
          <div className="inline-flex rounded-full border border-white/10 bg-white/[0.04] p-1 text-xs text-white/72">
            <button
              type="button"
              onClick={() => setAuthMode('login')}
              className={`rounded-full px-3 py-1 ${authMode === 'login' ? 'bg-white/14 text-white' : 'text-white/56'}`}
            >
              登录
            </button>
            <button
              type="button"
              onClick={() => setAuthMode('register')}
              className={`rounded-full px-3 py-1 ${authMode === 'register' ? 'bg-white/14 text-white' : 'text-white/56'}`}
            >
              注册
            </button>
          </div>
          {account.busy ? <div className="text-xs text-white/42">处理中…</div> : null}
        </div>

        <div className="space-y-2.5">
          {authMode === 'register' ? (
            <label className="block text-xs text-white/52">
              昵称
              <input
                value={displayName}
                onChange={(event) => setDisplayName(event.target.value)}
                className="mt-1 w-full rounded-2xl border border-white/10 bg-[#14171d] px-3 py-2 text-sm text-white outline-none placeholder:text-white/24"
                placeholder="输入显示名称"
              />
            </label>
          ) : null}
          <label className="block text-xs text-white/52">
            邮箱
            <input
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-1 w-full rounded-2xl border border-white/10 bg-[#14171d] px-3 py-2 text-sm text-white outline-none placeholder:text-white/24"
              placeholder="name@example.com"
            />
          </label>
          <label className="block text-xs text-white/52">
            密码
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-1 w-full rounded-2xl border border-white/10 bg-[#14171d] px-3 py-2 text-sm text-white outline-none placeholder:text-white/24"
              placeholder="至少 6 位"
            />
          </label>
          
          {account.error ? (
            <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 px-3 py-2 text-xs text-rose-100/85">{account.error}</div>
          ) : null}
          
          <button
            type="button"
            disabled={account.busy}
            onClick={() => {
              if (authMode === 'register') {
                void account.register({ email, password, display_name: displayName })
                return
              }
              void account.login({ email, password })
            }}
            className="w-full rounded-2xl border border-white/14 bg-[linear-gradient(120deg,#f4f6fb,#c2c8d3)] px-4 py-2.5 text-sm font-medium text-[#0d0f13] transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {authMode === 'register' ? '创建账户并进入工作台' : '登录并继续创作'}
          </button>
          <div className="text-[11px] text-white/34">支持邮箱登录、注册即送积分、订单状态自动轮询与到账同步。</div>
        </div>
      </div>
    </div>
  )
}
