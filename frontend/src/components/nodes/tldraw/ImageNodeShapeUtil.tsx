import {
  BaseBoxShapeUtil,
  HTMLContainer,
  Rectangle2d,
  type TLResizeInfo,
  type TLShapePartial,
  resizeBox,
} from 'tldraw'
import { ImageIcon, Upload } from 'lucide-react'
import { uploadAsset } from '../../../services/api'
import type { ImageNodeShape } from './types'
import { NodeFrame, RoundedCard, getBoxPortHandles } from './common'

export class ImageNodeShapeUtil extends BaseBoxShapeUtil<ImageNodeShape> {
  static override type = 'image-node' as const

  override getDefaultProps(): ImageNodeShape['props'] {
    return {
      w: 460,
      h: 300,
      dataUrl: null,
      filename: null,
    }
  }

  override canResize() {
    return true
  }

  override getHandles(shape: ImageNodeShape) {
    return getBoxPortHandles(shape.props.w, shape.props.h)
  }

  override getGeometry(shape: ImageNodeShape) {
    return new Rectangle2d({
      width: shape.props.w,
      height: shape.props.h,
      isFilled: true,
    })
  }

  override onResize(shape: ImageNodeShape, info: TLResizeInfo<ImageNodeShape>) {
    return resizeBox(shape, info)
  }

  component(shape: ImageNodeShape) {
    const onPickFile = async () => {
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = 'image/*'
      input.onchange = async () => {
        const file = input.files?.[0]
        if (!file) return
        const result = await uploadAsset(file)
        const partial: TLShapePartial<ImageNodeShape> = {
          id: shape.id,
          type: shape.type,
          props: {
            dataUrl: result.data_url,
            filename: result.filename,
          },
        }
        this.editor.updateShapes([partial])
      }
      input.click()
    }

    return (
      <HTMLContainer style={{ pointerEvents: 'all' }}>
        <NodeFrame title="Image" icon={<ImageIcon className="h-4 w-4" />}>
          <div className="mb-2 flex justify-center">
            <button
              type="button"
              onClick={onPickFile}
              className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-[#212121] px-4 py-2 text-sm text-gray-100 shadow"
            >
              <Upload className="h-4 w-4" />
              上传
            </button>
          </div>
          <RoundedCard>
            <button
              type="button"
              onClick={onPickFile}
              className="flex h-full w-full items-center justify-center rounded-2xl border border-white/20 bg-[#252525]"
            >
              {shape.props.dataUrl ? (
                <img
                  src={shape.props.dataUrl}
                  alt={shape.props.filename ?? 'uploaded'}
                  className="h-full w-full rounded-2xl object-cover"
                />
              ) : (
                <span className="inline-flex h-16 w-16 items-center justify-center rounded-xl border border-white/20 text-white/45">
                  <ImageIcon className="h-8 w-8" />
                </span>
              )}
            </button>
          </RoundedCard>
        </NodeFrame>
      </HTMLContainer>
    )
  }

  indicator(_shape: ImageNodeShape) {
    return null
  }
}
