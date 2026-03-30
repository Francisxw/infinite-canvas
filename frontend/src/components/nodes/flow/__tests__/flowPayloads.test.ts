import { describe, expect, it } from 'vitest'
import { buildNodeOutputs } from '../../../canvas/flowPayloads'
import type { ImageFlowNode, TextFlowNode, VideoFlowNode } from '../types'

describe('buildNodeOutputs', () => {
  it('text node outputs text payload when text exists', () => {
    const node = {
      id: 'text-1',
      type: 'text-node' as const,
      data: {
        text: 'Hello world',
        prompt: '',
        w: 320,
        h: 200,
      },
      position: { x: 0, y: 0 },
    }
    const outputs = buildNodeOutputs(node as unknown as TextFlowNode)
    expect(outputs).toHaveLength(1)
    expect(outputs[0]).toMatchObject({
      kind: 'text',
      textValue: 'Hello world',
    })
  })

  it('text node outputs empty array when text is empty', () => {
    const node = {
      id: 'text-1',
      type: 'text-node' as const,
      data: {
        text: '',
        prompt: '',
        w: 320,
        h: 200,
      },
      position: { x: 0, y: 0 },
    }
    const outputs = buildNodeOutputs(node as unknown as TextFlowNode)
    expect(outputs).toHaveLength(0)
  })

  it('image node outputs only image payload when dataUrl exists', () => {
    const node = {
      id: 'image-1',
      type: 'image-node' as const,
      data: {
        prompt: 'A beautiful sunset', // Should be ignored in output
        dataUrl: 'data:image/png;base64,abc123',
        filename: 'sunset.png',
        w: 320,
        h: 400,
      },
      position: { x: 0, y: 0 },
    }
    const outputs = buildNodeOutputs(node as unknown as ImageFlowNode)
    expect(outputs).toHaveLength(1)
    expect(outputs[0]).toMatchObject({
      kind: 'image',
      previewUrl: 'data:image/png;base64,abc123',
      label: 'sunset.png',
    })
  })

  it('image node outputs empty array when no dataUrl exists', () => {
    const node = {
      id: 'image-1',
      type: 'image-node' as const,
      data: {
        prompt: 'A beautiful sunset', // Should be ignored - not output as text
        dataUrl: '',
        w: 320,
        h: 400,
      },
      position: { x: 0, y: 0 },
    }
    const outputs = buildNodeOutputs(node as unknown as ImageFlowNode)
    expect(outputs).toHaveLength(0)
  })

  it('video node outputs only video payload when dataUrl exists', () => {
    const node = {
      id: 'video-1',
      type: 'video-node' as const,
      data: {
        prompt: 'A dancing cat', // Should be ignored in output
        dataUrl: 'https://example.com/video.mp4',
        filename: 'dance.mp4',
        w: 320,
        h: 400,
      },
      position: { x: 0, y: 0 },
    }
    const outputs = buildNodeOutputs(node as unknown as VideoFlowNode)
    expect(outputs).toHaveLength(1)
    expect(outputs[0]).toMatchObject({
      kind: 'video',
      previewUrl: 'https://example.com/video.mp4',
      label: 'dance.mp4',
    })
  })

  it('video node outputs video payload with coverUrl when no dataUrl', () => {
    const node = {
      id: 'video-1',
      type: 'video-node' as const,
      data: {
        prompt: 'A dancing cat',
        dataUrl: '',
        coverUrl: 'https://example.com/cover.jpg',
        filename: 'preview.jpg',
        w: 320,
        h: 400,
      },
      position: { x: 0, y: 0 },
    }
    const outputs = buildNodeOutputs(node as unknown as VideoFlowNode)
    expect(outputs).toHaveLength(1)
    expect(outputs[0]).toMatchObject({
      kind: 'video',
      previewUrl: 'https://example.com/cover.jpg',
    })
  })

  it('video node outputs empty array when no media exists', () => {
    const node = {
      id: 'video-1',
      type: 'video-node' as const,
      data: {
        prompt: 'A dancing cat', // Should be ignored - not output as text
        dataUrl: '',
        coverUrl: '',
        w: 320,
        h: 400,
      },
      position: { x: 0, y: 0 },
    }
    const outputs = buildNodeOutputs(node as unknown as VideoFlowNode)
    expect(outputs).toHaveLength(0)
  })
})
