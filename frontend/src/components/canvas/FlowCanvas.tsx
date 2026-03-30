import {
  addEdge,
  Background,
  ConnectionMode,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  type Edge,
  type IsValidConnection,
  type OnConnect,
  type OnEdgesDelete,
  type OnNodesDelete,
  type Viewport,
  useEdgesState,
  useNodesState,
  useReactFlow,
} from '@xyflow/react'
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import '@xyflow/react/dist/style.css'
import { CanvasNodeMenu } from './CanvasNodeMenu'
import { CanvasDock } from './CanvasDock'
import { CanvasMenuBar } from './CanvasMenuBar'
import { isPaneTarget } from './flowConnectionUtils'
import { createFlowNode, createInitialCanvasState } from './flowNodeFactory'
import { attachConnectionHints, isNodeConnectionCompatible, syncNodeInputs } from './flowPayloads'
import { CustomEdge } from '../edges/CustomEdge'
import { ImageNode } from '../nodes/flow/ImageNode'
import { TextNode } from '../nodes/flow/TextNode'
import { VideoNode } from '../nodes/flow/VideoNode'
import type { AnyFlowNode, FlowNodeType } from '../nodes/flow/types'
import { hydrateFlowSnapshot, saveFlowViewport, serializeFlowSnapshot, useFlowPersistence } from '../../hooks/useFlowPersistence'
import { useViewportPersistence } from '../../hooks/useViewportPersistence'
import { useCanvasDockStore } from '../../stores/canvasDockStore'
import { usePendingConnection } from './usePendingConnection'

type MenuPosition = { x: number; y: number }

const nodeTypes = {
  'text-node': TextNode,
  'image-node': ImageNode,
  'video-node': VideoNode,
}

const edgeTypes = {
  custom: CustomEdge,
}

function updateTextNodeSize(node: Extract<AnyFlowNode, { type: 'text-node' }>, width: number, height: number): Extract<AnyFlowNode, { type: 'text-node' }> {
  return {
    ...node,
    data: {
      ...node.data,
      manualSize: true,
      w: width,
      h: height,
    },
    style: {
      ...node.style,
      width,
      height,
    },
  }
}

function updateImageNodeSize(node: Extract<AnyFlowNode, { type: 'image-node' }>, width: number, height: number): Extract<AnyFlowNode, { type: 'image-node' }> {
  return {
    ...node,
    data: {
      ...node.data,
      manualSize: true,
      w: width,
      h: height,
    },
    style: {
      ...node.style,
      width,
      height,
    },
  }
}

function updateVideoNodeSize(node: Extract<AnyFlowNode, { type: 'video-node' }>, width: number, height: number): Extract<AnyFlowNode, { type: 'video-node' }> {
  return {
    ...node,
    data: {
      ...node.data,
      manualSize: true,
      w: width,
      h: height,
    },
    style: {
      ...node.style,
      width,
      height,
    },
  }
}

function duplicateNode(node: AnyFlowNode, index: number): AnyFlowNode {
  const nextId = `${node.type}-${Date.now()}-${index}-${Math.random().toString(36).slice(2, 7)}`

  if (node.type === 'text-node') {
    return {
      ...node,
      id: nextId,
      position: {
        x: node.position.x + 48,
        y: node.position.y + 48,
      },
      selected: false,
      data: {
        ...node.data,
        modelPickerOpen: false,
        settingsOpen: false,
        isEditing: false,
        isConnectionCandidate: false,
        isConnectionHovered: false,
        isConnecting: false,
      },
    }
  }

  if (node.type === 'image-node') {
    return {
      ...node,
      id: nextId,
      position: {
        x: node.position.x + 48,
        y: node.position.y + 48,
      },
      selected: false,
      data: {
        ...node.data,
        modelPickerOpen: false,
        settingsOpen: false,
        quantityOpen: false,
        customCountOpen: false,
        isConnectionCandidate: false,
        isConnectionHovered: false,
        isConnecting: false,
      },
    }
  }

  return {
    ...node,
    id: nextId,
    position: {
      x: node.position.x + 48,
      y: node.position.y + 48,
    },
    selected: false,
    data: {
      ...node.data,
      modelPickerOpen: false,
      settingsOpen: false,
      isConnectionCandidate: false,
      isConnectionHovered: false,
      isConnecting: false,
    },
  }
}

