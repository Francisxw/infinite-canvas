import { useCallback } from 'react'
import type { Edge, Node, Viewport } from '@xyflow/react'
import type { AnyFlowNode } from '../components/nodes/flow/types'

const FLOW_STORAGE_KEY = 'infinite-canvas-flow'
const LEGACY_TLDRAW_STORAGE_KEY = 'infinite-canvas-project'
const CURRENT_FLOW_VERSION = 1

type PersistedFlowV1 = {
  version: 1
  nodes: Node[]
  edges: Edge[]
  viewport?: {
    x: number
    y: number
    zoom: number
  }
}

type PersistedFlowLike = {
  version?: number
  nodes?: unknown
  edges?: unknown
  viewport?: unknown
}

type LegacyArrowBinding = {
  start?: string
  end?: string
}

type FlowSnapshot = {
  nodes: Node[]
  edges: Edge[]
  viewport?: Viewport
}

type SerializableViewport = {
  x: number
  y: number
  zoom: number
}

type PortableNode = Node<Record<string, unknown>>

const stripTransientNodeData = (node: AnyFlowNode | PortableNode) => {
  const data = (node.data ?? {}) as Record<string, unknown>

  const {
    modelPickerOpen: _modelPickerOpen,
    settingsOpen: _settingsOpen,
    quantityOpen: _quantityOpen,
    customCountOpen: _customCountOpen,
    isEditing: _isEditing,
    isConnectionCandidate: _isConnectionCandidate,
    isConnectionHovered: _isConnectionHovered,
    isConnecting: _isConnecting,
    errorMessage: _errorMessage,
    isGenerating: _isGenerating,
    ...stableData
  } = data

  return {
    ...node,
    selected: false,
    dragging: false,
    data: stableData,
  }
}

const isBrowser = () => typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null

const normalizeEntityId = (id: unknown, prefix: string) => {
  if (typeof id !== 'string' || id.length === 0) return null
  return id.startsWith(prefix) ? id.slice(prefix.length) : id
}

const normalizeNode = (value: unknown): Node | null => {
  if (!isRecord(value)) return null

  const id = typeof value.id === 'string' ? value.id : null
  if (!id) return null

  const positionCandidate = value.position
  const hasPosition =
    isRecord(positionCandidate) &&
    typeof positionCandidate.x === 'number' &&
    typeof positionCandidate.y === 'number'

  const x = typeof value.x === 'number' ? value.x : 0
  const y = typeof value.y === 'number' ? value.y : 0

  return {
    ...(value as Node),
    id,
    position: hasPosition
      ? ({
          x: positionCandidate.x,
          y: positionCandidate.y,
        } as Node['position'])
      : { x, y },
    data: isRecord(value.data) ? value.data : {},
  }
}

const normalizeEdge = (value: unknown): Edge | null => {
  if (!isRecord(value)) return null

  const id = typeof value.id === 'string' ? value.id : null
  const source = typeof value.source === 'string' ? value.source : null
  const target = typeof value.target === 'string' ? value.target : null

  if (!id || !source || !target) return null

  return {
    ...(value as Edge),
    id,
    source,
    target,
    type: 'custom',
    sourceHandle:
      typeof value.sourceHandle === 'string' && value.sourceHandle.length > 0
        ? value.sourceHandle
        : 'right-source',
    targetHandle:
      typeof value.targetHandle === 'string' && value.targetHandle.length > 0
        ? value.targetHandle
        : 'left-target',
  }
}

const toNodeArray = (value: unknown): Node[] => {
  if (!Array.isArray(value)) return []
  return value.map(normalizeNode).filter((node): node is Node => node !== null)
}

const toEdgeArray = (value: unknown): Edge[] => {
  if (!Array.isArray(value)) return []
  return value.map(normalizeEdge).filter((edge): edge is Edge => edge !== null)
}

