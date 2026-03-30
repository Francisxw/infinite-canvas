import { ChevronDown, Film, Play, Settings2, Sparkles, Upload, X } from 'lucide-react'
import { useCallback, useEffect, useRef } from 'react'
import { useReactFlow } from '@xyflow/react'
import { generateVideo } from '../../../services/api'
import { useAssetImport } from '../../../hooks/useAssetImport'
import { useAsyncNodeTask } from '../../../hooks/useAsyncNodeTask'
import { useOpenRouterModels } from '../../../hooks/useOpenRouterModels'
import { useCanvasDockStore } from '../../../stores/canvasDockStore'
import type { VideoFlowNode } from './types'
import { FlowNodeShell, GenerateActionButton, GenerationProgress, MediaSidePorts, NodeNotice, NodeTooltip, patchNodeData } from './common'

const VIDEO_RATIOS: Array<VideoFlowNode['data']['aspectRatio']> = ['16:9', '9:16', '1:1']
const VIDEO_DURATIONS: Array<VideoFlowNode['data']['duration']> = ['5s', '10s']
const VIDEO_QUALITIES: Array<VideoFlowNode['data']['quality']> = ['720p', '1080p']
const VIDEO_SPEEDS: Array<VideoFlowNode['data']['speed']> = ['standard', 'fast']
const VIDEO_MODEL_EXPERIMENTAL_MESSAGE = '当前视频模型仍处于 OpenRouter 实验接入阶段，生成可能失败。'

function videoSpeedLabel(value: VideoFlowNode['data']['speed']) {
  return value === 'fast' ? '快速' : '标准'
}

