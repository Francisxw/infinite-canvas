import { FlowCanvas } from './components/canvas/FlowCanvas'

function App() {
  return (
    <div className="relative h-screen w-screen overflow-hidden bg-canvas-bg text-white">
      <div className="pointer-events-none absolute inset-0 z-0 opacity-70">
        <div className="absolute -left-20 -top-20 h-80 w-80 rounded-full bg-[radial-gradient(circle_at_center,rgba(122,156,255,0.35),transparent_68%)] blur-2xl" />
        <div className="absolute right-[-120px] top-[-90px] h-96 w-96 rounded-full bg-[radial-gradient(circle_at_center,rgba(102,196,255,0.28),transparent_70%)] blur-2xl" />
        <div className="absolute bottom-[-130px] left-1/2 h-96 w-[560px] -translate-x-1/2 rounded-full bg-[radial-gradient(circle_at_center,rgba(255,194,140,0.2),transparent_72%)] blur-2xl" />
      </div>
      <FlowCanvas />
    </div>
  )
}

export default App
