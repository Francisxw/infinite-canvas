import { describe, expect, it } from 'vitest'
import type { Edge } from '@xyflow/react'
import { createFlowNode } from '../flowNodeFactory'
import { buildNodeOutputs, isNodeConnectionCompatible, syncNodeInputs } from '../flowPayloads'
import type { AnyFlowNode, ImageFlowNode, TextFlowNode, VideoFlowNode } from '../../nodes/flow/types'

describe('flowPayloads', () => {
  it('buildNodeOutputs derives payloads from text, image, and video nodes', () => {
    const textNode = createFlowNode('text-node', 100, 100) as TextFlowNode
    textNode.data.text = 'hello world'

    const imageNode = createFlowNode('image-node', 200, 100) as ImageFlowNode
    imageNode.data.prompt = 'image prompt'
    imageNode.data.dataUrl = 'https://example.com/image.png'
    imageNode.data.filename = 'image.png'

    const videoNode = createFlowNode('video-node', 300, 100) as VideoFlowNode
    videoNode.data.prompt = 'video prompt'
    videoNode.data.coverUrl = 'https://example.com/video-cover.png'
    videoNode.data.filename = 'video.mp4'

    expect(buildNodeOutputs(textNode)).toEqual([
      expect.objectContaining({ kind: 'text', textValue: 'hello world' }),
    ])
    expect(buildNodeOutputs(imageNode)).toEqual([
      expect.objectContaining({ kind: 'image', previewUrl: 'https://example.com/image.png' }),
    ])
    expect(buildNodeOutputs(videoNode)).toEqual([
      expect.objectContaining({ kind: 'video', previewUrl: 'https://example.com/video-cover.png' }),
    ])
  })

  it('syncNodeInputs propagates text payloads into downstream prompts', () => {
    const textNode = createFlowNode('text-node', 100, 100) as TextFlowNode
    textNode.data.text = 'sunlit portrait'
    const sourceOutputs = buildNodeOutputs(textNode)
    textNode.data.outputPayloads = sourceOutputs
    textNode.data.selectedOutputPayloadIds = sourceOutputs.map((payload) => payload.id)

    const imageNode = createFlowNode('image-node', 300, 100) as ImageFlowNode
    imageNode.data.prompt = ''

    const nodes: AnyFlowNode[] = [textNode, imageNode]
    const edges: Edge[] = [
      {
        id: 'edge-1',
        source: textNode.id,
        target: imageNode.id,
        sourceHandle: 'right-source',
        targetHandle: 'left-target',
        type: 'custom',
      },
    ]

    const result = syncNodeInputs(nodes, edges)
    const nextImage = result.nodes.find((node) => node.id === imageNode.id)

    expect(result.changed).toBe(true)
    expect(nextImage?.data.inputPayloads).toHaveLength(1)
    expect(nextImage?.data.prompt).toBe('sunlit portrait')
  })

  it('allows structurally compatible connections before source nodes produce outputs', () => {
    const emptyTextNode = createFlowNode('text-node', 100, 100) as TextFlowNode
    const imageNode = createFlowNode('image-node', 300, 100) as ImageFlowNode

    expect(buildNodeOutputs(emptyTextNode)).toHaveLength(0)
    expect(isNodeConnectionCompatible(emptyTextNode, imageNode)).toBe(true)
  })

  it('still blocks structurally incompatible connections', () => {
    const videoNode = createFlowNode('video-node', 100, 100) as VideoFlowNode
    const incompatibleImageTarget = createFlowNode('image-node', 300, 100) as ImageFlowNode

    expect(isNodeConnectionCompatible(videoNode, incompatibleImageTarget)).toBe(false)
  })
})
