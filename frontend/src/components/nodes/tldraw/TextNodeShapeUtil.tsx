import {
  BaseBoxShapeUtil,
  HTMLContainer,
  Rectangle2d,
  type TLResizeInfo,
  type TLShapePartial,
  resizeBox,
} from 'tldraw'
import { AlignLeft, Bold, Heading1, Heading2, Heading3, Italic, List } from 'lucide-react'
import type { TextNodeShape } from './types'
import { NodeFrame, RoundedCard, getBoxPortHandles } from './common'

export class TextNodeShapeUtil extends BaseBoxShapeUtil<TextNodeShape> {
  static override type = 'text-node' as const

  override getDefaultProps(): TextNodeShape['props'] {
    return {
      w: 360,
      h: 360,
      text: '开启你的创作...',
    }
  }

  override canResize() {
    return true
  }

  override getHandles(shape: TextNodeShape) {
    return getBoxPortHandles(shape.props.w, shape.props.h)
  }

  override getGeometry(shape: TextNodeShape) {
    return new Rectangle2d({ width: shape.props.w, height: shape.props.h, isFilled: true })
  }

  override onResize(shape: TextNodeShape, info: TLResizeInfo<TextNodeShape>) {
    return resizeBox(shape, info)
  }

  component(shape: TextNodeShape) {
    const updateProps = (props: Partial<TextNodeShape['props']>) => {
      const partial: TLShapePartial<TextNodeShape> = {
        id: shape.id,
        type: shape.type,
        props,
      }
      this.editor.updateShapes([partial])
    }

    return (
      <HTMLContainer style={{ pointerEvents: 'all' }}>
        <NodeFrame title="Text" icon={<AlignLeft className="h-4 w-4" />}>
          <RoundedCard>
            <div className="flex h-full flex-col gap-3">
              <div className="flex items-center gap-2 rounded-full border border-white/10 bg-[#222] px-3 py-2 text-xs text-gray-300">
                <Heading1 className="h-3.5 w-3.5" />
                <Heading2 className="h-3.5 w-3.5" />
                <Heading3 className="h-3.5 w-3.5" />
                <Bold className="h-3.5 w-3.5" />
                <Italic className="h-3.5 w-3.5" />
                <List className="h-3.5 w-3.5" />
              </div>

              <textarea
                value={shape.props.text}
                onChange={(e) => updateProps({ text: e.target.value })}
                className="h-full w-full resize-none rounded-2xl border border-white/10 bg-[#232323] p-4 text-3xl text-gray-300 outline-none"
              />
            </div>
          </RoundedCard>
        </NodeFrame>
      </HTMLContainer>
    )
  }

  indicator(_shape: TextNodeShape) {
    return null
  }
}
