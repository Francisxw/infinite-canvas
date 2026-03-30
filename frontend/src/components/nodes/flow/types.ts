import type { Node, NodeProps } from '@xyflow/react'

export type FlowPayloadKind = 'text' | 'image' | 'video' | 'audio'

export type FlowPayload = {
  id: string
  kind: FlowPayloadKind
  label: string
  sourceNodeId: string
  textValue?: string
  previewUrl?: string
}

export type OpenRouterProviderMode = 'platform' | 'custom'

export type OpenRouterPreferredModels = {
  text: string | null
  image: string | null
  video: string | null
}

export type OpenRouterAccountSettings = {
  mode: OpenRouterProviderMode
  has_custom_key: boolean
  key_mask: string | null
  preferred_models: OpenRouterPreferredModels
}

export type TextNodeData = {
  w: number
  h: number
  text: string
  prompt?: string
  linkedPrompt?: string
  errorMessage?: string
  isEditing?: boolean
  bold: boolean
  italic: boolean
  heading: 1 | 2 | 3
  list: boolean
  model?: string
  modelPickerOpen?: boolean
  settingsOpen?: boolean
  isGenerating?: boolean
  manualSize?: boolean
  inputPayloads?: FlowPayload[]
  outputPayloads?: FlowPayload[]
  selectedInputPayloadIds?: string[]
  selectedOutputPayloadIds?: string[]
  isConnectionCandidate?: boolean
  isConnectionHovered?: boolean
  isConnecting?: boolean
}

export type ImageNodeData = {
  w: number
  h: number
  dataUrl: string | null
  mediaWidth?: number | null
  mediaHeight?: number | null
  filename: string | null
  prompt: string
  errorMessage?: string
  model: string
  aspectRatio: '1:1' | '16:9' | '9:16' | '4:3' | '3:4'
  imageSize: '1K' | '2K' | '4K'
  numImages: number
  customCountOpen?: boolean
  modelPickerOpen?: boolean
  settingsOpen?: boolean
  quantityOpen?: boolean
  isGenerating?: boolean
  manualSize?: boolean
  inputPayloads?: FlowPayload[]
  outputPayloads?: FlowPayload[]
  selectedInputPayloadIds?: string[]
  selectedOutputPayloadIds?: string[]
  isConnectionCandidate?: boolean
  isConnectionHovered?: boolean
  isConnecting?: boolean
}

export type VideoNodeData = {
  w: number
  h: number
  dataUrl: string | null
  coverUrl?: string | null
  mediaWidth?: number | null
  mediaHeight?: number | null
  filename: string | null
  prompt: string
  errorMessage?: string
  model: string
  aspectRatio: '16:9' | '9:16' | '1:1'
  duration: '5s' | '10s'
  quality: '720p' | '1080p'
  speed: 'standard' | 'fast'
  modelPickerOpen?: boolean
  settingsOpen?: boolean
  isGenerating?: boolean
  manualSize?: boolean
  inputPayloads?: FlowPayload[]
  outputPayloads?: FlowPayload[]
  selectedInputPayloadIds?: string[]
  selectedOutputPayloadIds?: string[]
  isConnectionCandidate?: boolean
  isConnectionHovered?: boolean
  isConnecting?: boolean
}

export type FlowNodeType = 'text-node' | 'image-node' | 'video-node'

export type TextFlowNode = Node<TextNodeData, 'text-node'>
export type ImageFlowNode = Node<ImageNodeData, 'image-node'>
export type VideoFlowNode = Node<VideoNodeData, 'video-node'>

export type AnyFlowNode = TextFlowNode | ImageFlowNode | VideoFlowNode

export type TextNodeProps = NodeProps<TextFlowNode>
export type ImageNodeProps = NodeProps<ImageFlowNode>
export type VideoNodeProps = NodeProps<VideoFlowNode>
