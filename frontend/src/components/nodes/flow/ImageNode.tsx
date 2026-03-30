import { ChevronDown, Hash, ImageIcon, Settings2, Sparkles, Upload, X } from 'lucide-react'
import { useCallback, useEffect, useRef } from 'react'
import { useReactFlow } from '@xyflow/react'
import { generateImage } from '../../../services/api'
import { useAssetImport } from '../../../hooks/useAssetImport'
import { useAsyncNodeTask } from '../../../hooks/useAsyncNodeTask'
import { useOpenRouterModels } from '../../../hooks/useOpenRouterModels'
import { useCanvasDockStore } from '../../../stores/canvasDockStore'
import type { ImageFlowNode } from './types'
import { FlowNodeShell, GenerateActionButton, GenerationProgress, MediaSidePorts, NodeNotice, NodeTooltip, patchNodeData } from './common'

const IMAGE_SIZES: Array<ImageFlowNode['data']['imageSize']> = ['1K', '2K', '4K']
const IMAGE_RATIOS: Array<ImageFlowNode['data']['aspectRatio']> = ['1:1', '4:3', '3:4', '16:9', '9:16']
const IMAGE_COUNTS = [1, 2, 5]

function imageRatioLabel(value: ImageFlowNode['data']['aspectRatio']) {
  return value
}

