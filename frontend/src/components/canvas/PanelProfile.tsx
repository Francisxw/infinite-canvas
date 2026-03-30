import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Clock3,
  Coins,
  Eye,
  EyeOff,
  KeyRound,
  LogOut,
  ShieldCheck,
  Sparkles,
  UserCircle2,
  Wallet,
} from 'lucide-react'
import { useAccount } from '../../hooks/useAccount'
import { useOpenRouterModels } from '../../hooks/useOpenRouterModels'
import { useRechargePolling } from '../../hooks/useRechargePolling'
import { getRequestErrorMessage } from '../../services/api'
import { PanelProfileAuth } from './PanelProfileAuth'
import { PanelProfileRecharge } from './PanelProfileRecharge'

export function PanelProfile() {
  const account = useAccount()
  const { imageModels, videoModels, loading: modelLoading } = useOpenRouterModels()
  const [profileTab, setProfileTab] = useState<'overview' | 'recharge' | 'ledger' | 'settings'>('overview')
  const [openRouterMode, setOpenRouterMode] = useState<'platform' | 'custom'>('platform')
  const [openRouterApiKey, setOpenRouterApiKey] = useState('')
  const [openRouterTextModel, setOpenRouterTextModel] = useState('')
  const [openRouterImageModel, setOpenRouterImageModel] = useState('')
  const [openRouterVideoModel, setOpenRouterVideoModel] = useState('')
  const [showOpenRouterKey, setShowOpenRouterKey] = useState(false)
  const [rechargeError, setRechargeError] = useState<string | null>(null)

  const openRouterSettings = account.profile?.openrouter

  const textModelOptions = useMemo(
    () =>
      Array.from(
        new Set(
          [
            'google/gemini-2.5-flash',
            'google/gemini-3.1-flash',
            'google/gemini-3-pro',
            openRouterSettings?.preferred_models.text ?? '',
          ].filter(Boolean)
        )
      ),
    [openRouterSettings?.preferred_models.text]
  )

  const imageModelOptions = useMemo(
    () =>
      Array.from(
        new Set([...imageModels.map((item) => item.id), openRouterSettings?.preferred_models.image ?? ''].filter(Boolean))
      ),
    [imageModels, openRouterSettings?.preferred_models.image]
  )

  const videoModelOptions = useMemo(
    () =>
      Array.from(
        new Set([...videoModels.map((item) => item.id), openRouterSettings?.preferred_models.video ?? ''].filter(Boolean))
      ),
    [openRouterSettings?.preferred_models.video, videoModels]
  )

  useEffect(() => {
    setOpenRouterMode(openRouterSettings?.mode ?? 'platform')
    setOpenRouterTextModel(openRouterSettings?.preferred_models.text ?? '')
    setOpenRouterImageModel(openRouterSettings?.preferred_models.image ?? '')
    setOpenRouterVideoModel(openRouterSettings?.preferred_models.video ?? '')
  }, [
    openRouterSettings?.mode,
    openRouterSettings?.preferred_models.image,
    openRouterSettings?.preferred_models.text,
    openRouterSettings?.preferred_models.video,
  ])

  const handlePollError = useCallback((message: string) => {
    console.error('Recharge polling error:', message)
  }, [])

  const { pendingRechargeOrder, setPendingRechargeOrder, refreshOrder, pollingError } = useRechargePolling({
    onError: handlePollError,
  })

  const startRecharge = useCallback(
    async (packageId: string) => {
      setRechargeError(null)
      try {
        const result = await account.startWeChatRecharge(packageId)
        setPendingRechargeOrder({
          order: result.order,
          package: result.package ?? account.packages.find((pkg) => pkg.id === packageId) ?? null,
          codeUrl: result.payment?.code_url ?? result.order.code_url ?? null,
        })
        setProfileTab('recharge')
      } catch (err) {
        const message = getRequestErrorMessage(err, '发起充值失败')
        setRechargeError(message)
        console.error('startRecharge error:', err)
      }
    },
    [account, setPendingRechargeOrder]
  )

  const refreshRechargeStatus = useCallback(async () => {
    try {
      await refreshOrder()
    } catch (err) {
      console.error('refreshRechargeStatus error:', err)
    }
  }, [refreshOrder])

  const saveOpenRouterSettings = useCallback(async () => {
    try {
      const result = await account.saveSettings({
        openrouter_mode: openRouterMode,
        openrouter_api_key: openRouterApiKey.trim() || undefined,
        preferred_models: {
          text: openRouterTextModel || null,
          image: openRouterImageModel || null,
          video: openRouterVideoModel || null,
        },
      })
      setOpenRouterApiKey('')
      setOpenRouterTextModel(result.settings.preferred_models.text ?? '')
      setOpenRouterImageModel(result.settings.preferred_models.image ?? '')
      setOpenRouterVideoModel(result.settings.preferred_models.video ?? '')
      setOpenRouterMode(result.settings.mode)
    } catch (err) {
      console.error('saveOpenRouterSettings error:', err)
    }
  }, [
    account,
    openRouterMode,
    openRouterApiKey,
    openRouterTextModel,
    openRouterImageModel,
    openRouterVideoModel,
  ])

  if (!account.isAuthenticated) {
    return <PanelProfileAuth />
  }

  return (
    <div className="space-y-3">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="text-xs uppercase tracking-[0.22em] text-white/35">个人中心</div>
        <div className="inline-flex rounded-full border border-white/10 bg-white/[0.04] p-1 text-xs text-white/72">
          {(
            [
              ['overview', '总览'],
              ['recharge', '充值'],
              ['ledger', '流水'],
              ['settings', '设置'],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setProfileTab(key)}
              className={`rounded-full px-3 py-1 ${profileTab === key ? 'bg-white/14 text-white' : 'text-white/56 hover:text-white/78'}`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-3 xl:grid-cols-[0.98fr_1.42fr]">
        <div className="space-y-3 rounded-[22px] border border-white/10 bg-white/[0.03] p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white/12 text-white/82">
              <UserCircle2 className="h-7 w-7" />
            </div>
            <div>
              <div className="text-sm text-white/92">{account.profile?.display_name}</div>
              <div className="text-xs text-white/45">{account.profile?.email}</div>
            </div>
          </div>

          <div className="rounded-[22px] border border-amber-400/14 bg-[radial-gradient(circle_at_top,rgba(255,205,112,0.18),rgba(255,255,255,0.03)_66%)] px-4 py-4">
            <div className="mb-1 flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-amber-100/70">
              <Wallet className="h-4 w-4" /> 积分钱包
            </div>
            <div className="flex items-end justify-between gap-3">
              <div>
                <div className="text-3xl font-semibold text-white">{account.profile?.points ?? 0}</div>
                <div className="mt-1 text-xs text-white/55">图像 40 / 文本 25 / 视频 60 积分</div>
              </div>
              <button
                type="button"
                onClick={() => setProfileTab('recharge')}
                className="rounded-full border border-white/12 bg-white/[0.08] px-3 py-1.5 text-xs text-white/82 transition hover:bg-white/[0.14]"
              >
                立即充值
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs text-white/72">
            <button
              type="button"
              onClick={() => setProfileTab('recharge')}
              className="rounded-2xl border border-white/8 bg-white/[0.04] px-3 py-3 text-left transition hover:bg-white/[0.08]"
            >
              <div className="mb-1 flex items-center gap-2 text-white/86">
                <Coins className="h-4 w-4 text-amber-300" /> 充值订单
              </div>
              <div className="text-white/55">套餐购买与扫码支付集中管理</div>
            </button>
            <button
              type="button"
              onClick={() => setProfileTab('ledger')}
              className="rounded-2xl border border-white/8 bg-white/[0.04] px-3 py-3 text-left transition hover:bg-white/[0.08]"
            >
              <div className="mb-1 flex items-center gap-2 text-white/86">
                <Clock3 className="h-4 w-4 text-sky-300" /> 积分流水
              </div>
              <div className="text-white/55">查看消费、退款与到账明细</div>
            </button>
            <button
              type="button"
              onClick={() => setProfileTab('settings')}
              className="rounded-2xl border border-white/8 bg-white/[0.04] px-3 py-3 text-left transition hover:bg-white/[0.08]"
            >
              <div className="mb-1 flex items-center gap-2 text-white/86">
                <KeyRound className="h-4 w-4 text-emerald-300" /> OpenRouter
              </div>
              <div className="text-white/55">托管 / 自定义密钥与默认模型</div>
            </button>
            <button
              type="button"
              onClick={() => void account.logout()}
              className="rounded-2xl border border-white/8 bg-white/[0.04] px-3 py-3 text-left transition hover:bg-white/[0.08]"
            >
              <div className="mb-1 flex items-center gap-2 text-white/86">
                <LogOut className="h-4 w-4 text-white/75" /> 退出登录
              </div>
              <div className="text-white/55">结束当前浏览器中的会话</div>
            </button>
          </div>
        </div>

        <div className="rounded-[22px] border border-white/10 bg-white/[0.03] p-4">
          {account.error ? (
            <div className="mb-3 rounded-2xl border border-rose-500/20 bg-rose-500/10 px-3 py-2 text-xs text-rose-100/85">{account.error}</div>
          ) : null}

          {profileTab === 'overview' ? (
            <div className="grid gap-3 lg:grid-cols-[1.08fr_0.92fr]">
              <div className="space-y-3">
                <div className="rounded-[20px] border border-white/10 bg-white/[0.04] p-4">
                  <div className="mb-2 flex items-center gap-2 text-sm text-white/88">
                    <Coins className="h-4 w-4 text-amber-300" /> 使用说明
                  </div>
                  <div className="space-y-2 text-sm text-white/62">
                    <div>• 画布中的图像、文本、视频节点会按类型实时扣除积分。</div>
                    <div>• 失败或取消的请求会自动退款，流水中可查看余额变化。</div>
                    <div>• 个人配置仅影响新建节点，不会强制覆盖已经存在的节点。</div>
                  </div>
                </div>
                <div className="grid gap-2 md:grid-cols-3">
                  {(account.packages.length > 0 ? account.packages.slice(0, 3) : []).map((pkg) => (
                    <button
                      key={pkg.id}
                      type="button"
                      onClick={() => startRecharge(pkg.id)}
                      className="rounded-[20px] border border-white/10 bg-white/[0.04] p-3 text-left transition hover:bg-white/[0.08]"
                    >
                      <div className="mb-2 flex items-center justify-between gap-2">
                        <div className="text-sm text-white/88">{pkg.label}</div>
                        <div className="rounded-full bg-emerald-400/14 px-2 py-1 text-[11px] text-emerald-100/82">
                          +{pkg.total_credits}
                        </div>
                      </div>
                      <div className="text-xs text-white/52">
                        基础 {pkg.credits} / 赠送 {pkg.bonus_credits}
                      </div>
                      <div className="mt-3 text-xl font-semibold text-white">¥{pkg.price_cny}</div>
                    </button>
                  ))}
                </div>
              </div>
              <div className="space-y-3">
                <div className="rounded-[20px] border border-white/10 bg-white/[0.04] px-4 py-4 text-sm text-white/78">
                  <div className="mb-2 flex items-center gap-2 text-white/88">
                    <KeyRound className="h-4 w-4 text-sky-300" /> 当前配置
                  </div>
                  <div className="space-y-2 text-xs text-white/58">
                    <div>
                      模型模式：{openRouterSettings?.mode === 'custom' ? '自定义 OpenRouter' : '平台托管'}
                    </div>
                    <div>文本默认：{openRouterSettings?.preferred_models.text ?? '跟随系统'}</div>
                    <div>图像默认：{openRouterSettings?.preferred_models.image ?? '跟随系统'}</div>
                    <div>视频默认：{openRouterSettings?.preferred_models.video ?? '跟随系统'}</div>
                  </div>
                </div>
                <div className="rounded-[20px] border border-white/10 bg-white/[0.04] px-4 py-4 text-sm text-white/78">
                  <div className="mb-2 flex items-center gap-2 text-white/88">
                    <ShieldCheck className="h-4 w-4 text-emerald-300" /> 账户安全
                  </div>
                  <div className="text-white/55">
                    充值流程已切到微信支付 Native 订单模式；上线前请配置商户证书、APIv3 Key 与 HTTPS 回调地址。
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          {profileTab === 'recharge' ? (
            <PanelProfileRecharge
              account={account}
              pendingRechargeOrder={pendingRechargeOrder}
              setPendingRechargeOrder={setPendingRechargeOrder}
              startRecharge={startRecharge}
              refreshRechargeStatus={refreshRechargeStatus}
              rechargeError={rechargeError}
              pollingError={pollingError}
            />
          ) : null}

          {profileTab === 'ledger' ? (
            <div className="rounded-[22px] border border-white/10 bg-white/[0.03] p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-white/40">
                <Clock3 className="h-4 w-4" /> 积分流水
              </div>
              <div className="canvas-scrollbar max-h-[420px] space-y-2 overflow-y-auto pr-1">
                {account.ledger.length === 0 ? (
                  <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-8 text-sm text-white/45">暂无积分流水</div>
                ) : null}
                {account.ledger.map((entry) => (
                  <div key={entry.id} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                    <div className="mb-1 flex items-center justify-between gap-3">
                      <div className="text-sm text-white/84">{entry.description}</div>
                      <div
                        className={`rounded-full px-2 py-1 text-[11px] ${
                          entry.amount >= 0 ? 'bg-emerald-500/18 text-emerald-100/82' : 'bg-amber-500/18 text-amber-100/82'
                        }`}
                      >
                        {entry.amount >= 0 ? `+${entry.amount}` : entry.amount}
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-white/42">
                      <span>{entry.type}</span>
                      <span>余额 {entry.balance_after}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {profileTab === 'settings' ? (
            <div className="space-y-3">
              <div className="rounded-[22px] border border-white/10 bg-white/[0.03] px-4 py-4 text-sm text-white/78">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div>
                    <div className="mb-2 flex items-center gap-2 text-white/88">
                      <KeyRound className="h-4 w-4 text-sky-300" /> OpenRouter 自定义配置
                    </div>
                    <div className="text-white/55">
                      可继续使用平台托管密钥，也可以切换为你自己的 OpenRouter 账户与默认模型。
                    </div>
                  </div>
                  <div
                    className={`rounded-full px-3 py-1 text-[11px] ${
                      openRouterSettings?.mode === 'custom'
                        ? 'bg-sky-500/18 text-sky-100/85'
                        : 'bg-white/10 text-white/62'
                    }`}
                  >
                    {openRouterSettings?.mode === 'custom' ? '使用自定义配置' : '使用平台托管'}
                  </div>
                </div>

                <div className="mb-3 grid grid-cols-2 gap-2 rounded-[20px] border border-white/8 bg-[#12151a]/86 p-2 text-xs">
                  <button
                    type="button"
                    onClick={() => setOpenRouterMode('platform')}
                    className={`rounded-2xl px-3 py-3 text-left transition ${
                      openRouterMode === 'platform' ? 'bg-white/12 text-white' : 'text-white/60 hover:bg-white/[0.06]'
                    }`}
                  >
                    <div className="mb-1 font-medium">平台托管</div>
                    <div className="text-[11px] text-white/48">直接沿用当前系统内置 OpenRouter Key。</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setOpenRouterMode('custom')}
                    className={`rounded-2xl px-3 py-3 text-left transition ${
                      openRouterMode === 'custom'
                        ? 'bg-sky-500/14 text-white'
                        : 'text-white/60 hover:bg-white/[0.06]'
                    }`}
                  >
                    <div className="mb-1 font-medium">我的 OpenRouter</div>
                    <div className="text-[11px] text-white/48">使用你自己的额度、模型权限和账单。</div>
                  </button>
                </div>

                <div className="mb-3 rounded-[20px] border border-amber-400/14 bg-[radial-gradient(circle_at_top,rgba(255,205,112,0.12),rgba(255,255,255,0.03)_72%)] px-4 py-3 text-xs text-white/68">
                  <div className="mb-1 flex items-center gap-2 text-amber-100/82">
                    <Sparkles className="h-3.5 w-3.5" /> 安全提示
                  </div>
                  <div>
                    自定义密钥只会在你保存时上传，服务器仅保留加密后的副本；如果密钥泄露，请到 OpenRouter 控制台立即重建。
                  </div>
                </div>

                <div className="space-y-3 rounded-[20px] border border-white/8 bg-[#12151a]/78 p-3">
                  <label className="block text-xs text-white/52">
                    OpenRouter API Key
                    <div className="mt-1 flex items-center gap-2 rounded-2xl border border-white/10 bg-[#14171d] px-3 py-2">
                      <input
                        type={showOpenRouterKey ? 'text' : 'password'}
                        value={openRouterApiKey}
                        onChange={(event) => setOpenRouterApiKey(event.target.value)}
                        placeholder={openRouterSettings?.key_mask ?? 'sk-or-v1-xxxxxxxxxxxxxxxx'}
                        className="w-full bg-transparent text-sm text-white outline-none placeholder:text-white/24"
                      />
                      <button
                        type="button"
                        onClick={() => setShowOpenRouterKey((current) => !current)}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-white/10 text-white/60 transition hover:bg-white/8 hover:text-white/84"
                      >
                        {showOpenRouterKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                    <div className="mt-1 text-[11px] text-white/38">
                      留空表示保留已保存密钥；切回平台托管不会删除已保存的自定义密钥。
                    </div>
                  </label>

                  <div className="grid gap-3 md:grid-cols-3">
                    <label className="block text-xs text-white/52">
                      文本默认模型
                      <select
                        value={openRouterTextModel}
                        onChange={(event) => setOpenRouterTextModel(event.target.value)}
                        className="mt-1 w-full rounded-2xl border border-white/10 bg-[#14171d] px-3 py-2 text-sm text-white outline-none"
                      >
                        <option value="">跟随系统默认</option>
                        {textModelOptions.map((modelId) => (
                          <option key={modelId} value={modelId}>{modelId}</option>
                        ))}
                      </select>
                    </label>
                    <label className="block text-xs text-white/52">
                      图像默认模型
                      <select
                        value={openRouterImageModel}
                        onChange={(event) => setOpenRouterImageModel(event.target.value)}
                        className="mt-1 w-full rounded-2xl border border-white/10 bg-[#14171d] px-3 py-2 text-sm text-white outline-none"
                      >
                        <option value="">跟随系统默认</option>
                        {imageModelOptions.map((modelId) => (
                          <option key={modelId} value={modelId}>{modelId}</option>
                        ))}
                      </select>
                    </label>
                    <label className="block text-xs text-white/52">
                      视频默认模型
                      <select
                        value={openRouterVideoModel}
                        onChange={(event) => setOpenRouterVideoModel(event.target.value)}
                        className="mt-1 w-full rounded-2xl border border-white/10 bg-[#14171d] px-3 py-2 text-sm text-white outline-none"
                      >
                        <option value="">跟随系统默认</option>
                        {videoModelOptions.map((modelId) => (
                          <option key={modelId} value={modelId}>{modelId}</option>
                        ))}
                      </select>
                    </label>
                  </div>
                  <div className="text-[11px] text-white/38">
                    保存后，只会影响对应类型的新建节点；已存在节点不会被强制改写。
                    {modelLoading ? ' 正在同步模型列表…' : ''}
                  </div>

                  <div className="flex items-center justify-between gap-3">
                    <div className="text-[11px] text-white/40">
                      {openRouterSettings?.has_custom_key
                        ? `已保存密钥：${openRouterSettings.key_mask ?? '已配置'}`
                        : '当前未保存自定义密钥'}
                    </div>
                    <button
                      type="button"
                      disabled={
                        account.busy ||
                        (openRouterMode === 'custom' && !openRouterSettings?.has_custom_key && !openRouterApiKey.trim())
                      }
                      onClick={saveOpenRouterSettings}
                      className="rounded-2xl border border-white/14 bg-[linear-gradient(120deg,#f4f6fb,#c2c8d3)] px-4 py-2 text-sm font-medium text-[#0d0f13] transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      保存配置
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
