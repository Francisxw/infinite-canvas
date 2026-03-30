import { useMemo, useState } from 'react'
import { Search, Trash2 } from 'lucide-react'
import { useCanvasDockStore } from '../../stores/canvasDockStore'

export function PanelAssets() {
  const assets = useCanvasDockStore((state) => state.assets)
  const clearAssets = useCanvasDockStore((state) => state.clearAssets)
  const removeAsset = useCanvasDockStore((state) => state.removeAsset)
  const [assetFilter, setAssetFilter] = useState<'all' | 'image' | 'video' | 'text'>('all')
  const [searchKeyword, setSearchKeyword] = useState('')

  const visibleAssets = useMemo(() => {
    const byType = assetFilter === 'all' ? assets : assets.filter((asset) => asset.kind === assetFilter)
    const normalizedKeyword = searchKeyword.trim().toLowerCase()
    if (!normalizedKeyword) return byType
    return byType.filter((asset) => asset.name.toLowerCase().includes(normalizedKeyword))
  }, [assetFilter, assets, searchKeyword])

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <div className="text-xs uppercase tracking-[0.22em] text-white/35">资产文件管理</div>
        <button
          type="button"
          onClick={clearAssets}
          className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs text-white/70 transition hover:bg-white/[0.08]"
        >
          清空资产
        </button>
      </div>

      <div className="mb-3 flex items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.03] px-3 py-2">
        <Search className="h-4 w-4 text-white/45" />
        <input
          value={searchKeyword}
          onChange={(event) => setSearchKeyword(event.target.value)}
          placeholder="搜索资产名称"
          className="nodrag nopan w-full bg-transparent text-sm text-white/85 outline-none placeholder:text-white/35"
        />
      </div>

      <div className="mb-3 flex items-center gap-2">
        {(['all', 'image', 'video', 'text'] as const).map((filter) => (
          <button
            key={filter}
            type="button"
            onClick={() => setAssetFilter(filter)}
            className={`rounded-full px-3 py-1 text-xs transition ${
              assetFilter === filter ? 'bg-white/16 text-white' : 'bg-white/[0.05] text-white/65 hover:bg-white/[0.1]'
            }`}
          >
            {filter === 'all' ? '全部' : filter.toUpperCase()}
          </button>
        ))}
      </div>

      <div className="canvas-scrollbar grid max-h-80 grid-cols-2 gap-2 overflow-y-auto pr-1">
        {visibleAssets.length === 0 ? (
          <div className="col-span-2 rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-8 text-sm text-white/45">没有匹配资产</div>
        ) : null}
        {visibleAssets.map((asset) => (
          <div key={asset.id} className="rounded-2xl border border-white/8 bg-white/[0.03] p-3">
            <div className="mb-2 flex items-center justify-between">
              <span className="rounded-full bg-white/10 px-2 py-0.5 text-[11px] text-white/75">{asset.kind.toUpperCase()}</span>
              <button
                type="button"
                onClick={() => removeAsset(asset.id)}
                className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-white/10 text-white/60 transition hover:bg-white/10 hover:text-white"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
            <div className="mb-2 truncate text-sm text-white/84">{asset.name}</div>
            {asset.url ? (
              <a
                href={asset.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex rounded-full border border-white/10 bg-white/[0.06] px-3 py-1 text-xs text-white/75 transition hover:bg-white/[0.12]"
              >
                打开资源
              </a>
            ) : (
              <div className="text-xs text-white/35">无预览链接</div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
