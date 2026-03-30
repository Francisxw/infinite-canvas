import { describe, expect, it, vi } from 'vitest'
import type { Edge, Node, Viewport } from '@xyflow/react'
import { loadPersistedViewport, migrateLegacyTldrawProject, saveFlowViewport } from '../useFlowPersistence'

describe('migrateLegacyTldrawProject', () => {
  it('migrates legacy tldraw arrows into custom edges with handles', () => {
    const migrated = migrateLegacyTldrawProject({
      records: [
        {
          id: 'shape:text-1',
          typeName: 'shape',
          type: 'text-node',
          x: 100,
          y: 100,
          props: { w: 300, h: 240, text: 'legacy text' },
        },
        {
          id: 'shape:image-1',
          typeName: 'shape',
          type: 'image-node',
          x: 400,
          y: 100,
          props: { w: 390, h: 292, prompt: 'legacy image' },
        },
        {
          id: 'shape:arrow-1',
          typeName: 'shape',
          type: 'arrow',
        },
        {
          id: 'binding:start-1',
          typeName: 'binding',
          type: 'arrow',
          fromId: 'shape:arrow-1',
          toId: 'shape:text-1',
          props: { terminal: 'start' },
        },
        {
          id: 'binding:end-1',
          typeName: 'binding',
          type: 'arrow',
          fromId: 'shape:arrow-1',
          toId: 'shape:image-1',
          props: { terminal: 'end' },
        },
      ],
    })

    expect(migrated.nodes).toHaveLength(2)
    expect(migrated.edges).toEqual([
      expect.objectContaining({
        id: 'arrow-1',
        source: 'text-1',
        target: 'image-1',
        type: 'custom',
        sourceHandle: 'right-source',
        targetHandle: 'left-target',
      }),
    ])
  })
})

describe('viewport persistence helpers', () => {
  it('loads viewport from an existing flow snapshot', () => {
    const viewport: Viewport = { x: 120, y: -80, zoom: 1.35 }

    expect(loadPersistedViewport(() => ({ nodes: [], edges: [], viewport }))).toEqual(viewport)
  })

  it('saves viewport without changing nodes or edges', () => {
    const saveFlow = vi.fn()
    const nodes = [{ id: 'node-1' }] as Node[]
    const edges = [{ id: 'edge-1', source: 'node-1', target: 'node-2' }] as Edge[]
    const viewport: Viewport = { x: 24, y: 48, zoom: 0.9 }

    saveFlowViewport(saveFlow, nodes, edges, viewport)

    expect(saveFlow).toHaveBeenCalledWith(nodes, edges, viewport)
  })
})
