import type { ReactNode } from 'react'
import type { IndexKey, TLHandle } from 'tldraw'

export function NodeFrame({
  title,
  icon,
  children,
}: {
  title: string
  icon: ReactNode
  children: ReactNode
}) {
  return (
    <div className="flex h-full w-full flex-col text-gray-200" style={{ pointerEvents: 'all' }}>
      <div className="mb-2 flex items-center gap-2 px-1 text-base">
        <span className="inline-flex h-4 w-4 items-center justify-center text-gray-400">{icon}</span>
        <span>{title}</span>
      </div>
      <div className="min-h-0 flex-1">{children}</div>
    </div>
  )
}

export function RoundedCard({ children }: { children: ReactNode }) {
  return (
    <div className="relative h-full w-full rounded-3xl border border-white/35 bg-[#1f1f1f]/95 p-4 shadow-[0_10px_40px_rgba(0,0,0,0.45)]">
      {children}
      <button
        type="button"
        aria-hidden="true"
        className="pointer-events-none absolute -left-12 top-1/2 inline-flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full border border-white/30 bg-[#1f1f1f]/80 text-lg text-white/80"
      >
        +
      </button>
      <button
        type="button"
        aria-hidden="true"
        className="pointer-events-none absolute -right-12 top-1/2 inline-flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full border border-white/30 bg-[#1f1f1f]/80 text-lg text-white/80"
      >
        +
      </button>
    </div>
  )
}

export function getBoxPortHandles(width: number, height: number): TLHandle[] {
  return [
    { id: 'top', index: 'a1' as IndexKey, type: 'vertex', x: width / 2, y: 0 },
    { id: 'right', index: 'a2' as IndexKey, type: 'vertex', x: width, y: height / 2 },
    { id: 'bottom', index: 'a3' as IndexKey, type: 'vertex', x: width / 2, y: height },
    { id: 'left', index: 'a4' as IndexKey, type: 'vertex', x: 0, y: height / 2 },
  ]
}
