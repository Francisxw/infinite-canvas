import {
  BaseBoxShapeUtil,
  HTMLContainer,
  Rectangle2d,
  createShapeId,
  type TLResizeInfo,
  type TLShapePartial,
  resizeBox,
} from 'tldraw'
import { Sparkles } from 'lucide-react'
import { generateImage } from '../../../services/api'
import type { AIPromptNodeShape } from './types'
import { NodeFrame, RoundedCard, getBoxPortHandles } from './common'

const MODELS = [
  'google/gemini-2.5-flash-image-preview',
  'google/gemini-3.1-flash-image-preview',
  'black-forest-labs/flux.2-pro',
]

export class AIPromptNodeShapeUtil extends BaseBoxShapeUtil<AIPromptNodeShape> {
  static override type = 'ai-prompt-node' as const

  override getDefaultProps(): AIPromptNodeShape['props'] {
    return {
      w: 660,
      h: 240,
      prompt: '',
      model: MODELS[0],
      aspectRatio: '1:1',
      imageSize: '1K',
      numImages: 1,
      generatedDataUrl: null,
    }
  }

  override canResize() {
    return true
  }

  override getHandles(shape: AIPromptNodeShape) {
    return getBoxPortHandles(shape.props.w, shape.props.h)
  }

  override getGeometry(shape: AIPromptNodeShape) {
    return new Rectangle2d({ width: shape.props.w, height: shape.props.h, isFilled: true })
  }

  override onResize(shape: AIPromptNodeShape, info: TLResizeInfo<AIPromptNodeShape>) {
    return resizeBox(shape, info)
  }

  component(shape: AIPromptNodeShape) {
    const updateProps = (props: Partial<AIPromptNodeShape['props']>) => {
      const partial: TLShapePartial<AIPromptNodeShape> = {
        id: shape.id,
        type: shape.type,
        props,
      }
      this.editor.updateShapes([partial])
    }

    const handleGenerate = async () => {
      if (!shape.props.prompt.trim()) return
      const result = await generateImage({
        provider: 'openrouter',
        prompt: shape.props.prompt,
        model: shape.props.model,
        aspect_ratio: shape.props.aspectRatio,
        image_size: shape.props.imageSize,
        num_images: shape.props.numImages,
        stream: false,
      })

      const firstImage =
        result?.choices?.[0]?.message?.images?.[0]?.image_url?.url ||
        result?.choices?.[0]?.message?.images?.[0]?.imageUrl?.url ||
        null

      updateProps({ generatedDataUrl: firstImage })

      if (firstImage) {
        this.editor.createShape({
          id: createShapeId(),
          type: 'image-node',
          x: shape.x,
          y: shape.y + shape.props.h + 64,
          props: {
            w: 460,
            h: 300,
            dataUrl: firstImage,
            filename: 'generated.png',
          },
        })
      }
    }

    return (
      <HTMLContainer style={{ pointerEvents: 'all' }}>
        <NodeFrame title="Prompt" icon={<Sparkles className="h-4 w-4" />}>
          <RoundedCard>
            <div className="flex h-full flex-col gap-3">
              {shape.props.generatedDataUrl ? (
                <div className="h-28 overflow-hidden rounded-xl border border-white/10 bg-black/30">
                  <img
                    src={shape.props.generatedDataUrl}
                    alt="generated preview"
                    className="h-full w-full object-cover"
                  />
                </div>
              ) : null}
              <textarea
                value={shape.props.prompt}
                onChange={(e) => updateProps({ prompt: e.target.value })}
                placeholder="描述任何你想要生成的内容"
                className="h-24 w-full resize-none rounded-xl border border-white/10 bg-[#1c1c1c] px-3 py-2 text-sm text-gray-200 outline-none placeholder:text-gray-500"
              />

              <div className="flex flex-wrap items-center gap-2 text-sm">
                <select
                  value={shape.props.model}
                  onChange={(e) => updateProps({ model: e.target.value })}
                  className="rounded-lg border border-white/10 bg-[#232323] px-2 py-1"
                >
                  {MODELS.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>

                <select
                  value={shape.props.imageSize}
                  onChange={(e) => updateProps({ imageSize: e.target.value as '1K' | '2K' | '4K' })}
                  className="rounded-lg border border-white/10 bg-[#232323] px-2 py-1"
                >
                  <option value="1K">1K</option>
                  <option value="2K">2K</option>
                  <option value="4K">4K</option>
                </select>

                <select
                  value={shape.props.aspectRatio}
                  onChange={(e) =>
                    updateProps({ aspectRatio: e.target.value as '1:1' | '16:9' | '9:16' | '4:3' | '3:4' })
                  }
                  className="rounded-lg border border-white/10 bg-[#232323] px-2 py-1"
                >
                  <option value="1:1">1:1</option>
                  <option value="16:9">16:9</option>
                  <option value="9:16">9:16</option>
                  <option value="4:3">4:3</option>
                  <option value="3:4">3:4</option>
                </select>

                <input
                  type="number"
                  min={1}
                  max={4}
                  value={shape.props.numImages}
                  onChange={(e) => updateProps({ numImages: Math.max(1, Math.min(4, Number(e.target.value || 1))) })}
                  className="w-16 rounded-lg border border-white/10 bg-[#232323] px-2 py-1"
                />

                <button
                  type="button"
                  onClick={handleGenerate}
                  className="ml-auto rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs hover:bg-white/20"
                >
                  生成
                </button>
              </div>
            </div>
          </RoundedCard>
        </NodeFrame>
      </HTMLContainer>
    )
  }

  indicator(_shape: AIPromptNodeShape) {
    return null
  }
}
