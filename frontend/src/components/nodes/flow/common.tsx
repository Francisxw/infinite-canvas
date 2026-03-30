import { CheckCheck, Loader, Trash2, Zap } from 'lucide-react'
import { useEffect, useRef, useState, type CSSProperties, type Dispatch, type PointerEvent as ReactPointerEvent, type ReactNode, type SetStateAction } from 'react'
import { Handle, Position, useReactFlow, useUpdateNodeInternals } from '@xyflow/react'
import type { AnyFlowNode, FlowPayload } from './types'
import { useAccountStore } from '../../../stores/accountStore'

export const EMPTY_TEXT_PLACEHOLDER = '双击输入文本，或使用下方 AI 生成'

type NodeShellProps = {
  id: string
  title: string
  icon: ReactNode
  selected: boolean
  width: number
  height: number
  isConnectionCandidate?: boolean
  isConnectionHovered?: boolean
  uploadButton?: ReactNode
  showUploadButton?: boolean
  belowContent?: ReactNode
  children: ReactNode
}

export function FlowNodeShell({
  id,
  title,
  icon,
  selected,
  width,
  height,
  isConnectionCandidate = false,
  isConnectionHovered = false,
  uploadButton,
  showUploadButton = true,
  belowContent,
  children,
}: NodeShellProps) {
  const { deleteElements } = useReactFlow<AnyFlowNode>()
  const updateNodeInternals = useUpdateNodeInternals()
  const shellRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    updateNodeInternals(id)
  }, [height, id, updateNodeInternals, width])

  useEffect(() => {
    if (!shellRef.current || typeof ResizeObserver === 'undefined') return

    const observer = new ResizeObserver(() => {
      updateNodeInternals(id)
    })

    observer.observe(shellRef.current)
    return () => observer.disconnect()
  }, [id, updateNodeInternals])

  const onDelete = () => {
    void deleteElements({ nodes: [{ id }] })
  }

  return (
    <div
      ref={shellRef}
      data-node-id={id}
      data-selected={selected ? 'true' : 'false'}
      data-connection-candidate={isConnectionCandidate ? 'true' : 'false'}
      data-connection-hovered={isConnectionHovered ? 'true' : 'false'}
      className={`group/node relative flex flex-col gap-4 overflow-visible rounded-[28px] bg-transparent px-2 pb-2 pt-1 text-gray-200 transition-all duration-200 ${
        selected
          ? 'drop-shadow-none'
          : 'opacity-[0.94] saturate-[0.92]'
      }`}
      style={{ width, height }}
    >
      <div className="flex items-center justify-between gap-3 px-2 text-sm">
        <div className="flex items-center gap-2 text-white/68">
          <span className="inline-flex h-4 w-4 items-center justify-center text-white/38">{icon}</span>
          <span className={`font-medium tracking-wide ${selected ? 'text-white/80' : 'text-white/58'}`}>{title}</span>
        </div>

        <button
          type="button"
          aria-label={`delete ${title.toLowerCase()} node`}
          onClick={onDelete}
          className="nodrag nopan inline-flex h-7 w-7 items-center justify-center rounded-full border border-white/8 bg-[#141414] text-white/34 opacity-0 shadow-[0_8px_16px_rgba(0,0,0,0.28)] transition hover:border-white/16 hover:bg-[#1a1a1a] hover:text-white/82 group-hover/node:opacity-100"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>

      {uploadButton && showUploadButton ? <div className="pointer-events-none absolute left-1/2 top-0 z-20 -translate-x-1/2 -translate-y-[72%]">{uploadButton}</div> : null}

      <div className="flex-1 overflow-visible">{children}</div>

        {belowContent ? <div className="absolute -left-3 -right-3 top-full z-10 mt-3 origin-top">{belowContent}</div> : null}

    </div>
  )
}

type MediaPortsProps = {
  nodeId: string
  active: boolean
  isConnecting?: boolean
  nodeType: AnyFlowNode['type']
  inputPayloads: FlowPayload[]
  outputPayloads: FlowPayload[]
  selectedInputPayloadIds: string[]
  selectedOutputPayloadIds: string[]
  onToggleInput: (payloadId: string) => void
  onToggleOutput: (payloadId: string) => void
  onSelectAllInputs: () => void
  onSelectAllOutputs: (payloads: FlowPayload[]) => void
}

