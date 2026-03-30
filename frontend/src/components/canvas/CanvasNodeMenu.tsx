import { NODE_CREATION_ITEMS } from './nodeCreationConfig'
import type { FlowNodeType } from '../nodes/flow/types'

type CanvasNodeMenuProps = {
  position: { x: number; y: number }
  onCreate: (type: FlowNodeType) => void
  dataTestId?: string
}

export function CanvasNodeMenu({ position, onCreate, dataTestId }: CanvasNodeMenuProps) {
  return (
    <div
      data-testid={dataTestId}
      className="absolute z-50 w-56 overflow-hidden rounded-2xl border border-white/10 bg-[#1f1f1f] p-2 shadow-[0_8px_32px_rgba(0,0,0,0.4)]"
      style={{ left: position.x, top: position.y }}
      onMouseDown={(event) => event.stopPropagation()}
    >
      <div className="px-2 py-1.5 text-[11px] text-[#888888]">添加节点</div>
      {NODE_CREATION_ITEMS.map((item) => {
        const Icon = item.icon
        return (
          <button
            key={item.type}
            type="button"
            onClick={() => onCreate(item.type)}
            className="flex w-full items-center gap-3 rounded-xl px-2 py-2.5 text-left transition hover:bg-white/5"
          >
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-[#2d2d2d] text-white/70">
              <Icon className="h-4 w-4" />
            </span>
            <div className="flex flex-col">
              <span className="text-sm text-white/90">{item.label}</span>
              <span className="text-[11px] text-white/40">{item.description}</span>
            </div>
          </button>
        )
      })}
    </div>
  )
}
