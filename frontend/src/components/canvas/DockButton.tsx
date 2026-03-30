import { NodeTooltip } from '../nodes/flow/common'

type DockButtonProps = {
  label: string
  active?: boolean
  onClick: () => void
  children: React.ReactNode
}

export function DockButton({ label, active, onClick, children }: DockButtonProps) {
  return (
    <NodeTooltip label={label}>
      <button
        type="button"
        aria-label={label}
        title={label}
        onClick={onClick}
        className={`nodrag nopan inline-flex h-11 w-11 items-center justify-center rounded-2xl border transition duration-200 ${
          active
            ? 'border-white/24 bg-white/14 text-white shadow-[0_10px_24px_rgba(0,0,0,0.28)]'
            : 'border-transparent bg-white/[0.04] text-white/70 hover:border-white/12 hover:bg-white/[0.08] hover:text-white'
        }`}
      >
        {children}
      </button>
    </NodeTooltip>
  )
}
