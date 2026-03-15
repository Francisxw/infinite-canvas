export type NodeKind = 'text' | 'image' | 'video' | 'audio' | 'ai-prompt'

export interface BaseNodeData {
  id: string
  kind: NodeKind
  x: number
  y: number
  width: number
  height: number
}

export interface ImageNodeData extends BaseNodeData {
  kind: 'image'
  dataUrl?: string
  filename?: string
}

export interface AIPromptNodeData extends BaseNodeData {
  kind: 'ai-prompt'
  prompt: string
  model: string
  aspectRatio: '1:1' | '16:9' | '9:16' | '4:3' | '3:4'
  imageSize: '1K' | '2K' | '4K'
  numImages: number
}
