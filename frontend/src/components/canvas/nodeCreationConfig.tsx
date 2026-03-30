import type { LucideIcon } from 'lucide-react'
import { ImageIcon, Type, Video } from 'lucide-react'
import type { FlowNodeType } from '../nodes/flow/types'

export type NodeCreationItem = {
  type: FlowNodeType
  label: string
  description: string
  icon: LucideIcon
  dockTestId: string
  dockAriaLabel: string
}

export const NODE_CREATION_ITEMS: NodeCreationItem[] = [
  {
    type: 'text-node',
    label: '文本',
    description: '创建文本卡片',
    icon: Type,
    dockTestId: 'dock-create-text',
    dockAriaLabel: 'dock create text node',
  },
  {
    type: 'image-node',
    label: '图片',
    description: '创建图像卡片',
    icon: ImageIcon,
    dockTestId: 'dock-create-image',
    dockAriaLabel: 'dock create image node',
  },
  {
    type: 'video-node',
    label: '视频',
    description: '创建视频卡片',
    icon: Video,
    dockTestId: 'dock-create-video',
    dockAriaLabel: 'dock create video node',
  },
]
