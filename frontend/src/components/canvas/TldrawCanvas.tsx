import { Tldraw, createShapeId, defaultTools } from 'tldraw'
import type { ComponentProps, MouseEvent as ReactMouseEvent } from 'react'
import { useRef, useState } from 'react'
import { AIPromptNodeShapeUtil } from '../nodes/tldraw/AIPromptNodeShapeUtil'
import { ImageNodeShapeUtil } from '../nodes/tldraw/ImageNodeShapeUtil'
import { TextNodeShapeUtil } from '../nodes/tldraw/TextNodeShapeUtil'
import { VideoNodeShapeUtil } from '../nodes/tldraw/VideoNodeShapeUtil'
import { AIPromptNodeTool, ImageNodeTool, TextNodeTool, VideoNodeTool } from '../nodes/tldraw/tools'
import { InternalContextMenu } from './InternalContextMenu'
import { registerWorkflowRules } from './workflowRules'
import '../nodes/tldraw/types'

const shapeUtils = [
  ImageNodeShapeUtil,
  AIPromptNodeShapeUtil,
  TextNodeShapeUtil,
  VideoNodeShapeUtil,
]

const tools = [...defaultTools, ImageNodeTool, AIPromptNodeTool, TextNodeTool, VideoNodeTool]

const components = {
  Handles: null,
  ShapeIndicators: null,
  SelectionForeground: null,
  SelectionBackground: null,
  ContextMenu: InternalContextMenu,
}

const editorOptions = {
  wheelBehavior: 'zoom' as const,
}

// Helper to check if event originated from canvas area
// Uses Element instead of HTMLElement to support SVG and other non-HTML DOM nodes in tldraw
function isInsideCanvas(eventTarget: EventTarget | null): boolean {
  if (!(eventTarget instanceof Element)) return false
  // Check if target is or is inside the tldraw canvas element
  return !!eventTarget.closest('.tl-canvas')
}

