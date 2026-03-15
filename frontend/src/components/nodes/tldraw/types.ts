import type { TLBaseShape } from 'tldraw'

declare module 'tldraw' {
  interface TLGlobalShapePropsMap {
    'image-node': {
      w: number
      h: number
      dataUrl: string | null
      filename: string | null
    }
    'ai-prompt-node': {
      w: number
      h: number
      prompt: string
      model: string
      aspectRatio: '1:1' | '16:9' | '9:16' | '4:3' | '3:4'
      imageSize: '1K' | '2K' | '4K'
      numImages: number
      generatedDataUrl: string | null
    }
    'text-node': {
      w: number
      h: number
      text: string
    }
    'video-node': {
      w: number
      h: number
      dataUrl: string | null
      filename: string | null
    }
  }
}

export type ImageNodeShape = TLBaseShape<
  'image-node',
  {
    w: number
    h: number
    dataUrl: string | null
    filename: string | null
  }
>

export type AIPromptNodeShape = TLBaseShape<
  'ai-prompt-node',
  {
    w: number
    h: number
    prompt: string
    model: string
    aspectRatio: '1:1' | '16:9' | '9:16' | '4:3' | '3:4'
    imageSize: '1K' | '2K' | '4K'
    numImages: number
    generatedDataUrl: string | null
  }
>

export type TextNodeShape = TLBaseShape<
  'text-node',
  {
    w: number
    h: number
    text: string
  }
>

export type VideoNodeShape = TLBaseShape<
  'video-node',
  {
    w: number
    h: number
    dataUrl: string | null
    filename: string | null
  }
>
