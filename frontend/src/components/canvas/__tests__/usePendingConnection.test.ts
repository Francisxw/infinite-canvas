import { describe, expect, it } from 'vitest'
import { createFlowNode } from '../flowNodeFactory'
import { resolvePendingConnectionTarget } from '../usePendingConnection'
import type { ImageFlowNode, TextFlowNode, VideoFlowNode } from '../../nodes/flow/types'

describe('usePendingConnection', () => {
  it('prefers the hovered target over fallback candidates when pointer release misses a node', () => {
    const sourceNode = createFlowNode('text-node', 200, 200) as TextFlowNode
    const hoveredNode = createFlowNode('video-node', 700, 220) as VideoFlowNode
    const nearerFallbackNode = createFlowNode('image-node', 430, 200) as ImageFlowNode

    const resolution = resolvePendingConnectionTarget({
      clientX: 0,
      clientY: 0,
      nodes: [sourceNode, hoveredNode, nearerFallbackNode],
      pendingConnection: { nodeId: sourceNode.id, handleType: 'source' },
      hoveredTargetNodeId: hoveredNode.id,
      screenToFlowPosition: () => ({ x: 430, y: 200 }),
      getTargetNodeIdFromPoint: () => null,
    })

    expect(resolution).toEqual({
      targetNodeId: hoveredNode.id,
      shouldClear: false,
    })
  })

  it('falls back to a nearby node when pointer release lands just outside node bounds', () => {
    const sourceNode = createFlowNode('text-node', 200, 200) as TextFlowNode
    const targetNode = createFlowNode('video-node', 700, 220) as VideoFlowNode
    const targetBounds = {
      left: targetNode.position.x,
      centerY: targetNode.position.y + targetNode.data.h / 2,
    }

    const resolution = resolvePendingConnectionTarget({
      clientX: 0,
      clientY: 0,
      nodes: [sourceNode, targetNode],
      pendingConnection: { nodeId: sourceNode.id, handleType: 'source' },
      hoveredTargetNodeId: null,
      screenToFlowPosition: () => ({ x: targetBounds.left - 10, y: targetBounds.centerY }),
      getTargetNodeIdFromPoint: () => null,
    })

    expect(resolution).toEqual({
      targetNodeId: targetNode.id,
      shouldClear: false,
    })
  })

  it('clears when no direct, hovered, or nearby fallback target exists', () => {
    const sourceNode = createFlowNode('text-node', 200, 200) as TextFlowNode
    const targetNode = createFlowNode('video-node', 1200, 900) as VideoFlowNode

    const resolution = resolvePendingConnectionTarget({
      clientX: 0,
      clientY: 0,
      nodes: [sourceNode, targetNode],
      pendingConnection: { nodeId: sourceNode.id, handleType: 'source' },
      hoveredTargetNodeId: null,
      screenToFlowPosition: () => ({ x: 0, y: 0 }),
      getTargetNodeIdFromPoint: () => null,
    })

    expect(resolution).toEqual({
      targetNodeId: null,
      shouldClear: true,
    })
  })
})
