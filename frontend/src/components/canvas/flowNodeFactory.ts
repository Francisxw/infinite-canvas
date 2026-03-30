import type { Edge } from '@xyflow/react'
import type { AnyFlowNode, FlowNodeType, ImageNodeData, TextNodeData, VideoNodeData } from '../nodes/flow/types'
import { useAccountStore } from '../../stores/accountStore'



const DEFAULT_TEXT_MODEL = 'google/gemini-2.5-flash'
const DEFAULT_IMAGE_MODEL = 'google/gemini-3.1-flash-image-preview'
const DEFAULT_VIDEO_MODEL = 'google/veo-3.1'

const DEFAULT_TEXT_NODE: TextNodeData = {
  w: 360,
  h: 280,
  text: '',
  bold: false,
  italic: false,
  heading: 1,
  list: false,
  model: DEFAULT_TEXT_MODEL,
  modelPickerOpen: false,
  settingsOpen: false,
  inputPayloads: [],
  selectedInputPayloadIds: [],
  selectedOutputPayloadIds: [],
}

const DEFAULT_IMAGE_NODE: ImageNodeData = {
  w: 430,
  h: 360,
  dataUrl: null,
  mediaWidth: null,
  mediaHeight: null,
  filename: null,
  prompt: '',
  model: DEFAULT_IMAGE_MODEL,
  aspectRatio: '1:1',
  imageSize: '1K',
  numImages: 1,
  customCountOpen: false,
  modelPickerOpen: false,
  settingsOpen: false,
  inputPayloads: [],
  selectedInputPayloadIds: [],
  selectedOutputPayloadIds: [],
}

const DEFAULT_VIDEO_NODE: VideoNodeData = {
  w: 430,
  h: 360,
  dataUrl: null,
  coverUrl: null,
  mediaWidth: null,
  mediaHeight: null,
  filename: null,
  prompt: '',
  model: DEFAULT_VIDEO_MODEL,
  aspectRatio: '16:9',
  duration: '5s',
  quality: '1080p',
  speed: 'standard',
  modelPickerOpen: false,
  settingsOpen: false,
  inputPayloads: [],
  selectedInputPayloadIds: [],
  selectedOutputPayloadIds: [],
}

function resolveDefaultModel(type: FlowNodeType) {
  const openRouterSettings = useAccountStore.getState().profile?.openrouter

  if (type === 'text-node') {
    return openRouterSettings?.preferred_models.text ?? DEFAULT_TEXT_MODEL
  }

  if (type === 'image-node') {
    return openRouterSettings?.preferred_models.image ?? DEFAULT_IMAGE_MODEL
  }

  return openRouterSettings?.preferred_models.video ?? DEFAULT_VIDEO_MODEL
}

export function makeNodeData(type: FlowNodeType) {
  if (type === 'text-node') {
    return {
      ...DEFAULT_TEXT_NODE,
      model: resolveDefaultModel(type),
      inputPayloads: [],
      selectedInputPayloadIds: [],
      selectedOutputPayloadIds: [],
    }
  }

  if (type === 'image-node') {
    return {
      ...DEFAULT_IMAGE_NODE,
      model: resolveDefaultModel(type),
      inputPayloads: [],
      selectedInputPayloadIds: [],
      selectedOutputPayloadIds: [],
    }
  }

  return {
    ...DEFAULT_VIDEO_NODE,
    model: resolveDefaultModel(type),
    inputPayloads: [],
    selectedInputPayloadIds: [],
    selectedOutputPayloadIds: [],
  }
}

export function createFlowNode(type: FlowNodeType, x: number, y: number, existingNodes?: AnyFlowNode[]): AnyFlowNode {
  const id = `${type}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  const data = makeNodeData(type)
  let px = x - data.w / 2
  let py = y - data.h / 2

  if (existingNodes && existingNodes.length > 0) {
    const GAP = 20
    const STEP = 40
    let attempts = 0
    while (attempts < 20) {
      const overlaps = existingNodes.some((n) => {
        const nw = (n.data as { w?: number }).w ?? 360
        const nh = (n.data as { h?: number }).h ?? 280
        return (
          px < n.position.x + nw + GAP &&
          px + data.w + GAP > n.position.x &&
          py < n.position.y + nh + GAP &&
          py + data.h + GAP > n.position.y
        )
      })
      if (!overlaps) break
      px += STEP
      py += STEP
      attempts++
    }
  }

  return {
    id,
    type,
    position: { x: px, y: py },
    data,
    style: { width: data.w, height: data.h },
  } as AnyFlowNode
}

export function createInitialCanvasState(): { nodes: AnyFlowNode[]; edges: Edge[] } {
  return {
    nodes: [],
    edges: [],
  }
}
