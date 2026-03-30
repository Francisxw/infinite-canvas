import { useMemo, useState } from 'react'
import { X } from 'lucide-react'
import { useCanvasDockStore } from '../../stores/canvasDockStore'

function statusChipClass(status: string) {
  if (status === 'done') return 'bg-emerald-500/20 text-emerald-200'
  if (status === 'running') return 'bg-sky-500/20 text-sky-200'
  if (status === 'unsupported') return 'bg-amber-500/20 text-amber-200'
  if (status === 'cancelled') return 'bg-zinc-500/25 text-zinc-200'
  return 'bg-rose-500/20 text-rose-200'
}

export function PanelHistory() {
  const history = useCanvasDockStore((state) => state.history)
  const clearHistory = useCanvasDockStore((state) => state.clearHistory)
  const removeHistory = useCanvasDockStore((state) => state.removeHistory)
  const [historyFilter, setHistoryFilter] = useState<'all' | 'running' | 'problem'>('all')

  const historyMetrics = useMemo(() => {
    const running = history.filter((item) => item.status === 'running').length
    const done = history.filter((item) => item.status === 'done').length
    const problem = history.filter((item) => item.status === 'error' || item.status === 'unsupported').length
    return { running, done, problem }
  }, [history])

  const visibleHistory = useMemo(() => {
    if (historyFilter === 'running') return history.filter((item) => item.status === 'running')
    if (historyFilter === 'problem') return history.filter((item) => item.status === 'error' || item.status === 'unsupported')
    return history
  }, [history, historyFilter])

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <div className="text-xs uppercase tracking-[0.22em] text-white/35">生成记录</div>
        <button
          type="button"
          onClick={clearHistory}
          className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs text-white/70 transition hover:bg-white/[0.08]"
        >
          清空记录
        </button>
      </div>

      <div className="mb-3 grid grid-cols-3 gap-2">
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-white/75">
          进行中: {historyMetrics.running}
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-white/75">
          已完成: {historyMetrics.done}
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-white/75">
          异常/未支持: {historyMetrics.problem}
        </div>
      </div>

      <div className="mb-3 flex items-center gap-2">
        {(['all', 'running', 'problem'] as const).map((filter) => (
          <button
            key={filter}
            type="button"
            onClick={() => setHistoryFilter(filter)}
            className={`rounded-full px-3 py-1 text-xs transition ${
              historyFilter === filter ? 'bg-white/16 text-white' : 'bg-white/[0.05] text-white/65 hover:bg-white/[0.1]'
            }`}
          >
            {filter === 'all' ? '全部' : filter === 'running' ? '进行中' : '问题项'}
          </button>
        ))}
      </div>

      <div className="canvas-scrollbar max-h-80 space-y-2 overflow-y-auto pr-1">
        {visibleHistory.length === 0 ? (
          <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-8 text-sm text-white/45">当前筛选下没有记录</div>
        ) : null}
        {visibleHistory.map((item) => (
          <div key={item.id} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
            <div className="mb-1 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-[11px] text-white/35">
                <span>{item.kind.toUpperCase()}</span>
                <span className={`rounded-full px-2 py-0.5 ${statusChipClass(item.status)}`}>{item.status}</span>
              </div>
              <button
                type="button"
                onClick={() => removeHistory(item.id)}
                className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-white/10 text-white/60 transition hover:bg-white/10 hover:text-white"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
            <div className="line-clamp-2 text-sm text-white/82">{item.prompt}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