export function TldrawCanvas() {
  const editorRef = useRef<Parameters<NonNullable<ComponentProps<typeof Tldraw>['onMount']>>[0] | null>(null)
  const panStartRef = useRef<{ x: number; y: number; camX: number; camY: number; moved: boolean } | null>(null)
  const leftGestureRef = useRef<{ x: number; y: number; moved: boolean; ctrlAtStart: boolean } | null>(null)
  const suppressNextContextMenuRef = useRef(false)
  const [nodeMenu, setNodeMenu] = useState<{ x: number; y: number } | null>(null)

  const handleMount = (editor: Parameters<NonNullable<ComponentProps<typeof Tldraw>['onMount']>>[0]) => {
    editorRef.current = editor
    editor.user.updateUserPreferences({ colorScheme: 'dark', locale: 'zh-cn' })
    registerWorkflowRules(editor)

    const existing = editor.getCurrentPageShapes().some((shape) =>
      ['image-node', 'ai-prompt-node', 'text-node', 'video-node'].includes(shape.type)
    )

    if (existing) return

    editor.createShapes([
      {
        id: createShapeId('image-node-initial'),
        type: 'image-node',
        x: 220,
        y: 120,
      },
      {
        id: createShapeId('ai-node-initial'),
        type: 'ai-prompt-node',
        x: 180,
        y: 500,
      },
      {
        id: createShapeId('text-node-initial'),
        type: 'text-node',
        x: 760,
        y: 140,
      },
      {
        id: createShapeId('video-node-initial'),
        type: 'video-node',
        x: 210,
        y: 860,
      },
    ])
  }

  const createNodeAtScreenPoint = (clientX: number, clientY: number, type: 'text-node' | 'image-node' | 'video-node' | 'ai-prompt-node' = 'text-node') => {
    const editor = editorRef.current
    if (!editor) return
    const pagePoint = editor.screenToPage({ x: clientX, y: clientY })
    editor.createShape({
      type,
      x: pagePoint.x - 180,
      y: pagePoint.y - 120,
    })
    editor.setCurrentTool('select')
  }

  const onMouseDown = (event: ReactMouseEvent<HTMLDivElement>) => {
    // Left button drag pans canvas.
    // Ctrl + Left button should be reserved for tldraw brush selection (pass-through).
    if (event.button !== 0) return
    // Only track drag gestures that originate from canvas area
    if (!isInsideCanvas(event.target)) return

    leftGestureRef.current = {
      x: event.clientX,
      y: event.clientY,
      moved: false,
      ctrlAtStart: event.ctrlKey,
    }

    if (event.ctrlKey) return
    const editor = editorRef.current
    if (!editor) return

    setNodeMenu(null)
    const camera = editor.getCamera()
    panStartRef.current = {
      x: event.clientX,
      y: event.clientY,
      camX: camera.x,
      camY: camera.y,
      moved: false,
    }

    // Prevent default browser behavior from interrupting drag.
    event.preventDefault()
  }

  const onMouseMove = (event: ReactMouseEvent<HTMLDivElement>) => {
    const leftGesture = leftGestureRef.current

    if (leftGesture) {
      if (Math.abs(event.clientX - leftGesture.x) + Math.abs(event.clientY - leftGesture.y) > 0) {
        leftGesture.moved = true
      }
    }

    const start = panStartRef.current
    const editor = editorRef.current
    if (!start || !editor) return

    const zoom = editor.getZoomLevel()
    const dx = (event.clientX - start.x) / zoom
    const dy = (event.clientY - start.y) / zoom
    // User requirement: any movement (>0) should suppress context menu
    if (Math.abs(event.clientX - start.x) + Math.abs(event.clientY - start.y) > 0) {
      start.moved = true
    }
    editor.setCamera({ x: start.camX + dx, y: start.camY + dy, z: editor.getCamera().z })
  }

  const onMouseUp = (event: ReactMouseEvent<HTMLDivElement>) => {
    // Always clear tracked gesture on left-button release, even if released off-canvas
    // This prevents stale state from affecting future interactions
    if (event.button === 0) {
      suppressNextContextMenuRef.current = !!leftGestureRef.current?.moved
      panStartRef.current = null
      leftGestureRef.current = null
    }
  }

  const onContextMenu = (event: ReactMouseEvent<HTMLDivElement>) => {
    // Only handle context menu for canvas-originated events
    if (!isInsideCanvas(event.target)) return

    if (suppressNextContextMenuRef.current) {
      event.preventDefault()
      suppressNextContextMenuRef.current = false
      panStartRef.current = null
      leftGestureRef.current = null
      return
    }

    // Right click is dedicated to opening context menu.
    suppressNextContextMenuRef.current = false
    setNodeMenu(null)
  }

  const onDoubleClick = (event: ReactMouseEvent<HTMLDivElement>) => {
    const editor = editorRef.current
    if (!editor) return

    const pagePoint = editor.screenToPage({ x: event.clientX, y: event.clientY })
    const hit = editor.getShapeAtPoint(pagePoint, { hitInside: true, margin: 2 })
    if (hit) return

    setNodeMenu({ x: event.clientX, y: event.clientY })
  }

  const pickType = (type: 'text-node' | 'image-node' | 'video-node' | 'ai-prompt-node') => {
    if (!nodeMenu) return
    createNodeAtScreenPoint(nodeMenu.x, nodeMenu.y, type)
    setNodeMenu(null)
  }

  const closeMenus = () => {
    setNodeMenu(null)
  }

  return (
    <div
      className="fixed inset-0 overflow-hidden"
      onMouseDownCapture={onMouseDown}
      onMouseMoveCapture={onMouseMove}
      onMouseUpCapture={onMouseUp}
      onContextMenu={onContextMenu}
      onDoubleClick={onDoubleClick}
    >
      <Tldraw
        persistenceKey="infinite-canvas-project"
        shapeUtils={shapeUtils}
        tools={tools}
        components={components}
        cameraOptions={editorOptions}
        onMount={handleMount}
      />

      {nodeMenu ? (
        <div className="fixed inset-0 z-40" onMouseDown={closeMenus} />
      ) : null}

      {nodeMenu ? (
        <div
          className="absolute z-50 w-44 rounded-xl border border-white/15 bg-[#161616]/98 p-1.5 shadow-xl backdrop-blur"
          style={{ left: nodeMenu.x, top: nodeMenu.y }}
          onMouseDown={(e) => e.stopPropagation()}
        >
          <button type="button" onClick={() => pickType('text-node')} className="block w-full rounded-lg px-2 py-2 text-left text-sm text-gray-100 hover:bg-white/10">添加文本节点</button>
          <button type="button" onClick={() => pickType('image-node')} className="block w-full rounded-lg px-2 py-2 text-left text-sm text-gray-100 hover:bg-white/10">添加图片节点</button>
          <button type="button" onClick={() => pickType('video-node')} className="block w-full rounded-lg px-2 py-2 text-left text-sm text-gray-100 hover:bg-white/10">添加视频节点</button>
          <button type="button" onClick={() => pickType('ai-prompt-node')} className="block w-full rounded-lg px-2 py-2 text-left text-sm text-gray-100 hover:bg-white/10">添加提示节点</button>
        </div>
      ) : null}

      <style>{`.tl-selection__bg, .tl-selection__fg, .tl-collaborator-scribble, .tl-user-indicator, .tl-corner-handle, .tl-corner-crop-handle, .tl-corner-crop-edge-handle, .tl-text-handle { display: none !important; }`}</style>
    </div>
  )
}
