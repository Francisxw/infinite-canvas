import type { Connection, FinalConnectionState, OnConnect, OnConnectStart } from '@xyflow/react'
import { useCallback, useEffect, useRef, useState } from 'react'
import type { AnyFlowNode } from '../nodes/flow/types'
import { getNodeIdFromPoint } from './flowConnectionUtils'
import type { PendingConnection } from './flowPayloads'

type FlowPoint = { x: number; y: number }

type PendingConnectionResolution = {
  targetNodeId: string | null
  shouldClear: boolean
}

type ResolvePendingConnectionTargetOptions = {
  clientX: number
  clientY: number
  nodes: AnyFlowNode[]
  pendingConnection: PendingConnection
  hoveredTargetNodeId: string | null
  screenToFlowPosition: (position: { x: number; y: number }) => FlowPoint
  getTargetNodeIdFromPoint?: (clientX: number, clientY: number, excludeNodeId?: string) => string | null
}

type UsePendingConnectionOptions = {
  nodes: AnyFlowNode[]
  isValidConnection: (connection: Connection) => boolean
  onConnect: OnConnect
  screenToFlowPosition: (position: { x: number; y: number }) => FlowPoint
}

function getNodeBounds(node: AnyFlowNode) {
  const width = typeof node.width === 'number' ? node.width : node.data.w
  const height = typeof node.height === 'number' ? node.height : node.data.h

  return {
    width,
    height,
    x: node.position.x,
    y: node.position.y,
  }
}

export function resolvePendingConnectionTarget({
  clientX,
  clientY,
  nodes,
  pendingConnection,
  hoveredTargetNodeId,
  screenToFlowPosition,
  getTargetNodeIdFromPoint = getNodeIdFromPoint,
}: ResolvePendingConnectionTargetOptions): PendingConnectionResolution {
  const directTargetNodeId = getTargetNodeIdFromPoint(clientX, clientY, pendingConnection.nodeId)
  const flowPoint = screenToFlowPosition({ x: clientX, y: clientY })
  const fallbackCandidates = nodes
    .filter((node) => node.id !== pendingConnection.nodeId)
    .map((node) => {
      const bounds = getNodeBounds(node)
      const hitPadding = 20
      const inBounds =
        flowPoint.x >= bounds.x - hitPadding &&
        flowPoint.x <= bounds.x + bounds.width + hitPadding &&
        flowPoint.y >= bounds.y - hitPadding &&
        flowPoint.y <= bounds.y + bounds.height + hitPadding

      const centerX = bounds.x + bounds.width / 2
      const centerY = bounds.y + bounds.height / 2
      const distance = Math.hypot(centerX - flowPoint.x, centerY - flowPoint.y)

      return { nodeId: node.id, inBounds, distance }
    })
    .sort((left, right) => left.distance - right.distance)

  const inBoundsTarget = fallbackCandidates.find((candidate) => candidate.inBounds)
  const nearestTarget = fallbackCandidates[0]
  const fallbackTargetNodeId = inBoundsTarget?.nodeId ?? (nearestTarget && nearestTarget.distance <= 420 ? nearestTarget.nodeId : null)
  const targetNodeId = directTargetNodeId ?? hoveredTargetNodeId ?? fallbackTargetNodeId

  if (!targetNodeId || targetNodeId === pendingConnection.nodeId) {
    return { targetNodeId: null, shouldClear: true }
  }

  return { targetNodeId, shouldClear: false }
}

function buildPendingConnectionConnection(pendingConnection: PendingConnection, targetNodeId: string): Connection {
  return pendingConnection.handleType === 'source'
    ? {
        source: pendingConnection.nodeId,
        sourceHandle: 'right-source',
        target: targetNodeId,
        targetHandle: 'left-target',
      }
    : {
        source: targetNodeId,
        sourceHandle: 'right-source',
        target: pendingConnection.nodeId,
        targetHandle: 'left-target',
      }
}

export function usePendingConnection({ nodes, isValidConnection, onConnect, screenToFlowPosition }: UsePendingConnectionOptions) {
  const [pendingConnection, setPendingConnection] = useState<PendingConnection | null>(null)
  const [hoverTargetNodeId, setHoverTargetNodeId] = useState<string | null>(null)
  const pendingConnectionRef = useRef<PendingConnection | null>(null)
  const hoverTargetNodeIdRef = useRef<string | null>(null)

  const clearPendingConnection = useCallback(() => {
    pendingConnectionRef.current = null
    hoverTargetNodeIdRef.current = null
    setPendingConnection(null)
    setHoverTargetNodeId(null)
  }, [])

  useEffect(() => {
    pendingConnectionRef.current = pendingConnection
  }, [pendingConnection])

  useEffect(() => {
    hoverTargetNodeIdRef.current = hoverTargetNodeId
  }, [hoverTargetNodeId])

  useEffect(() => {
    if (!pendingConnection) return

    const onPointerMove = (event: PointerEvent) => {
      const targetNodeId = getNodeIdFromPoint(event.clientX, event.clientY, pendingConnection.nodeId)
      setHoverTargetNodeId(targetNodeId)
    }

    window.addEventListener('pointermove', onPointerMove)
    return () => window.removeEventListener('pointermove', onPointerMove)
  }, [pendingConnection])

  const resolvePendingConnectionAtPoint = useCallback((clientX: number, clientY: number) => {
    const activePendingConnection = pendingConnectionRef.current

    if (!activePendingConnection) {
      clearPendingConnection()
      return
    }

    const resolution = resolvePendingConnectionTarget({
      clientX,
      clientY,
      nodes,
      pendingConnection: activePendingConnection,
      hoveredTargetNodeId: hoverTargetNodeIdRef.current,
      screenToFlowPosition,
    })

    if (resolution.shouldClear || !resolution.targetNodeId) {
      clearPendingConnection()
      return
    }

    const connection = buildPendingConnectionConnection(activePendingConnection, resolution.targetNodeId)

    if (isValidConnection(connection)) {
      onConnect(connection)
    }

    clearPendingConnection()
  }, [clearPendingConnection, isValidConnection, nodes, onConnect, screenToFlowPosition])

  const onConnectStart = useCallback<OnConnectStart>((_, params) => {
    if (!params.nodeId || !params.handleType) return
    const nextPending: PendingConnection = { nodeId: params.nodeId, handleType: params.handleType }
    pendingConnectionRef.current = nextPending
    setPendingConnection(nextPending)
  }, [])

  const onConnectEnd = useCallback((event: MouseEvent | TouchEvent, state: FinalConnectionState) => {
    if (state.toNode) {
      clearPendingConnection()
      return
    }

    if (!pendingConnectionRef.current) {
      clearPendingConnection()
      return
    }

    const point = 'changedTouches' in event ? event.changedTouches[0] : event
    resolvePendingConnectionAtPoint(point.clientX, point.clientY)
  }, [clearPendingConnection, resolvePendingConnectionAtPoint])

  const onNodeMouseEnter = useCallback((_: React.MouseEvent, node: AnyFlowNode) => {
    if (!pendingConnection || node.id === pendingConnection.nodeId) return
    hoverTargetNodeIdRef.current = node.id
    setHoverTargetNodeId(node.id)
  }, [pendingConnection])

  const onNodeMouseLeave = useCallback(() => {
    hoverTargetNodeIdRef.current = null
    setHoverTargetNodeId(null)
  }, [])

  return {
    hoverTargetNodeId,
    onConnectEnd,
    onConnectStart,
    onNodeMouseEnter,
    onNodeMouseLeave,
    pendingConnection,
  }
}
