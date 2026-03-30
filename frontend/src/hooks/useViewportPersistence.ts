import { useCallback, useEffect, useRef, useState } from 'react'
import type { Edge, Node, OnMove, OnMoveEnd, Viewport } from '@xyflow/react'

type UseViewportPersistenceOptions = {
  hydrated: boolean
  initialViewport: Viewport | null
  nodes: Node[]
  edges: Edge[]
  saveViewport: (nodes: Node[], edges: Edge[], viewport: Viewport) => void
  setViewport: (viewport: Viewport, options?: { duration?: number }) => Promise<boolean>
}

export function useViewportPersistence({
  hydrated,
  initialViewport,
  nodes,
  edges,
  saveViewport,
  setViewport,
}: UseViewportPersistenceOptions) {
  const didRestoreViewportRef = useRef(false)
  const didHydrateViewportRef = useRef(false)
  const viewportSaveTimerRef = useRef<number | null>(null)
  const nodesRef = useRef(nodes)
  const edgesRef = useRef(edges)
  const [zoomValue, setZoomValue] = useState(1)

  useEffect(() => {
    nodesRef.current = nodes
  }, [nodes])

  useEffect(() => {
    edgesRef.current = edges
  }, [edges])

  useEffect(() => () => {
    if (viewportSaveTimerRef.current !== null) {
      window.clearTimeout(viewportSaveTimerRef.current)
      viewportSaveTimerRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!hydrated || didRestoreViewportRef.current) return

    didRestoreViewportRef.current = true
    didHydrateViewportRef.current = true
    if (!initialViewport) return

    void setViewport(initialViewport, { duration: 0 })
    setZoomValue(initialViewport.zoom)
  }, [hydrated, initialViewport, setViewport])

  const persistViewport = useCallback((viewport: Viewport) => {
    if (!hydrated || !didHydrateViewportRef.current) return
    saveViewport(nodesRef.current, edgesRef.current, viewport)
  }, [hydrated, saveViewport])

  const onMove = useCallback<OnMove>((_, viewport) => {
    setZoomValue(viewport.zoom)

    if (viewportSaveTimerRef.current !== null) {
      return
    }

    viewportSaveTimerRef.current = window.setTimeout(() => {
      persistViewport(viewport)
      viewportSaveTimerRef.current = null
    }, 220)
  }, [persistViewport])

  const onMoveEnd = useCallback<OnMoveEnd>((_, viewport) => {
    if (viewportSaveTimerRef.current !== null) {
      window.clearTimeout(viewportSaveTimerRef.current)
      viewportSaveTimerRef.current = null
    }

    persistViewport(viewport)
  }, [persistViewport])

  return {
    onMove,
    onMoveEnd,
    setZoomValue,
    zoomValue,
  }
}
