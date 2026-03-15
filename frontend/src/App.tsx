import { Languages } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { TldrawCanvas } from './components/canvas/TldrawCanvas'

function App() {
  const { i18n, t } = useTranslation()
  const isZh = i18n.language.startsWith('zh')

  const toggleLanguage = async () => {
    await i18n.changeLanguage(isZh ? 'en' : 'zh')
  }

  return (
    <div className="h-screen w-screen bg-canvas-bg text-white">
      <header className="pointer-events-none absolute right-4 top-4 z-30 flex items-center gap-2 rounded-lg border border-node-border bg-node-bg/85 px-2.5 py-1.5 shadow backdrop-blur">
        <span className="text-sm font-medium">{t('app.title')}</span>
        <button
          type="button"
          onClick={toggleLanguage}
          className="pointer-events-auto inline-flex items-center gap-1.5 rounded-md border border-node-border px-2 py-1 text-xs text-gray-200 transition hover:bg-white/5"
        >
          <Languages className="h-3.5 w-3.5" />
          {isZh ? 'EN' : '中文'}
        </button>
      </header>
      <TldrawCanvas />
    </div>
  )
}

export default App