function PayloadPanel({
  title,
  payloads,
  selectedIds,
  onToggle,
  onSelectAll,
}: {
  title: string
  payloads: FlowPayload[]
  selectedIds: string[]
  onToggle: (payloadId: string) => void
  onSelectAll: () => void
}) {
  return (
    <div className="pointer-events-auto min-w-[180px] max-w-[260px] rounded-[16px] border border-white/10 bg-[#141414]/96 p-2.5 shadow-[0_18px_48px_rgba(0,0,0,0.45)] backdrop-blur-xl">
      <div className="mb-1.5 flex items-center justify-between gap-2">
        <span className="text-[11px] font-medium uppercase tracking-[0.14em] text-white/40">{title}</span>
        <button type="button" onClick={onSelectAll} className="inline-flex items-center gap-1 rounded-full bg-white/8 px-2 py-0.5 text-[10px] text-white/72 transition hover:bg-white/12">
          <CheckCheck className="h-2.5 w-2.5" /> 全选
        </button>
      </div>
      <div className="space-y-1">
        {payloads.length === 0 ? <div className="rounded-lg border border-white/8 bg-white/[0.03] px-2.5 py-2 text-[11px] text-white/40">暂无可用数据</div> : null}
        {payloads.map((payload) => {
          const active = selectedIds.includes(payload.id)
          const canShowImagePreview = Boolean(payload.previewUrl) && payload.kind !== 'video'
          return (
            <button
              key={payload.id}
              type="button"
              onClick={() => onToggle(payload.id)}
              className={`flex w-full items-center gap-2 rounded-xl border px-2 py-1.5 text-left transition ${active ? 'border-white/36 bg-white/14 text-white shadow-[0_0_0_1px_rgba(255,255,255,0.06)]' : 'border-white/6 bg-white/[0.02] text-white/55 hover:bg-white/[0.06] hover:text-white/75'}`}
            >
              {canShowImagePreview ? <img src={payload.previewUrl} alt={payload.label} className="h-7 w-7 rounded-md object-cover" /> : <span className={`inline-flex h-7 w-7 items-center justify-center rounded-md text-[10px] uppercase ${active ? 'bg-white/12 text-white/70' : 'bg-white/6 text-white/45'}`}>{payload.kind}</span>}
              <span className="min-w-0 flex-1 truncate text-xs">{payload.label}</span>
              {active ? <span className="ml-1 h-1.5 w-1.5 rounded-full bg-white/60" /> : null}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export function MediaSidePorts({
  nodeId,
  active,
  isConnecting = false,
  nodeType,
  inputPayloads,
  outputPayloads,
  selectedInputPayloadIds,
  selectedOutputPayloadIds,
  onToggleInput,
  onToggleOutput,
  onSelectAllInputs,
  onSelectAllOutputs,
}: MediaPortsProps) {
  const updateNodeInternals = useUpdateNodeInternals()
  const inputPortRef = useRef<HTMLDivElement | null>(null)
  const outputPortRef = useRef<HTMLDivElement | null>(null)
  const inputPortId = `${nodeType}-input-port`
  const outputPortId = `${nodeType}-output-port`
  const [pinnedPanel, setPinnedPanel] = useState<'input' | 'output' | null>(null)
  const [suppressHoverPanel, setSuppressHoverPanel] = useState<'input' | 'output' | null>(null)
  const pointerStartRef = useRef<{ side: 'input' | 'output'; x: number; y: number } | null>(null)

  useEffect(() => {
    updateNodeInternals(nodeId)
  }, [active, inputPayloads.length, nodeId, outputPayloads.length, selectedInputPayloadIds.length, selectedOutputPayloadIds.length, updateNodeInternals])

  useEffect(() => {
    if (!inputPortRef.current || typeof ResizeObserver === 'undefined') return

    const previewFrame = inputPortRef.current.closest('[data-preview-frame]')
    if (!previewFrame) return

    const observer = new ResizeObserver(() => {
      updateNodeInternals(nodeId)
    })
    observer.observe(previewFrame)
    return () => observer.disconnect()
  }, [nodeId, updateNodeInternals])

  useEffect(() => {
    if (!isConnecting) return
    setPinnedPanel(null)
    setSuppressHoverPanel(null)
  }, [isConnecting])

  useEffect(() => {
    if (!pinnedPanel) return

    const onWindowPointerDown = (event: PointerEvent) => {
      const target = event.target as Node | null
      if (!target) return

      if (inputPortRef.current?.contains(target) || outputPortRef.current?.contains(target)) {
        return
      }

      setPinnedPanel(null)
    }

    const onWindowKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setPinnedPanel(null)
      }
    }

    window.addEventListener('pointerdown', onWindowPointerDown, true)
    window.addEventListener('keydown', onWindowKeyDown)
    return () => {
      window.removeEventListener('pointerdown', onWindowPointerDown, true)
      window.removeEventListener('keydown', onWindowKeyDown)
    }
  }, [pinnedPanel])

  const onPortPointerDown = (side: 'input' | 'output', event: ReactPointerEvent<HTMLDivElement>) => {
    if ((event.target as Element).closest('[data-port-panel="true"]')) return
    pointerStartRef.current = { side, x: event.clientX, y: event.clientY }
  }

  const onPortPointerUp = (side: 'input' | 'output', event: ReactPointerEvent<HTMLDivElement>) => {
    if ((event.target as Element).closest('[data-port-panel="true"]')) return
    const started = pointerStartRef.current
    pointerStartRef.current = null

    if (!started || started.side !== side) return
    const movedDistance = Math.hypot(event.clientX - started.x, event.clientY - started.y)
    if (movedDistance > 6) return

    setPinnedPanel((current) => (current === side ? null : side))
  }

  return (
    <>
      <div
        ref={inputPortRef}
        className="group/port nodrag nopan absolute -left-12 top-1/2 z-30 h-[46px] w-[46px] -translate-y-1/2"
        onPointerDown={onPortPointerDown.bind(null, 'input')}
        onPointerUp={onPortPointerUp.bind(null, 'input')}
        onPointerLeave={() => {
          if (suppressHoverPanel === 'input') {
            setSuppressHoverPanel(null)
          }
        }}
      >
        {!isConnecting ? <div data-port-panel="true" className={`pointer-events-none absolute right-[calc(100%+24px)] top-1/2 z-40 -translate-y-1/2 ${pinnedPanel === 'input' ? 'block' : suppressHoverPanel === 'input' ? 'hidden' : 'hidden group-hover/port:block'}`}>
          <PayloadPanel
            title="输入数据"
            payloads={inputPayloads}
            selectedIds={selectedInputPayloadIds}
            onToggle={onToggleInput}
            onSelectAll={onSelectAllInputs}
          />
        </div> : null}

        <Handle
          id="left-target"
          type="target"
          position={Position.Left}
          aria-label={inputPortId}
          data-testid={inputPortId}
          style={{ top: '50%', left: '50%', transform: 'translate(-50%, -50%)', background: 'transparent', border: 'none', width: 46, height: 46 } as CSSProperties}
          className="nodrag nopan !absolute !flex !h-[46px] !w-[46px] !items-center !justify-center !rounded-full"
        >
          <span
            aria-hidden="true"
            title="输入数据"
            className={`pointer-events-none absolute left-1/2 top-1/2 flex h-[28px] w-[28px] -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border bg-[#101010]/96 text-[18px] font-medium leading-none shadow-[0_12px_28px_rgba(0,0,0,0.46)] ring-1 ring-black/28 transition-all ${
              active ? 'border-white/56 text-white' : 'border-white/38 text-white/92'
            }`}
          >
            +
          </span>
        </Handle>
      </div>

      <div
        ref={outputPortRef}
        className="group/port nodrag nopan absolute -right-12 top-1/2 z-30 h-[46px] w-[46px] -translate-y-1/2"
        onPointerDown={onPortPointerDown.bind(null, 'output')}
        onPointerUp={onPortPointerUp.bind(null, 'output')}
        onPointerLeave={() => {
          if (suppressHoverPanel === 'output') {
            setSuppressHoverPanel(null)
          }
        }}
      >
        {!isConnecting ? <div data-port-panel="true" className={`pointer-events-none absolute left-[calc(100%+20px)] top-1/2 z-40 -translate-y-1/2 ${pinnedPanel === 'output' ? 'block' : suppressHoverPanel === 'output' ? 'hidden' : 'hidden group-hover/port:block'}`}>
          <PayloadPanel
            title="输出数据"
            payloads={outputPayloads}
            selectedIds={selectedOutputPayloadIds}
            onToggle={onToggleOutput}
            onSelectAll={() => onSelectAllOutputs(outputPayloads)}
          />
        </div> : null}

        <Handle
          id="right-source"
          type="source"
          position={Position.Right}
          aria-label={outputPortId}
          data-testid={outputPortId}
          style={{ top: '50%', left: '50%', transform: 'translate(-50%, -50%)', background: 'transparent', border: 'none', width: 46, height: 46 } as CSSProperties}
          className="nodrag nopan !absolute !flex !h-[46px] !w-[46px] !items-center !justify-center !rounded-full"
        >
          <span
            aria-hidden="true"
            title="输出数据"
            className={`pointer-events-none absolute left-1/2 top-1/2 flex h-[28px] w-[28px] -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border bg-[#101010]/96 text-[18px] font-medium leading-none shadow-[0_12px_28px_rgba(0,0,0,0.46)] ring-1 ring-black/28 transition-all ${
              active ? 'border-white/56 text-white' : 'border-white/38 text-white/92'
            }`}
          >
            +
          </span>
        </Handle>
      </div>
    </>
  )
}

type NodeTooltipProps = {
  label: string
  children: ReactNode
}

export function NodeTooltip({ label, children }: NodeTooltipProps) {
  return (
    <div className="group/tooltip relative inline-flex">
      {children}
      <div className="pointer-events-none absolute bottom-[calc(100%+10px)] left-1/2 z-40 -translate-x-1/2 rounded-full border border-white/10 bg-[#0f0f0f]/96 px-2.5 py-1 text-[11px] text-white/76 opacity-0 shadow-[0_10px_24px_rgba(0,0,0,0.32)] backdrop-blur-xl transition duration-150 group-hover/tooltip:opacity-100 whitespace-nowrap">
        {label}
      </div>
    </div>
  )
}

type NodeNoticeProps = {
  message?: string | null
  tone?: 'error' | 'warning'
}

export function NodeNotice({ message, tone = 'error' }: NodeNoticeProps) {
  if (!message) return null

  const palette = tone === 'warning'
    ? 'border-amber-500/20 bg-amber-500/8 text-amber-100/82'
    : 'border-rose-500/20 bg-rose-500/10 text-rose-100/86'

  return (
    <div role={tone === 'error' ? 'alert' : 'status'} className={`rounded-2xl border px-3 py-2 text-xs ${palette}`}>
      {message}
    </div>
  )
}

type GenerateActionButtonProps = {
  label: string
  points: number
  onClick: () => void
  disabled?: boolean
  tone?: 'primary' | 'muted'
  ariaLabel?: string
}

export function GenerateActionButton({
  label,
  points,
  onClick,
  disabled = false,
  tone = 'primary',
  ariaLabel,
}: GenerateActionButtonProps) {
  const profile = useAccountStore((state) => state.profile)
  const isAuthenticated = useAccountStore((state) => Boolean(state.token && state.profile))
  const canAfford = (profile?.points ?? 0) >= points
  const effectiveDisabled = disabled || !isAuthenticated || !canAfford
  const toneClass = tone === 'primary'
    ? 'border-white/16 bg-[linear-gradient(120deg,#e8eaee,#b9bdc5)] text-[#0d0f13] hover:brightness-105'
    : 'border-white/12 bg-white/10 text-white/84 hover:bg-white/14'

  return (
    <button
      type="button"
      aria-label={ariaLabel ?? label}
      onClick={onClick}
      disabled={effectiveDisabled}
      title={!isAuthenticated ? '请先登录账号' : canAfford ? undefined : '积分不足，请先充值'}
      className={`nodrag nopan inline-flex h-10 items-center gap-2 rounded-full border px-4 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-45 ${toneClass}`}
    >
      <span className="inline-flex items-center gap-1.5">
        <Zap className="h-3.5 w-3.5" />
        <span>{label}</span>
      </span>
      <span className={`rounded-full px-2 py-0.5 text-[11px] ${tone === 'primary' ? 'bg-black/14 text-[#0d0f13]' : 'bg-black/20 text-white/86'}`}>
        {points}
      </span>
    </button>
  )
}

type GenerationProgressProps = {
  active?: boolean
  label?: string
}

export function GenerationProgress({ active = false, label = '生成中…' }: GenerationProgressProps) {
  if (!active) return null

  return (
    <div className="pointer-events-none absolute inset-0 z-20 overflow-hidden rounded-[inherit]">
      <div className="absolute inset-x-0 top-0 h-full bg-[linear-gradient(90deg,transparent_0%,rgba(255,255,255,0.04)_15%,rgba(255,255,255,0.18)_48%,rgba(255,255,255,0.04)_82%,transparent_100%)] animate-[scanline_1.8s_linear_infinite]" />
      <div className="absolute inset-x-5 bottom-4 h-1.5 overflow-hidden rounded-full bg-white/8">
        <div className="h-full w-1/3 rounded-full bg-[linear-gradient(90deg,rgba(255,255,255,0.18),rgba(255,255,255,0.9),rgba(255,255,255,0.18))] animate-[scanbar_1.4s_ease-in-out_infinite]" />
      </div>
      <div className="absolute left-5 top-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/35 px-3 py-1 text-[11px] text-white/82 backdrop-blur-md">
        <Loader className="h-3.5 w-3.5 animate-spin" />
        <span>{label}</span>
      </div>
    </div>
  )
}

export function patchNodeData<TNode extends AnyFlowNode>(
  setNodes: Dispatch<SetStateAction<TNode[]>>,
  nodeId: string,
  patch: Partial<TNode['data']>
) {
  setNodes((nodes) =>
    nodes.map((node) => {
      if (node.id !== nodeId) return node
      const patchRecord = patch as Record<string, unknown>
      const nextWidth = typeof patchRecord.w === 'number' ? patchRecord.w : undefined
      const nextHeight = typeof patchRecord.h === 'number' ? patchRecord.h : undefined

      return {
        ...node,
        data: {
          ...node.data,
          ...patch,
        },
        style:
          nextWidth !== undefined || nextHeight !== undefined
            ? {
                ...node.style,
                ...(nextWidth !== undefined ? { width: nextWidth } : {}),
                ...(nextHeight !== undefined ? { height: nextHeight } : {}),
              }
            : node.style,
      }
    })
  )
}