const parseJson = (raw: string | null): unknown => {
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

const normalizeViewport = (value: unknown): { x: number; y: number; zoom: number } | undefined => {
  if (!isRecord(value)) return undefined
  if (typeof value.x !== 'number' || typeof value.y !== 'number' || typeof value.zoom !== 'number') return undefined

  return {
    x: value.x,
    y: value.y,
    zoom: value.zoom,
  }
}

export const serializeFlowSnapshot = (
  nodes: Node[],
  edges: Edge[],
  viewport?: SerializableViewport
): PersistedFlowV1 => ({
  version: CURRENT_FLOW_VERSION,
  nodes: nodes.map((node) => stripTransientNodeData(node as PortableNode)),
  edges: edges.map((edge) => ({
    ...edge,
    selected: false,
  })),
  viewport,
})

export const hydrateFlowSnapshot = (parsed: unknown): FlowSnapshot | null => {
  return hydratePersistedFlow(parsed)
}

export const loadPersistedViewport = (loadFlow: () => FlowSnapshot): Viewport | undefined => loadFlow().viewport

export const saveFlowViewport = (
  saveFlow: (nodes: Node[], edges: Edge[], viewport?: Viewport) => void,
  nodes: Node[],
  edges: Edge[],
  viewport: Viewport
) => {
  saveFlow(nodes, edges, viewport)
}

const hydratePersistedFlow = (parsed: unknown): FlowSnapshot | null => {
  if (!isRecord(parsed)) return null

  const value = parsed as PersistedFlowLike
  const version = typeof value.version === 'number' ? value.version : undefined
  const nodes = toNodeArray(value.nodes)
  const edges = toEdgeArray(value.edges)
  const viewport = normalizeViewport(value.viewport)

  if (!Array.isArray(value.nodes) || !Array.isArray(value.edges)) {
    return null
  }

  if (version === undefined) {
    return { nodes, edges, viewport }
  }

  if (version === CURRENT_FLOW_VERSION) {
    return { nodes, edges, viewport }
  }

  if (version > CURRENT_FLOW_VERSION) {
    return null
  }

  return { nodes, edges, viewport }
}

const collectRecords = (
  value: unknown,
  byId: Map<string, Record<string, unknown>>,
  seen: Set<unknown>,
  depth: number
) => {
  if (depth > 6 || value === null || value === undefined || seen.has(value)) return
  seen.add(value)

  if (Array.isArray(value)) {
    value.forEach((entry) => collectRecords(entry, byId, seen, depth + 1))
    return
  }

  if (!isRecord(value)) return

  if (typeof value.id === 'string') {
    byId.set(value.id, value)
  }

  Object.values(value).forEach((entry) => collectRecords(entry, byId, seen, depth + 1))
}

export const migrateLegacyTldrawProject = (parsed: unknown): FlowSnapshot => {
  if (!isRecord(parsed)) return { nodes: [], edges: [] }

  const byId = new Map<string, Record<string, unknown>>()
  collectRecords(parsed, byId, new Set(), 0)

  const records = Array.from(byId.values())
  const shapeRecords = records.filter((record) => {
    const typeName = record.typeName
    if (typeName === 'shape') return true
    if (typeof record.id === 'string' && record.id.startsWith('shape:')) return true
    return false
  })

  const supportedNodeTypes = new Set(['text-node', 'image-node', 'video-node'])
  const nodeRecords = shapeRecords.filter((record) => {
    const shapeType = record.type
    return typeof shapeType === 'string' && supportedNodeTypes.has(shapeType)
  })

  const arrowRecords = shapeRecords.filter((record) => record.type === 'arrow')

  const nodes = nodeRecords
    .map((record): Node | null => {
      const normalizedId = normalizeEntityId(record.id, 'shape:')
      if (!normalizedId) return null

      const props = isRecord(record.props) ? record.props : {}
      const width = typeof props.w === 'number' ? props.w : undefined
      const height = typeof props.h === 'number' ? props.h : undefined

      return {
        id: normalizedId,
        type: typeof record.type === 'string' ? record.type : 'default',
        position: {
          x: typeof record.x === 'number' ? record.x : 0,
          y: typeof record.y === 'number' ? record.y : 0,
        },
        data: {
          ...props,
          legacyTldrawShapeId: record.id,
          legacyTldrawShapeType: record.type,
          migratedFrom: 'tldraw',
        },
        style:
          width !== undefined || height !== undefined
            ? {
                ...(width !== undefined ? { width } : {}),
                ...(height !== undefined ? { height } : {}),
              }
            : undefined,
      }
    })
    .filter((node): node is Node => node !== null)

  const availableNodeIds = new Set(nodes.map((node) => node.id))
  const bindings = records.filter((record) => {
    return record.typeName === 'binding' && record.type === 'arrow'
  })

  const edgeBindings = new Map<string, LegacyArrowBinding>()
  bindings.forEach((binding) => {
    const fromId = typeof binding.fromId === 'string' ? binding.fromId : null
    const toId = normalizeEntityId(binding.toId, 'shape:')
    const terminal =
      isRecord(binding.props) && typeof binding.props.terminal === 'string'
        ? binding.props.terminal
        : null

    if (!fromId || !toId || !terminal) return
    if (terminal !== 'start' && terminal !== 'end') return

    const current = edgeBindings.get(fromId) ?? {}
    current[terminal] = toId
    edgeBindings.set(fromId, current)
  })

  const edges = arrowRecords
    .map((arrow): Edge | null => {
      const arrowId = typeof arrow.id === 'string' ? arrow.id : null
      if (!arrowId) return null

      const binding = edgeBindings.get(arrowId)
      if (!binding?.start || !binding.end) return null
      if (!availableNodeIds.has(binding.start) || !availableNodeIds.has(binding.end)) {
        return null
      }

      const edgeId = normalizeEntityId(arrowId, 'shape:') ?? arrowId

      return {
        id: edgeId,
        source: binding.start,
        target: binding.end,
        type: 'custom',
        sourceHandle: 'right-source',
        targetHandle: 'left-target',
        data: {
          legacyTldrawShapeId: arrowId,
          migratedFrom: 'tldraw',
        },
      }
    })
    .filter((edge): edge is Edge => edge !== null)

  return { nodes, edges }
}

export function useFlowPersistence() {
  const saveFlow = useCallback((
    nodes: Node[],
    edges: Edge[],
    viewport?: { x: number; y: number; zoom: number }
  ) => {
    if (!isBrowser()) return

    const payload = serializeFlowSnapshot(nodes, edges, viewport)

    try {
      window.localStorage.setItem(FLOW_STORAGE_KEY, JSON.stringify(payload))
    } catch {
      // Keep failure silent: persistence should not break user interactions.
    }
  }, [])

  const loadFlow = useCallback((): FlowSnapshot => {
    if (!isBrowser()) return { nodes: [], edges: [] }

    const persisted = parseJson(window.localStorage.getItem(FLOW_STORAGE_KEY))
    const hydrated = hydratePersistedFlow(persisted)
    if (hydrated) {
      return hydrated
    }

    const legacy = parseJson(window.localStorage.getItem(LEGACY_TLDRAW_STORAGE_KEY))
    const migrated = migrateLegacyTldrawProject(legacy)
    if (migrated.nodes.length > 0 || migrated.edges.length > 0) {
      saveFlow(migrated.nodes, migrated.edges)
      return migrated
    }

    return { nodes: [], edges: [] }
  }, [saveFlow])

  const clearFlow = useCallback(() => {
    if (!isBrowser()) return

    try {
      window.localStorage.removeItem(FLOW_STORAGE_KEY)
      window.localStorage.removeItem(LEGACY_TLDRAW_STORAGE_KEY)
    } catch {
      // Keep failure silent: clearing persistence should not crash app.
    }
  }, [])

  return { saveFlow, loadFlow, clearFlow }
}
