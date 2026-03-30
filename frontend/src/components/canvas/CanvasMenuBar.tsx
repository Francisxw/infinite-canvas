import { Copy, Download, FilePlus2, PencilLine, Redo2, Trash2, Undo2, Upload } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'

type CanvasMenuBarProps = {
  canDeleteSelection: boolean
  canDuplicateSelection: boolean
  notice?: { tone: 'success' | 'error'; message: string } | null
  onClearCanvas: () => void
  onDeleteSelection: () => void
  onDuplicateSelection: () => void
  onExportCanvas: () => void
  onImportCanvas: (file: File) => void
  onNewCanvas: () => void
}

type MenuKey = 'file' | 'edit' | null

type MenuItem = {
  id: string
  label: string
  shortcut?: string
  icon: typeof FilePlus2
  disabled?: boolean
  danger?: boolean
  onSelect: () => void
}

type MenuGroup = {
  key: Exclude<MenuKey, null>
  label: string
  items: MenuItem[]
}

function MenuPanel({ items }: { items: MenuItem[] }) {
  return (
    <div className="absolute left-0 top-[calc(100%+10px)] min-w-[220px] rounded-[18px] p-2 glass-panel">
      <div className="space-y-1">
        {items.map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.id}
              type="button"
              disabled={item.disabled}
              onClick={item.onSelect}
              className={`flex w-full items-center gap-3 rounded-[14px] px-3 py-2 text-left text-xs transition ${
                item.danger
                  ? 'text-rose-100/90 hover:bg-rose-500/10'
                  : 'text-white/82 hover:bg-white/[0.06]'
              } disabled:cursor-not-allowed disabled:opacity-35`}
            >
              <Icon className="h-3.5 w-3.5 shrink-0" />
              <span className="min-w-0 flex-1">{item.label}</span>
              {item.shortcut ? <span className="text-[10px] text-white/34">{item.shortcut}</span> : null}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export function CanvasMenuBar({
  canDeleteSelection,
  canDuplicateSelection,
  notice,
  onClearCanvas,
  onDeleteSelection,
  onDuplicateSelection,
  onExportCanvas,
  onImportCanvas,
  onNewCanvas,
}: CanvasMenuBarProps) {
  const [activeMenu, setActiveMenu] = useState<MenuKey>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    const onWindowPointerDown = (event: PointerEvent) => {
      const target = event.target as Node | null
      if (containerRef.current?.contains(target)) return
      setActiveMenu(null)
    }

    const onWindowKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setActiveMenu(null)
      }
    }

    window.addEventListener('pointerdown', onWindowPointerDown, true)
    window.addEventListener('keydown', onWindowKeyDown)
    return () => {
      window.removeEventListener('pointerdown', onWindowPointerDown, true)
      window.removeEventListener('keydown', onWindowKeyDown)
    }
  }, [])

  useEffect(() => {
    const onWindowKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null
      const isEditable = Boolean(
        target && (
          target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.tagName === 'SELECT' ||
          target.isContentEditable
        )
      )

      if (isEditable) return

      const withPrimaryModifier = event.ctrlKey || event.metaKey

      if (withPrimaryModifier && event.key.toLowerCase() === 'n') {
        event.preventDefault()
        onNewCanvas()
        return
      }

      if (withPrimaryModifier && event.key.toLowerCase() === 'o') {
        event.preventDefault()
        fileInputRef.current?.click()
        return
      }

      if (withPrimaryModifier && event.key.toLowerCase() === 's') {
        event.preventDefault()
        onExportCanvas()
        return
      }

      if (withPrimaryModifier && event.key.toLowerCase() === 'd' && canDuplicateSelection) {
        event.preventDefault()
        onDuplicateSelection()
        return
      }

      if (event.key === 'Delete' && event.shiftKey) {
        event.preventDefault()
        onClearCanvas()
        return
      }

      if (event.key === 'Delete' && canDeleteSelection) {
        event.preventDefault()
        onDeleteSelection()
      }
    }

    window.addEventListener('keydown', onWindowKeyDown)
    return () => window.removeEventListener('keydown', onWindowKeyDown)
  }, [canDeleteSelection, canDuplicateSelection, onClearCanvas, onDeleteSelection, onDuplicateSelection, onExportCanvas, onNewCanvas])

  const closeMenu = () => setActiveMenu(null)

  const groups = useMemo<MenuGroup[]>(() => [
    {
      key: 'file',
      label: '文件',
      items: [
        {
          id: 'new-canvas',
          label: '新建画布',
          shortcut: 'Ctrl+N',
          icon: FilePlus2,
          onSelect: () => {
            onNewCanvas()
            closeMenu()
          },
        },
        {
          id: 'import-json',
          label: '导入 JSON',
          shortcut: 'Ctrl+O',
          icon: Upload,
          onSelect: () => {
            fileInputRef.current?.click()
            closeMenu()
          },
        },
        {
          id: 'export-json',
          label: '导出 JSON',
          shortcut: 'Ctrl+S',
          icon: Download,
          onSelect: () => {
            onExportCanvas()
            closeMenu()
          },
        },
      ],
    },
    {
      key: 'edit',
      label: '编辑',
      items: [
        {
          id: 'duplicate',
          label: '复制所选节点',
          shortcut: 'Ctrl+D',
          icon: Copy,
          disabled: !canDuplicateSelection,
          onSelect: () => {
            onDuplicateSelection()
            closeMenu()
          },
        },
        {
          id: 'delete',
          label: '删除所选',
          shortcut: 'Delete',
          icon: Trash2,
          danger: true,
          disabled: !canDeleteSelection,
          onSelect: () => {
            onDeleteSelection()
            closeMenu()
          },
        },
        {
          id: 'clear-canvas',
          label: '清空画布',
          shortcut: 'Shift+Delete',
          icon: PencilLine,
          danger: true,
          onSelect: () => {
            onClearCanvas()
            closeMenu()
          },
        },
        {
          id: 'undo-placeholder',
          label: '撤销（即将支持）',
          shortcut: 'Ctrl+Z',
          icon: Undo2,
          disabled: true,
          onSelect: closeMenu,
        },
        {
          id: 'redo-placeholder',
          label: '重做（即将支持）',
          shortcut: 'Ctrl+Shift+Z',
          icon: Redo2,
          disabled: true,
          onSelect: closeMenu,
        },
      ],
    },
  ], [canDeleteSelection, canDuplicateSelection, onClearCanvas, onDeleteSelection, onDuplicateSelection, onExportCanvas, onNewCanvas])

  return (
    <div ref={containerRef} className="pointer-events-auto absolute left-4 top-4 z-50 flex items-center gap-1 rounded-[18px] p-1.5 glass-panel">
      <input
        ref={fileInputRef}
        type="file"
        accept="application/json"
        className="hidden"
        onChange={(event) => {
          const file = event.target.files?.[0]
          if (!file) return
          onImportCanvas(file)
          event.target.value = ''
        }}
      />

      {groups.map((group) => (
        <div
          key={group.key}
          className="relative"
          onMouseEnter={() => {
            if (activeMenu) {
              setActiveMenu(group.key)
            }
          }}
        >
          <button
            type="button"
            onClick={() => setActiveMenu((current) => current === group.key ? null : group.key)}
            className={`rounded-[14px] px-3 py-1.5 text-xs font-medium transition ${
              activeMenu === group.key ? 'bg-white/[0.12] text-white' : 'text-white/68 hover:bg-white/[0.06] hover:text-white/88'
            }`}
          >
            {group.label}
          </button>
          {activeMenu === group.key ? <MenuPanel items={group.items} /> : null}
        </div>
      ))}

      {notice ? (
        <div className={`ml-2 rounded-[14px] px-3 py-1.5 text-[11px] ${notice.tone === 'success' ? 'bg-emerald-500/16 text-emerald-100/84' : 'bg-rose-500/14 text-rose-100/84'}`}>
          {notice.message}
        </div>
      ) : null}
    </div>
  )
}