export function ImageNode({ id, data, selected }: { id: string; data: ImageFlowNode['data']; selected: boolean }) {
  const { setNodes } = useReactFlow<ImageFlowNode>()
  const { imageModels, loading: modelsLoading, error: modelLoadError } = useOpenRouterModels()
  const addAsset = useCanvasDockStore((state) => state.addAsset)
  const nodeRef = useRef<HTMLDivElement>(null)

  const update = (patch: Partial<ImageFlowNode['data']>) => {
    patchNodeData<ImageFlowNode>(setNodes, id, patch)
  }

  const generationTask = useAsyncNodeTask<ImageFlowNode>({ kind: 'image', nodeId: id, setNodes })
  const assetImport = useAssetImport({
    onStart: () => update({ errorMessage: undefined }),
    onError: (message) => update({ errorMessage: message }),
    onImported: (result) => {
      readImageDimensions(result.mediaUrl as string)
      update({ dataUrl: result.mediaUrl, filename: result.filename, errorMessage: undefined })
      addAsset({ id: `asset-${Date.now()}`, kind: 'image', name: result.filename, createdAt: Date.now(), url: result.mediaUrl as string })
    },
  })

  const isExpanded = selected
  const previewHeight = data.mediaWidth && data.mediaHeight
    ? Math.max(180, Math.min(280, 390 * (data.mediaHeight / data.mediaWidth)))
    : 220
  const stableHeight = Math.max(292, Math.round(previewHeight + 72))
  const resolvedModel = imageModels.find((model) => model.id === data.model) ?? imageModels[0]

  const closeOverlays = () => {
    update({ modelPickerOpen: false, settingsOpen: false, quantityOpen: false, customCountOpen: false })
  }

  useEffect(() => {
    if (data.manualSize) return
    if (data.h === stableHeight) return
    update({ h: stableHeight })
  }, [data.h, data.manualSize, stableHeight])

  useEffect(() => {
    if (selected) return
    if (!data.modelPickerOpen && !data.settingsOpen && !data.quantityOpen && !data.customCountOpen) return
    closeOverlays()
  }, [selected, data.modelPickerOpen, data.settingsOpen, data.quantityOpen, data.customCountOpen])

  const readImageDimensions = (dataUrl: string) => {
    const image = new window.Image()
    image.onload = () => {
      update({ mediaWidth: image.naturalWidth, mediaHeight: image.naturalHeight })
    }
    image.src = dataUrl
  }

  const stopCanvasWheel = (event: React.WheelEvent<HTMLDivElement>) => {
    event.stopPropagation()
  }

  const onPickFile = async () => {
    closeOverlays()
    assetImport.openPicker('image/*', {
      emptyResultMessage: '图像上传结果为空，请重试。',
      failureMessage: '图像上传失败，请稍后重试。',
    })
  }

  const handlePasteFiles = useCallback(async (files: FileList | null) => {
    const fileArray = Array.from(files || [])
    const imageFile = fileArray.find((file) => file.type.startsWith('image/'))
    if (!imageFile) return
    closeOverlays()

    await assetImport.importFromClipboard(fileArray, (file) => file.type.startsWith('image/'), {
      emptyResultMessage: '图像上传结果为空，请重试。',
      failureMessage: '图像上传失败，请稍后重试。',
    })
  }, [assetImport])

  const onPasteImage = async (event: React.ClipboardEvent<HTMLDivElement>) => {
    const files = event.clipboardData.files
    if (!files || files.length === 0) return
    event.preventDefault()
    await handlePasteFiles(files)
  }

  useEffect(() => {
    if (!selected) return

    const onDocumentPaste = (event: ClipboardEvent) => {
      const target = event.target as Node | null
      if (nodeRef.current?.contains(target)) return
      const activeEl = document.activeElement
      if (activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA' || (activeEl as HTMLElement).isContentEditable)) {
        return
      }
      event.preventDefault()
      void handlePasteFiles(event.clipboardData?.files ?? null)
    }

    document.addEventListener('paste', onDocumentPaste)
    return () => document.removeEventListener('paste', onDocumentPaste)
  }, [selected, handlePasteFiles])

  const onGenerate = async () => {
    closeOverlays()
    const prompt = data.prompt || ''
    if (!prompt.trim()) return

    const task = generationTask.startTask(prompt)

    try {
      const result = await generateImage({
        provider: 'openrouter',
        prompt,
        model: data.model || imageModels[0]?.id || 'google/gemini-3.1-flash-image-preview',
        aspect_ratio: data.aspectRatio || '1:1',
        image_size: data.imageSize || '1K',
        num_images: data.numImages || 1,
        stream: false,
      }, { signal: task.controller.signal })

      const firstImage = result.images[0] ?? null
      if (firstImage) {
        readImageDimensions(firstImage)
        generationTask.finishSuccess(task, { dataUrl: firstImage, filename: 'generated.png' })
        addAsset({ id: `asset-${Date.now()}`, kind: 'image', name: 'generated.png', createdAt: Date.now(), url: firstImage })
        return
      }

      generationTask.finishError(task, '图像生成结果为空，请更换提示词后重试。')
    } catch (error) {
      const message = generationTask.resolveErrorMessage(error, '图像生成失败，请稍后重试。')
      if (!message) {
        generationTask.finishCancelled(task)
        return
      }

      generationTask.finishError(task, message)
    }
  }

  return (
    <FlowNodeShell
      id={id}
      title="Image"
      icon={<ImageIcon className="h-4 w-4" />}
      selected={selected}
      width={data.w}
      height={data.h}
      isConnectionCandidate={data.isConnectionCandidate}
      isConnectionHovered={data.isConnectionHovered}
      showUploadButton={selected}
      belowContent={
        isExpanded ? (
          <div className="relative rounded-[26px] border border-white/8 bg-[#202020] px-4 py-4 opacity-100 shadow-[0_18px_36px_rgba(0,0,0,0.28)] transition-all duration-500 ease-out animate-in fade-in slide-in-from-top-1">
            {data.modelPickerOpen || data.settingsOpen || data.quantityOpen || data.customCountOpen ? (
              <button
                type="button"
                aria-label="close image overlays"
                onClick={closeOverlays}
                className="fixed inset-0 z-10 cursor-default"
              />
            ) : null}

            <div className="mb-3 flex items-center gap-2">
              <NodeTooltip label="选择图像模型">
                <button
                  type="button"
                  onClick={() => update({ modelPickerOpen: !data.modelPickerOpen, settingsOpen: false, quantityOpen: false, customCountOpen: false })}
                  className="nodrag nopan relative z-20 inline-flex items-center gap-2 rounded-full bg-[#2a2a2a] px-3 py-1.5 text-sm text-white/86 transition hover:bg-[#313131]"
                >
                  <Sparkles className="h-4 w-4 text-white/55" />
                  <span>{resolvedModel?.label ?? '选择模型'}</span>
                  <ChevronDown className={`h-4 w-4 text-white/45 transition ${data.modelPickerOpen ? 'rotate-180' : ''}`} />
                </button>
              </NodeTooltip>
              <NodeTooltip label="图像参数设置">
                <button
                  type="button"
                  onClick={() => update({ settingsOpen: !data.settingsOpen, modelPickerOpen: false, quantityOpen: false, customCountOpen: false })}
                  className="nodrag nopan relative z-20 inline-flex items-center gap-2 rounded-full bg-[#2a2a2a] px-3 py-1.5 text-sm text-white/78 transition hover:bg-[#313131]"
                >
                  <Settings2 className="h-4 w-4 text-white/55" />
                  <span>{data.aspectRatio} · {data.imageSize}</span>
                  <ChevronDown className={`h-4 w-4 text-white/45 transition ${data.settingsOpen ? 'rotate-180' : ''}`} />
                </button>
              </NodeTooltip>
              </div>

            {data.modelPickerOpen ? (
              <div className="absolute left-4 top-14 z-30 w-[calc(100%-2rem)] overflow-hidden rounded-[20px] border border-white/10 bg-[#2a2a2a]/98 p-2 shadow-[0_22px_60px_rgba(0,0,0,0.48)] backdrop-blur-xl" onClick={(event) => event.stopPropagation()} onWheel={stopCanvasWheel} onWheelCapture={stopCanvasWheel}>
                <div className="canvas-scrollbar max-h-72 overflow-y-auto pr-1">
                  {(imageModels.length > 0 ? imageModels : []).map((model) => {
                    const active = model.id === data.model
                    return (
                      <button
                        key={model.id}
                        type="button"
                         onClick={() => update({ model: model.id, modelPickerOpen: false, settingsOpen: false, quantityOpen: false, customCountOpen: false })}
                        className={`flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left transition ${
                          active ? 'bg-white/8' : 'hover:bg-white/6'
                        } ${model.available ? 'text-white/88' : 'text-white/45'}`}
                      >
                        <span className="inline-flex h-9 w-9 items-center justify-center rounded-2xl bg-white/6 text-white/60">
                          <Sparkles className="h-4 w-4" />
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-sm">{model.label}</span>
                        </span>
                        <span className="rounded-full bg-white/6 px-2 py-1 text-[11px] text-white/45">{model.available ? model.eta : 'soon'}</span>
                      </button>
                    )
                  })}
                  {modelsLoading ? <div className="px-3 py-2 text-xs text-white/35">正在同步 OpenRouter 模型…</div> : null}
                </div>
              </div>
            ) : null}

            {data.settingsOpen ? (
              <div className="absolute left-4 top-14 z-30 w-[calc(100%-2rem)] rounded-[20px] border border-white/10 bg-[#2a2a2a]/98 p-3 shadow-[0_22px_60px_rgba(0,0,0,0.48)] backdrop-blur-xl" onClick={(event) => event.stopPropagation()} onWheel={stopCanvasWheel} onWheelCapture={stopCanvasWheel}>
                <div className="mb-2 text-xs text-white/35">画质</div>
                <div className="mb-3 grid grid-cols-3 gap-1 rounded-2xl bg-[#323232] p-1">
                  {IMAGE_SIZES.map((size) => (
                    <button
                      key={size}
                      type="button"
                        onClick={() => update({ imageSize: size, settingsOpen: false, modelPickerOpen: false, quantityOpen: false, customCountOpen: false })}
                      className={`rounded-xl px-3 py-2 text-sm transition ${data.imageSize === size ? 'bg-[#4a4a4a] text-white' : 'text-white/32 hover:text-white/68'}`}
                    >
                      {size}
                    </button>
                  ))}
                </div>

                <div className="mb-2 text-xs text-white/35">比例</div>
                <div className="grid grid-cols-5 gap-2 rounded-2xl bg-[#323232] p-3">
                  {IMAGE_RATIOS.map((ratio) => (
                    <button
                      key={ratio}
                      type="button"
                       onClick={() => update({ aspectRatio: ratio, settingsOpen: false, modelPickerOpen: false, quantityOpen: false, customCountOpen: false })}
                      className={`flex h-16 flex-col items-center justify-center gap-2 rounded-2xl border transition ${
                        data.aspectRatio === ratio ? 'border-white/24 bg-white/6 text-white' : 'border-transparent text-white/36 hover:text-white/68'
                      }`}
                    >
                      <span className="block rounded-sm border border-current" style={{ width: ratio === '1:1' ? 18 : ratio === '16:9' ? 24 : ratio === '9:16' ? 12 : 16, height: ratio === '1:1' ? 18 : ratio === '16:9' ? 14 : ratio === '9:16' ? 22 : ratio === '4:3' ? 18 : 20 }} />
                      <span className="text-[11px]">{imageRatioLabel(ratio)}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            {data.quantityOpen ? (
              <div className="absolute left-4 top-14 z-30 w-[calc(100%-2rem)] rounded-[20px] border border-white/10 bg-[#2a2a2a]/98 p-3 shadow-[0_22px_60px_rgba(0,0,0,0.48)] backdrop-blur-xl" onClick={(event) => event.stopPropagation()}>
                <div className="mb-2 text-xs text-white/35">生成数量</div>
                <div className="mb-3 grid grid-cols-4 gap-2 rounded-2xl bg-[#323232] p-2">
                  {IMAGE_COUNTS.map((count) => (
                    <button
                      key={count}
                      type="button"
                       onClick={() => update({ numImages: count, quantityOpen: false, modelPickerOpen: false, settingsOpen: false, customCountOpen: false })}
                      className={`rounded-xl px-3 py-2 text-sm transition ${
                        (data.numImages || 1) === count ? 'bg-[#4a4a4a] text-white' : 'text-white/38 hover:text-white/72'
                      }`}
                    >
                      ×{count}
                    </button>
                  ))}
                  <button
                    type="button"
                    onClick={() => update({ customCountOpen: true, quantityOpen: false, modelPickerOpen: false, settingsOpen: false })}
                    className="rounded-xl px-3 py-2 text-sm text-white/72 transition hover:bg-white/6"
                  >
                    自定义
                  </button>
                </div>
                <div className="text-[11px] text-white/35">快速选择常用数量，或进入自定义输入。</div>
              </div>
            ) : null}

            {data.customCountOpen ? (
              <div className="absolute left-4 top-14 z-30 w-[calc(100%-2rem)] rounded-[20px] border border-white/10 bg-[#2a2a2a]/98 p-3 shadow-[0_22px_60px_rgba(0,0,0,0.48)] backdrop-blur-xl" onClick={(event) => event.stopPropagation()}>
                <div className="mb-2 text-xs text-white/35">自定义数量</div>
                <label className="flex items-center gap-2 rounded-2xl border border-white/10 bg-[#232323] px-3 py-2 text-xs text-white/45">
                  输入数量
                  <input
                    type="number"
                    min={1}
                    max={8}
                    value={Math.max(1, Math.min(8, data.numImages || 1))}
                    onChange={(event) => {
                      const raw = Number(event.target.value)
                      const next = Number.isFinite(raw) ? Math.max(1, Math.min(8, Math.round(raw))) : 1
                      update({ numImages: next })
                    }}
                    className="nodrag nopan ml-auto w-16 rounded-lg border border-white/10 bg-[#1d1d1d] px-2 py-1 text-right text-sm text-white/85 outline-none"
                  />
                </label>
                <div className="mt-3 flex justify-end">
                  <button
                    type="button"
                    onClick={() => update({ customCountOpen: false })}
                    className="rounded-full bg-white/10 px-3 py-1.5 text-xs text-white/80 transition hover:bg-white/16"
                  >
                    确定
                  </button>
                </div>
              </div>
            ) : null}

            <textarea
              value={data.prompt || ''}
              onFocus={closeOverlays}
              onChange={(event) => update({ prompt: event.target.value, errorMessage: undefined })}
              placeholder="描述任何你想要生成的图像内容"
              className="nodrag nopan h-24 w-full resize-none border-0 bg-transparent px-0 py-0 text-sm text-white/84 outline-none placeholder:text-white/24"
            />

            <div className="mt-2 space-y-2">
              <NodeNotice message={modelLoadError} />
              <NodeNotice message={data.errorMessage} />
            </div>

            <div className="mt-3 flex items-center justify-between gap-3">
              <NodeTooltip label="生成数量">
                <button
                  type="button"
                  onClick={() => update({ quantityOpen: !data.quantityOpen, modelPickerOpen: false, settingsOpen: false, customCountOpen: false })}
                  className="nodrag nopan relative z-20 inline-flex h-10 items-center gap-2 rounded-full border border-white/10 bg-[#2a2a2a] px-3 py-1.5 text-sm text-white/78 transition hover:bg-[#313131]"
                >
                  <Hash className="h-4 w-4 text-white/55" />
                  <span>×{data.numImages || 1}</span>
                  <ChevronDown className={`h-4 w-4 text-white/45 transition ${data.quantityOpen ? 'rotate-180' : ''}`} />
                </button>
              </NodeTooltip>
              <NodeTooltip label="开始生成图像">
                <GenerateActionButton
                  label="生成图像"
                  points={40}
                  onClick={onGenerate}
                  disabled={!data.prompt.trim() || data.isGenerating}
                />
              </NodeTooltip>
            </div>
          </div>
        ) : null
      }
      uploadButton={
        <NodeTooltip label="上传图像素材">
          <button
            type="button"
            onClick={onPickFile}
            className="nodrag nopan pointer-events-auto inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-[#171717] px-4 py-2 text-xs text-white/80 shadow-[0_10px_24px_rgba(0,0,0,0.45)] transition hover:border-white/20 hover:bg-[#1d1d1d]"
          >
            <Upload className="h-3.5 w-3.5" />
            上传
          </button>
        </NodeTooltip>
      }
    >
      <div ref={nodeRef} className="flex h-full min-h-0 flex-col gap-2 overflow-visible" onPaste={onPasteImage}>
        <div
          data-preview-frame="image"
          className={`relative flex shrink-0 items-center justify-center overflow-visible rounded-[24px] bg-[#232323] transition-all duration-200 ${
            selected ? 'border-[3px] border-white/52' : 'border border-white/16'
          } ${data.isConnectionCandidate ? (data.isConnectionHovered ? 'border-white/72 shadow-[0_0_0_1px_rgba(255,255,255,0.18),0_0_36px_rgba(255,255,255,0.12)]' : 'border-white/30') : ''}`}
          style={{ height: previewHeight }}
        >
          <MediaSidePorts
            nodeId={id}
            active={selected}
            isConnecting={Boolean(data.isConnecting)}
            nodeType="image-node"
            inputPayloads={data.inputPayloads ?? []}
            outputPayloads={data.outputPayloads ?? []}
            selectedInputPayloadIds={data.selectedInputPayloadIds ?? []}
            selectedOutputPayloadIds={data.selectedOutputPayloadIds ?? []}
            onToggleInput={(payloadId) => update({ selectedInputPayloadIds: (data.selectedInputPayloadIds ?? []).includes(payloadId) ? (data.selectedInputPayloadIds ?? []).filter((id) => id !== payloadId) : [...(data.selectedInputPayloadIds ?? []), payloadId] })}
            onToggleOutput={(payloadId) => update({ selectedOutputPayloadIds: (data.selectedOutputPayloadIds ?? []).includes(payloadId) ? (data.selectedOutputPayloadIds ?? []).filter((id) => id !== payloadId) : [...(data.selectedOutputPayloadIds ?? []), payloadId] })}
            onSelectAllInputs={() => update({ selectedInputPayloadIds: (data.inputPayloads ?? []).map((payload) => payload.id) })}
            onSelectAllOutputs={(payloads) => update({ selectedOutputPayloadIds: payloads.map((payload) => payload.id) })}
          />
          <GenerationProgress active={Boolean(data.isGenerating)} label="图像生成中…" />
          {data.dataUrl ? (
            <div className="relative flex h-full w-full items-center justify-center overflow-hidden rounded-[inherit] bg-[#1b1b1b]">
              <img data-testid="image-node-preview-media" src={data.dataUrl} alt={data.filename ?? 'image'} className="block h-full w-full object-contain" />
              <button
                type="button"
                onClick={() => update({ dataUrl: undefined, filename: undefined, mediaWidth: undefined, mediaHeight: undefined })}
                className="nodrag nopan absolute right-2 top-2 inline-flex h-6 w-6 items-center justify-center rounded-full border border-white/16 bg-[#141414]/88 text-white/68 shadow-[0_6px_14px_rgba(0,0,0,0.24)] transition hover:border-white/28 hover:bg-[#1a1a1a] hover:text-white/88"
                aria-label="remove image"
                title="移除图像"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ) : (
            <div className="flex h-full w-full items-center justify-center overflow-hidden rounded-[inherit]">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-white/14 text-white/30 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.04)]">
                <ImageIcon className="h-8 w-8" />
              </div>
            </div>
          )}
        </div>

      </div>
    </FlowNodeShell>
  )
}
