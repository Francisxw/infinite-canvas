import { BaseBoxShapeTool } from 'tldraw'

export class ImageNodeTool extends BaseBoxShapeTool {
  static override id = 'image-node'
  static override initial = 'idle'
  override shapeType = 'image-node'
}

export class AIPromptNodeTool extends BaseBoxShapeTool {
  static override id = 'ai-prompt-node'
  static override initial = 'idle'
  override shapeType = 'ai-prompt-node'
}

export class TextNodeTool extends BaseBoxShapeTool {
  static override id = 'text-node'
  static override initial = 'idle'
  override shapeType = 'text-node'
}

export class VideoNodeTool extends BaseBoxShapeTool {
  static override id = 'video-node'
  static override initial = 'idle'
  override shapeType = 'video-node'
}
