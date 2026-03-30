import { Clock3, FolderOpen, Plus, UserCircle2 } from 'lucide-react'
import { NODE_CREATION_ITEMS } from './nodeCreationConfig'
import { useCanvasDockStore, type DockPanel } from '../../stores/canvasDockStore'
import { DockButton } from './DockButton'
import { PanelHistory } from './PanelHistory'
import { PanelAssets } from './PanelAssets'
import { PanelProfile } from './PanelProfile'

type CanvasDockProps = {
  onCreateText: () => void
  onCreateImage: () => void
  onCreateVideo: () => void
}

function Panel({ panel }: { panel: DockPanel }) {
  if (!panel || panel === 'create') return null

  return (
    <div className="pointer-events-none fixed bottom-24 left-1/2 z-50 -translate-x-1/2">
      <div className="pointer-events-auto w-[min(78vw,860px)] rounded-[26px] p-4 glass-panel">
        {panel === 'history' ? <PanelHistory /> : null}
        {panel === 'assets' ? <PanelAssets /> : null}
        {panel === 'profile' ? <PanelProfile /> : null}
      </div>
    </div>
  )
}

export function CanvasDock({ onCreateText, onCreateImage, onCreateVideo }: CanvasDockProps) {
  const activePanel = useCanvasDockStore((state) => state.activePanel)
  const setActivePanel = useCanvasDockStore((state) => state.setActivePanel)

  const toggle = (panel: DockPanel) => {
    setActivePanel(activePanel === panel ? null : panel)
  }

  return (
    <>
      {activePanel ? (
        <button
          type="button"
          className="fixed inset-0 z-40 cursor-default"
          onClick={() => setActivePanel(null)}
        />
      ) : null}

      <Panel panel={activePanel} />

      <div className="pointer-events-none fixed bottom-5 left-1/2 z-50 -translate-x-1/2">
        <div className="pointer-events-auto flex items-center gap-2 rounded-[28px] px-3 py-3 glass-panel">
          <DockButton label="新建节点" active={activePanel === 'create'} onClick={() => toggle('create')}>
            <Plus className="h-5 w-5" />
          </DockButton>
          <DockButton label="生成记录" active={activePanel === 'history'} onClick={() => toggle('history')}>
            <Clock3 className="h-5 w-5" />
          </DockButton>
          <DockButton label="资产文件管理" active={activePanel === 'assets'} onClick={() => toggle('assets')}>
            <FolderOpen className="h-5 w-5" />
          </DockButton>
          <DockButton label="个人中心" active={activePanel === 'profile'} onClick={() => toggle('profile')}>
            <UserCircle2 className="h-5 w-5" />
          </DockButton>
        </div>
      </div>

      {activePanel === 'create' ? (
        <div
          data-testid="dock-create-panel"
          className="pointer-events-none fixed bottom-24 left-1/2 z-50 -translate-x-1/2"
        >
          <div className="pointer-events-auto flex min-w-[320px] gap-2 rounded-[24px] p-3 glass-panel">
            {NODE_CREATION_ITEMS.map((item) => {
              const onCreate =
                item.type === 'text-node' ? onCreateText : item.type === 'image-node' ? onCreateImage : onCreateVideo

              return (
                <button
                  key={item.type}
                  data-testid={item.dockTestId}
                  aria-label={item.dockAriaLabel}
                  title={`创建${item.label}节点`}
                  type="button"
                  onClick={() => {
                    onCreate()
                    setActivePanel(null)
                  }}
                  className="flex-1 rounded-2xl border border-white/8 bg-white/[0.04] px-4 py-4 text-sm text-white/86 transition hover:bg-white/[0.08]"
                >
                  {item.label}
                </button>
              )
            })}
          </div>
        </div>
      ) : null}
    </>
  )
}