export function VideoNode({ id, data, selected }: { id: string; data: VideoFlowNode['data']; selected: boolean }) {
  const { setNodes } = useReactFlow<VideoFlowNode>()
  const { videoModels, loading: modelsLoading, error: modelLoadError } = useOpenRouterModels()
  const addAsset = useCanvasDockStore((state) => state.addAsset)
  const nodeRef = useRef<HTMLDivElement>(null)

  const update = (patch: Partial<VideoFlowNode['data']>) => {
    patchNodeData<VideoFlowNode>(setNodes, id, patch)
  }

  const generationTask = useAsyncNodeTask<VideoFlowNode>({ kind: 'video', nodeId: id, setNodes })
  const assetImport = useAssetImport({
    onStart: () => update({ errorMessage: undefined }),
    onError: (message) => update({ errorMessage: message }),
    onImported: (result, file) => {
      if (file.type.startsWith('video/')) {
        readMediaDimensions(result.mediaUrl as string, 'video')
        update({ dataUrl: result.mediaUrl, coverUrl: null, filename: result.filename, errorMessage: undefined })
      } else {
        readMediaDimensions(result.mediaUrl as string, 'image')
        update({ coverUrl: result.mediaUrl, filename: result.filename, errorMessage: undefined })
      }

      addAsset({ id: `asset-${Date.now()}`, kind: 'video', name: result.filename, createdAt: Date.now(), url: result.mediaUrl as string })
    },
  })

  const isExpanded = selected
  const previewHeight = data.mediaWidth && data.mediaHeight
    ? Math.max(180, Math.min(260, 390 * (data.mediaHeight / data.mediaWidth)))
    : 220
  const stableHeight = Math.max(292, Math.round(previewHeight + 72))
  const prompt = data.prompt ?? ''
  const previewMedia = data.dataUrl || data.coverUrl
  const hasVideo = typeof data.dataUrl === 'string' && data.dataUrl.length > 0
  const resolvedModel = videoModels.find((model) => model.id === data.model) ?? videoModels[0]
  const videoModelWarning = resolvedModel && !resolvedModel.available ? VIDEO_MODEL_EXPERIMENTAL_MESSAGE : undefined

  const closeOverlays = () => {
    update({ modelPickerOpen: false, settingsOpen: false })
  }

  useEffect(() => {
    if (data.manualSize) return
    if (data.h === stableHeight) return
    update({ h: stableHeight })
  }, [data.h, data.manualSize, stableHeight])

  useEffect(() => {
    if (selected) return
    if (!data.modelPickerOpen && !data.settingsOpen) return
    closeOverlays()
  }, [selected, data.modelPickerOpen, data.settingsOpen])

  const readMediaDimensions = (dataUrl: string, mediaType: 'video' | 'image') => {
    if (mediaType === 'image') {
      const image = new window.Image()
      image.onload = () => {
        update({ mediaWidth: image.naturalWidth, mediaHeight: image.naturalHeight })
      }
      image.src = dataUrl
      return
    }

    const video = document.createElement('video')
    video.onloadedmetadata = () => {
      update({ mediaWidth: video.videoWidth, mediaHeight: video.videoHeight })
    }
    video.src = dataUrl
  }

  const stopCanvasWheel = (event: React.WheelEvent<HTMLDivElement>) => {
    event.stopPropagation()
  }

  const onPickVideo = async () => {
    closeOverlays()
    assetImport.openPicker('video/*,image/*', {
      emptyResultMessage: '视频上传结果为空，请重试。',
      failureMessage: '视频上传失败，请稍后重试。',
    })
  }

  const handlePasteFiles = useCallback(async (files: FileList | null) => {
    const fileArray = Array.from(files || [])
    const mediaFile = fileArray.find((file) => file.type.startsWith('video/') || file.type.startsWith('image/'))
    if (!mediaFile) return
    closeOverlays()

    await assetImport.importFromClipboard(fileArray, (file) => file.type.startsWith('video/') || file.type.startsWith('image/'), {
      emptyResultMessage: '视频上传结果为空，请重试。',
      failureMessage: '视频上传失败，请稍后重试。',
    })
  }, [assetImport])

  const onPasteMedia = async (event: React.ClipboardEvent<HTMLDivElement>) => {
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
    const normalizedPrompt = prompt.trim()
    if (!normalizedPrompt) return

    const task = generationTask.startTask(normalizedPrompt)

    try {
      const result = await generateVideo({
        provider: 'openrouter',
        prompt: normalizedPrompt,
        model: data.model || videoModels[0]?.id || 'google/veo-3.1',
        aspect_ratio: data.aspectRatio || '16:9',
        duration: data.duration || '5s',
        quality: data.quality || '1080p',
        speed: data.speed || 'standard',
        stream: false,
      }, { signal: task.controller.signal })

      const firstVideo = result.videos[0] ?? null
      if (firstVideo) {
        readMediaDimensions(firstVideo, 'video')
        generationTask.finishSuccess(task, { dataUrl: firstVideo, coverUrl: null, filename: 'generated.mp4' })
        addAsset({ id: `asset-${Date.now()}`, kind: 'video', name: 'generated.mp4', createdAt: Date.now(), url: firstVideo })
        return
      }

      generationTask.finishError(task, '视频生成结果为空，请更换提示词后重试。')
    } catch (error) {
      const message = generationTask.resolveErrorMessage(error, '视频生成失败，请稍后重试。')
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
      title="Video"
      icon={<Film className="h-4 w-4" />}
      selected={selected}
      width={data.w}
      height={data.h}
      isConnectionCandidate={data.isConnectionCandidate}
      isConnectionHovered={data.isConnectionHovered}
      showUploadButton={selected}
      belowContent={
        isExpanded ? (
          <div className="relative rounded-[26px] border border-white/8 bg-[#202020] px-4 py-4 opacity-100 shadow-[0_18px_36px_rgba(0,0,0,0.28)] transition-all duration-500 ease-out animate-in fade-in slide-in-from-top-1">
            {data.modelPickerOpen || data.settingsOpen ? (
              <button
                type="button"
                aria-label="close video overlays"
                onClick={closeOverlays}
                className="fixed inset-0 z-10 cursor-default"
              />
            ) : null}

            <div className="mb-3 flex items-center gap-2">
              <NodeTooltip label="选择视频模型">
                <button
                  type="button"
                  onClick={() => update({ modelPickerOpen: !data.modelPickerOpen, settingsOpen: false })}
                  className="nodrag nopan relative z-20 inline-flex items-center gap-2 rounded-full bg-[#2a2a2a] px-3 py-1.5 text-sm text-white/86 transition hover:bg-[#313131]"
                >
                  <Sparkles className="h-4 w-4 text-white/55" />
                  <span>{resolvedModel?.label ?? '选择模型'}</span>
                  <ChevronDown className={`h-4 w-4 text-white/45 transition ${data.modelPickerOpen ? 'rotate-180' : ''}`} />
                </button>
              </NodeTooltip>
              <NodeTooltip label="视频参数设置">
                <button
                  type="button"
                  onClick={() => update({ settingsOpen: !data.settingsOpen, modelPickerOpen: false })}
                  className="nodrag nopan relative z-20 inline-flex items-center gap-2 rounded-full bg-[#2a2a2a] px-3 py-1.5 text-sm text-white/78 transition hover:bg-[#313131]"
                >
                  <Settings2 className="h-4 w-4 text-white/55" />
                  <span>{data.aspectRatio} · {data.quality} · {videoSpeedLabel(data.speed || 'standard')}</span>
                  <ChevronDown className={`h-4 w-4 text-white/45 transition ${data.settingsOpen ? 'rotate-180' : ''}`} />
                </button>
              </NodeTooltip>
            </div>

            {data.modelPickerOpen ? (
              <div className="absolute left-4 top-14 z-30 w-[calc(100%-2rem)] overflow-hidden rounded-[20px] border border-white/10 bg-[#2a2a2a]/98 p-2 shadow-[0_22px_60px_rgba(0,0,0,0.48)] backdrop-blur-xl" onClick={(event) => event.stopPropagation()} onWheel={stopCanvasWheel} onWheelCapture={stopCanvasWheel}>
                <div className="canvas-scrollbar max-h-72 overflow-y-auto pr-1">
                  {videoModels.map((model) => {
                    const active = model.id === data.model
                    return (
                      <button
                        key={model.id}
                        type="button"
                        onClick={() => update({ model: model.id, modelPickerOpen: false, settingsOpen: false })}
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
                        <span className="rounded-full bg-white/6 px-2 py-1 text-[11px] text-white/45">{model.available ? model.eta : 'alpha'}</span>
                      </button>
                    )
                  })}
                  {modelsLoading ? <div className="px-3 py-2 text-xs text-white/35">正在同步 OpenRouter 模型…</div> : null}
                </div>
              </div>
            ) : null}

            {data.settingsOpen ? (
              <div className="absolute left-4 top-14 z-30 w-[calc(100%-2rem)] rounded-[20px] border border-white/10 bg-[#2a2a2a]/98 p-3 shadow-[0_22px_60px_rgba(0,0,0,0.48)] backdrop-blur-xl" onClick={(event) => event.stopPropagation()} onWheel={stopCanvasWheel} onWheelCapture={stopCanvasWheel}>
                <div className="mb-2 text-xs text-white/35">比例</div>
                <div className="mb-3 grid grid-cols-3 gap-2 rounded-2xl bg-[#323232] p-2 text-xs">
                  {VIDEO_RATIOS.map((ratio) => (
                    <button
                      key={ratio}
                      type="button"
                      onClick={() => update({ aspectRatio: ratio })}
                      className={`rounded-xl px-3 py-2 transition ${data.aspectRatio === ratio ? 'bg-[#4a4a4a] text-white' : 'text-white/38 hover:text-white/68'}`}
                    >
                      {ratio}
                    </button>
                  ))}
                </div>

                <div className="mb-2 text-xs text-white/35">时长</div>
                <div className="mb-3 grid grid-cols-2 gap-2 rounded-2xl bg-[#323232] p-2 text-xs">
                  {VIDEO_DURATIONS.map((duration) => (
                    <button
                      key={duration}
                      type="button"
                      onClick={() => update({ duration })}
                      className={`rounded-xl px-3 py-2 transition ${data.duration === duration ? 'bg-[#4a4a4a] text-white' : 'text-white/38 hover:text-white/68'}`}
                    >
                      {duration}
                    </button>
                  ))}
                </div>

                <div className="mb-2 text-xs text-white/35">画质</div>
                <div className="mb-3 grid grid-cols-2 gap-2 rounded-2xl bg-[#323232] p-2 text-xs">
                  {VIDEO_QUALITIES.map((quality) => (
                    <button
                      key={quality}
                      type="button"
                      onClick={() => update({ quality })}
                      className={`rounded-xl px-3 py-2 transition ${data.quality === quality ? 'bg-[#4a4a4a] text-white' : 'text-white/38 hover:text-white/68'}`}
                    >
                      {quality}
                    </button>
                  ))}
                </div>

                <div className="mb-2 text-xs text-white/35">速度</div>
                <div className="grid grid-cols-2 gap-2 rounded-2xl bg-[#323232] p-2 text-xs">
                  {VIDEO_SPEEDS.map((speed) => (
                    <button
                      key={speed}
                      type="button"
                      onClick={() => update({ speed })}
                      className={`rounded-xl px-3 py-2 transition ${(data.speed || 'standard') === speed ? 'bg-[#4a4a4a] text-white' : 'text-white/38 hover:text-white/68'}`}
                    >
                      {videoSpeedLabel(speed)}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            <textarea
              value={prompt}
              onFocus={closeOverlays}
              onChange={(event) => update({ prompt: event.target.value, errorMessage: undefined })}
              placeholder="描述任何你想要生成的视频内容"
              className="nodrag nopan h-24 w-full resize-none border-0 bg-transparent px-0 py-0 text-sm text-white/84 outline-none placeholder:text-white/24"
            />

            <div className="mt-2 space-y-2">
              <NodeNotice message={videoModelWarning} tone="warning" />
              <NodeNotice message={modelLoadError} />
              <NodeNotice message={data.errorMessage} />
            </div>

            <div className="mt-3 flex items-center justify-end gap-3">
              <NodeTooltip label="调用视频生成接口">
                <GenerateActionButton
                  label="生成视频"
                  points={60}
                  onClick={onGenerate}
                  disabled={!prompt.trim() || data.isGenerating}
                />
              </NodeTooltip>
            </div>
          </div>
        ) : null
      }
      uploadButton={
        <NodeTooltip label="上传视频或封面素材">
          <button
            type="button"
            onClick={onPickVideo}
            className="nodrag nopan pointer-events-auto inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-[#171717] px-4 py-2 text-xs text-white/80 shadow-[0_10px_24px_rgba(0,0,0,0.45)] transition hover:border-white/20 hover:bg-[#1d1d1d]"
          >
            <Upload className="h-3.5 w-3.5" />
            上传
          </button>
        </NodeTooltip>
      }
    >
      <div ref={nodeRef} className="flex h-full min-h-0 flex-col gap-2 overflow-visible" onPaste={onPasteMedia}>
        <div
          data-preview-frame="video"
          className={`relative flex shrink-0 items-center justify-center overflow-visible rounded-[24px] bg-[#232323] transition-all duration-200 ${
            selected ? 'border-[3px] border-white/52' : 'border border-white/16'
          } ${data.isConnectionCandidate ? (data.isConnectionHovered ? 'border-white/72 shadow-[0_0_0_1px_rgba(255,255,255,0.18),0_0_36px_rgba(255,255,255,0.12)]' : 'border-white/30') : ''}`}
          style={{ height: previewHeight }}
        >
          <MediaSidePorts
            nodeId={id}
            active={selected}
            isConnecting={Boolean(data.isConnecting)}
            nodeType="video-node"
            inputPayloads={data.inputPayloads ?? []}
            outputPayloads={data.outputPayloads ?? []}
            selectedInputPayloadIds={data.selectedInputPayloadIds ?? []}
            selectedOutputPayloadIds={data.selectedOutputPayloadIds ?? []}
            onToggleInput={(payloadId) => update({ selectedInputPayloadIds: (data.selectedInputPayloadIds ?? []).includes(payloadId) ? (data.selectedInputPayloadIds ?? []).filter((selectedId) => selectedId !== payloadId) : [...(data.selectedInputPayloadIds ?? []), payloadId] })}
            onToggleOutput={(payloadId) => update({ selectedOutputPayloadIds: (data.selectedOutputPayloadIds ?? []).includes(payloadId) ? (data.selectedOutputPayloadIds ?? []).filter((selectedId) => selectedId !== payloadId) : [...(data.selectedOutputPayloadIds ?? []), payloadId] })}
            onSelectAllInputs={() => update({ selectedInputPayloadIds: (data.inputPayloads ?? []).map((payload) => payload.id) })}
            onSelectAllOutputs={(payloads) => update({ selectedOutputPayloadIds: payloads.map((payload) => payload.id) })}
          />
          <GenerationProgress active={Boolean(data.isGenerating)} label="视频生成中…" />
          {hasVideo ? (
            <div className="relative flex h-full w-full items-center justify-center">
              <video src={data.dataUrl ?? undefined} controls className="h-full w-full rounded-[inherit] object-cover" />
              <button
                type="button"
                onClick={() => update({ dataUrl: undefined, coverUrl: undefined, filename: undefined, mediaWidth: undefined, mediaHeight: undefined })}
                className="nodrag nopan absolute right-3 top-3 inline-flex h-8 w-8 items-center justify-center rounded-full border border-white/16 bg-[#141414]/90 text-white/70 shadow-[0_8px_16px_rgba(0,0,0,0.28)] transition hover:border-white/28 hover:bg-[#1a1a1a] hover:text-white/90"
                aria-label="remove video"
                title="移除视频"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : previewMedia ? (
            <div className="relative flex h-full w-full items-center justify-center">
              <img src={previewMedia} alt={data.filename ?? 'video preview'} className="h-full w-full rounded-[inherit] object-cover" />
              <button
                type="button"
                onClick={() => update({ dataUrl: undefined, coverUrl: undefined, filename: undefined, mediaWidth: undefined, mediaHeight: undefined })}
                className="nodrag nopan absolute right-3 top-3 inline-flex h-8 w-8 items-center justify-center rounded-full border border-white/16 bg-[#141414]/90 text-white/70 shadow-[0_8px_16px_rgba(0,0,0,0.28)] transition hover:border-white/28 hover:bg-[#1a1a1a] hover:text-white/90"
                aria-label="remove cover"
                title="移除封面"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <div className="flex h-full w-full items-center justify-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-white/14 text-white/30 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.04)]">
                <Play className="ml-1 h-8 w-8" />
              </div>
            </div>
          )}
        </div>
      </div>
    </FlowNodeShell>
  )
}