function FlowCanvasInner() {
  const { deleteElements, fitView, getNodes, getViewport, screenToFlowPosition, setViewport, zoomIn, zoomOut } = useReactFlow<AnyFlowNode>()
  const { clearFlow, loadFlow, saveFlow } = useFlowPersistence()
  const history = useCanvasDockStore((state) => state.history)
  const canvasRef = useRef<HTMLDivElement | null>(null)
  const [nodes, setNodes, onNodesChangeBase] = useNodesState<AnyFlowNode>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [contextMenu, setContextMenu] = useState<MenuPosition | null>(null)
  const [hydrated, setHydrated] = useState(false)
  const [menuNotice, setMenuNotice] = useState<{ tone: 'success' | 'error'; message: string } | null>(null)
  const [selectionVersion, setSelectionVersion] = useState(0)
  const initialViewportRef = useRef<Viewport | null>(null)
  const edgesRef = useRef<Edge[]>([])
  const leftDockWidth = 240
  const leftDockInset = 16
  const zoomPanelBottom = 16
  const minimapBottom = 156
  const tasksBottom = 322

  useEffect(() => {
    const snapshot = loadFlow()
    setNodes(snapshot.nodes as AnyFlowNode[])
    setEdges(snapshot.edges)
    initialViewportRef.current = snapshot.viewport ?? null
    setHydrated(true)
  }, [loadFlow])

  useLayoutEffect(() => {
    if (!hydrated) return
    saveFlow(nodes, edges, getViewport())
  }, [edges, getViewport, hydrated, nodes, saveFlow])

  useEffect(() => {
    edgesRef.current = edges
  }, [edges])

  useEffect(() => {
    setSelectionVersion((current) => current + 1)
  }, [edges, nodes])

  useEffect(() => {
    if (!menuNotice) return
    const timer = window.setTimeout(() => setMenuNotice(null), 2600)
    return () => window.clearTimeout(timer)
  }, [menuNotice])

  useEffect(() => {
    setNodes((current) => {
      const next = syncNodeInputs(current, edges)
      return next.changed ? next.nodes : current
    })
  }, [edges, nodes])

  useEffect(() => {
    if (!hydrated) return
    const hasNodes = nodes.length > 0
    const hasEdges = edges.length > 0
    if (hasNodes || hasEdges) return

    const initialState = createInitialCanvasState()
    setNodes(initialState.nodes)
    setEdges(initialState.edges)
  }, [edges.length, hydrated, nodes.length])

  const { onMove, onMoveEnd, setZoomValue, zoomValue } = useViewportPersistence({
    hydrated,
    initialViewport: initialViewportRef.current,
    nodes,
    edges,
    saveViewport: useCallback((currentNodes, currentEdges, viewport) => {
      saveFlowViewport(saveFlow, currentNodes, currentEdges, viewport)
    }, [saveFlow]),
    setViewport,
  })

  const closeMenus = useCallback(() => {
    setContextMenu(null)
  }, [])

  const handleFitView = useCallback(() => {
    void fitView({ duration: 180, padding: 0.2 })
  }, [fitView])

  const appendNodeAtFlowPosition = useCallback((type: FlowNodeType, flowPosition: { x: number; y: number }) => {
    setNodes((current) => {
      const node = createFlowNode(type, flowPosition.x, flowPosition.y, current)
      return [...current, node]
    })
  }, [])

  const appendNodeAtScreenPosition = useCallback((type: FlowNodeType, screenPosition: { x: number; y: number }) => {
    const flowPosition = screenToFlowPosition(screenPosition)
    appendNodeAtFlowPosition(type, flowPosition)
  }, [appendNodeAtFlowPosition, screenToFlowPosition])

  const appendNodeAtViewportCenter = useCallback((type: FlowNodeType) => {
    const bounds = canvasRef.current?.getBoundingClientRect()
    const screenPosition = bounds
      ? {
          x: bounds.left + bounds.width / 2,
          y: bounds.top + bounds.height / 2,
        }
      : {
          x: window.innerWidth / 2,
          y: window.innerHeight / 2,
        }

    appendNodeAtScreenPosition(type, screenPosition)
  }, [appendNodeAtScreenPosition])

  const onCanvasContextMenu = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    if (!isPaneTarget(event.target)) return
    event.preventDefault()
    setContextMenu({ x: event.clientX, y: event.clientY })
  }, [])

  const onCanvasDoubleClick = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    if (!isPaneTarget(event.target)) return
    setContextMenu({ x: event.clientX, y: event.clientY })
  }, [])

  const onCreateNodeAtMenu = useCallback(
    (type: FlowNodeType) => {
      if (!contextMenu) return
      const menuPos = contextMenu
      if (!menuPos) return
      appendNodeAtScreenPosition(type, { x: menuPos.x, y: menuPos.y })
      setContextMenu(null)
    },
    [appendNodeAtScreenPosition, contextMenu]
  )

  const isValidConnection = useCallback<IsValidConnection<Edge>>((connection) => {
    if (!connection.source || !connection.target) return false
    if (connection.source === connection.target) return false
    const sourceNode = nodes.find((node) => node.id === connection.source)
    const targetNode = nodes.find((node) => node.id === connection.target)
    if (!sourceNode || !targetNode) return false

    return isNodeConnectionCompatible(sourceNode, targetNode)
  }, [nodes])

  const onConnect: OnConnect = useCallback(
    (connection) => {
      if (!isValidConnection(connection)) return
      setEdges((current) =>
        addEdge(
          {
            ...connection,
            id: `edge-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
            sourceHandle: connection.sourceHandle ?? 'right-source',
            targetHandle: connection.targetHandle ?? 'left-target',
            type: 'custom',
          },
          current
        )
      )
    },
    [isValidConnection]
  )

  const {
    hoverTargetNodeId,
    onConnectEnd,
    onConnectStart,
    onNodeMouseEnter,
    onNodeMouseLeave,
    pendingConnection,
  } = usePendingConnection({
    nodes,
    isValidConnection,
    onConnect,
    screenToFlowPosition,
  })

  const onNodesDelete: OnNodesDelete<AnyFlowNode> = useCallback((deletedNodes) => {
    const deletedIds = new Set(deletedNodes.map((node) => node.id))
    setEdges((current) => current.filter((edge) => !deletedIds.has(edge.source) && !deletedIds.has(edge.target)))
  }, [])

  const onEdgesDelete: OnEdgesDelete = useCallback(() => {
    window.requestAnimationFrame(() => {
      setNodes((current) => {
        const next = syncNodeInputs(current, edgesRef.current)
        return next.changed ? next.nodes : current
      })
    })
  }, [setNodes])

  const onEdgeClick = useCallback((event: React.MouseEvent, edge: Edge) => {
    event.preventDefault()
    setEdges((current) => current.filter((item) => item.id !== edge.id))
  }, [])

  const selectedNodes = useMemo(() => nodes.filter((node) => node.selected), [nodes, selectionVersion])
  const selectedEdges = useMemo(() => edges.filter((edge) => edge.selected), [edges, selectionVersion])
  const canDeleteSelection = selectedNodes.length > 0 || selectedEdges.length > 0
  const canDuplicateSelection = selectedNodes.length > 0

  const resetCanvas = useCallback(() => {
    const initialState = createInitialCanvasState()
    setNodes(initialState.nodes)
    setEdges(initialState.edges)
    clearFlow()
    window.requestAnimationFrame(() => {
      void fitView({ duration: 180, padding: 0.2 })
    })
  }, [clearFlow, fitView])

  const handleDeleteSelection = useCallback(() => {
    if (!canDeleteSelection) return

    const nodeIds = selectedNodes.map((node) => ({ id: node.id }))
    const edgeIds = selectedEdges.map((edge) => ({ id: edge.id }))
    void deleteElements({ nodes: nodeIds, edges: edgeIds })
  }, [canDeleteSelection, deleteElements, selectedEdges, selectedNodes])

  const handleDuplicateSelection = useCallback(() => {
    if (!canDuplicateSelection) return

    const duplicatedNodes = selectedNodes.map((node, index) => duplicateNode(node, index))

    setNodes((current) => [...current.map((node) => ({ ...node, selected: false })), ...duplicatedNodes])
  }, [canDuplicateSelection, selectedNodes])

  const handleExportCanvas = useCallback(() => {
    const snapshot = serializeFlowSnapshot(getNodes(), edgesRef.current, getViewport())
    const blob = new Blob([JSON.stringify(snapshot, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `infinite-studio-canvas-${new Date().toISOString().slice(0, 19).replace(/[T:]/g, '-')}.json`
    anchor.click()
    URL.revokeObjectURL(url)
    setMenuNotice({ tone: 'success', message: '画布 JSON 已导出' })
  }, [getNodes, getViewport])

  const handleImportCanvas = useCallback((file: File) => {
    void file.text().then((raw) => {
      let parsed: unknown
      try {
        parsed = JSON.parse(raw)
      } catch (exc) {
        if (exc instanceof SyntaxError) {
          setMenuNotice({ tone: 'error', message: '导入失败：JSON 格式错误' })
          return
        }
        throw exc
      }

      const snapshot = hydrateFlowSnapshot(parsed)
      if (!snapshot) {
        setMenuNotice({ tone: 'error', message: '导入失败：文件格式无效' })
        return
      }

      const typedNodes = snapshot.nodes as AnyFlowNode[]
      setNodes(typedNodes)
      setEdges(snapshot.edges)
      if (snapshot.viewport) {
        void setViewport(snapshot.viewport, { duration: 120 })
      }
      setMenuNotice({ tone: 'success', message: '画布已导入' })
    }).catch((err) => {
      console.error('Import failed:', err)
      setMenuNotice({ tone: 'error', message: '导入失败：无法读取文件' })
    })
  }, [setViewport])

  const handleNewCanvas = useCallback(() => {
    resetCanvas()
  }, [resetCanvas])

  const runningTasks = useMemo(() => history.filter((item) => item.status === 'running').slice(0, 3), [history])

  const nodeTypesMemo = useMemo(() => nodeTypes, [])
  const edgeTypesMemo = useMemo(() => edgeTypes, [])
  const displayNodes = useMemo(() => attachConnectionHints(nodes, pendingConnection, hoverTargetNodeId), [hoverTargetNodeId, nodes, pendingConnection])

  return (
    <div ref={canvasRef} className="fixed inset-0 overflow-hidden" onContextMenu={onCanvasContextMenu} onDoubleClick={onCanvasDoubleClick}>
      <CanvasMenuBar
        canDeleteSelection={canDeleteSelection}
        canDuplicateSelection={canDuplicateSelection}
        notice={menuNotice}
        onClearCanvas={resetCanvas}
        onDeleteSelection={handleDeleteSelection}
        onDuplicateSelection={handleDuplicateSelection}
        onExportCanvas={handleExportCanvas}
        onImportCanvas={handleImportCanvas}
        onNewCanvas={handleNewCanvas}
      />

      <ReactFlow
        nodes={displayNodes}
        edges={edges}
        onNodesChange={(changes) => {
          onNodesChangeBase(changes)
          const resizedNodeIds = new Set(
            changes.flatMap((change) =>
              change.type === 'dimensions' && change.resizing && change.dimensions ? [change.id] : []
            )
          )

          if (resizedNodeIds.size === 0) return

          setNodes((current) =>
            current.map((node) => {
              if (!resizedNodeIds.has(node.id)) return node
              const nextWidth = typeof node.width === 'number' ? node.width : node.data.w
              const nextHeight = typeof node.height === 'number' ? node.height : node.data.h

              if (node.type === 'text-node') {
                return updateTextNodeSize(node, nextWidth, nextHeight)
              }

              if (node.type === 'image-node') {
                return updateImageNodeSize(node, nextWidth, nextHeight)
              }

              return updateVideoNodeSize(node, nextWidth, nextHeight)
            })
          )
        }}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onConnectStart={onConnectStart}
        onConnectEnd={onConnectEnd}
        isValidConnection={isValidConnection}
        onNodesDelete={onNodesDelete}
        onEdgesDelete={onEdgesDelete}
        onEdgeClick={onEdgeClick}
        onNodeMouseEnter={onNodeMouseEnter}
        onNodeMouseLeave={onNodeMouseLeave}
        onMove={onMove}
        onMoveEnd={onMoveEnd}
        onPaneClick={closeMenus}
        nodeTypes={nodeTypesMemo}
        edgeTypes={edgeTypesMemo}
        defaultEdgeOptions={{ type: 'custom' }}
        connectionMode={ConnectionMode.Loose}
        minZoom={0.2}
        maxZoom={2}
        panOnDrag
        zoomOnScroll
        zoomOnPinch
        zoomOnDoubleClick={false}
        connectionRadius={80}
        deleteKeyCode={['Backspace', 'Delete']}
      >
        <Background gap={24} size={1} color="rgba(255,255,255,0.08)" />
        <MiniMap
          position="bottom-left"
          pannable
          zoomable
          maskColor="rgba(18,18,18,0.45)"
          nodeStrokeColor="rgba(255,255,255,0.38)"
          nodeColor="rgba(255,255,255,0.15)"
          style={{
            width: leftDockWidth,
            height: 150,
            left: leftDockInset,
            bottom: minimapBottom,
            margin: 0,
            borderRadius: 18,
            border: '1px solid rgba(255,255,255,0.14)',
            background: 'linear-gradient(145deg, rgba(27,30,37,0.94), rgba(19,21,27,0.92))',
            boxShadow: '0 24px 60px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.04)',
          }}
        />
      </ReactFlow>

      <div className="pointer-events-none absolute z-40 rounded-[18px] p-3 glass-panel" style={{ left: leftDockInset, bottom: tasksBottom, width: leftDockWidth }}>
        <div className="mb-2 flex items-center justify-between text-[11px] uppercase tracking-[0.18em] text-white/42">
          <span>任务</span>
          <span>{runningTasks.length} 活跃</span>
        </div>
        <div className="space-y-2">
          {runningTasks.length === 0 ? <div className="rounded-xl border border-white/8 bg-white/[0.03] px-3 py-2 text-xs text-white/45">暂无进行中的任务</div> : null}
          {runningTasks.map((task) => (
            <div key={task.id} className="rounded-xl border border-white/8 bg-white/[0.04] px-3 py-2 text-xs text-white/82">
              <div className="mb-1 text-[10px] uppercase tracking-[0.12em] text-sky-200/72">{task.kind}</div>
              <div className="line-clamp-1">{task.prompt}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="pointer-events-auto absolute z-40 rounded-[18px] p-3 glass-panel" style={{ left: leftDockInset, bottom: zoomPanelBottom, width: leftDockWidth }}>
        <div className="mb-2 flex items-center justify-between text-xs text-white/72">
          <button type="button" onClick={() => void zoomOut({ duration: 120 })} className="rounded-lg border border-white/12 bg-white/[0.04] px-2 py-1 hover:bg-white/[0.1]">-</button>
          <span>{Math.round(zoomValue * 100)}%</span>
          <button type="button" onClick={() => void zoomIn({ duration: 120 })} className="rounded-lg border border-white/12 bg-white/[0.04] px-2 py-1 hover:bg-white/[0.1]">+</button>
        </div>
        <input
          type="range"
          min={0.2}
          max={2}
          step={0.01}
          value={zoomValue}
          onChange={(event) => {
            const next = Number(event.target.value)
            const viewport = getViewport()
            void setViewport({ x: viewport.x, y: viewport.y, zoom: next }, { duration: 80 })
            setZoomValue(next)
          }}
          className="w-full accent-white"
        />
        <button
          type="button"
          onClick={handleFitView}
          className="mt-2 w-full rounded-xl border border-white/12 bg-white/[0.04] py-1.5 text-xs text-white/78 transition hover:bg-white/[0.1]"
        >
          适配画布
        </button>
      </div>

      {contextMenu ? <div className="fixed inset-0 z-40" onMouseDown={closeMenus} /> : null}

      {contextMenu ? <CanvasNodeMenu dataTestId="canvas-context-menu" position={contextMenu} onCreate={onCreateNodeAtMenu} /> : null}

      <CanvasDock
        onCreateText={() => appendNodeAtViewportCenter('text-node')}
        onCreateImage={() => appendNodeAtViewportCenter('image-node')}
        onCreateVideo={() => appendNodeAtViewportCenter('video-node')}
      />
    </div>
  )
}

export function FlowCanvas() {
  return (
    <ReactFlowProvider>
      <FlowCanvasInner />
    </ReactFlowProvider>
  )
}
