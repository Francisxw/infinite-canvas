import { ChevronDown, Hash, List, Settings2, Sparkles, Wand2 } from 'lucide-react'
import { useEffect } from 'react'
import { useReactFlow } from '@xyflow/react'
import { generateText } from '../../../services/api'
import { useAsyncNodeTask } from '../../../hooks/useAsyncNodeTask'
import { useCanvasDockStore } from '../../../stores/canvasDockStore'
import type { TextFlowNode } from './types'
import { EMPTY_TEXT_PLACEHOLDER, FlowNodeShell, GenerateActionButton, GenerationProgress, MediaSidePorts, NodeNotice, NodeTooltip, patchNodeData } from './common'

const TEXT_MODELS = [
  { id: 'google/gemini-2.5-flash', label: 'Gemini 2.5 Flash', eta: 'fast' },
  { id: 'google/gemini-3.1-flash', label: 'Gemini 3.1 Flash', eta: 'fast' },
  { id: 'google/gemini-3-pro', label: 'Gemini 3 Pro', eta: 'pro' },
]

const TEXT_FORMATS = [
  { id: 1 as const, label: 'Large' },
  { id: 2 as const, label: 'Medium' },
  { id: 3 as const, label: 'Compact' },
]

export function TextNode({ id, data, selected }: { id: string; data: TextFlowNode['data']; selected: boolean }) {
  const { setNodes } = useReactFlow<TextFlowNode>()
  const addAsset = useCanvasDockStore((state) => state.addAsset)

  const update = (patch: Partial<TextFlowNode['data']>) => {
    patchNodeData<TextFlowNode>(setNodes, id, patch)
  }

  const generationTask = useAsyncNodeTask<TextFlowNode>({ kind: 'text', nodeId: id, setNodes })

  const isExpanded = selected
  const resolvedModel = TEXT_MODELS.find((model) => model.id === data.model) ?? TEXT_MODELS[0]
  const displayText = data.text?.trim() ? data.text : EMPTY_TEXT_PLACEHOLDER
  const selectedInputPayloads = (data.inputPayloads ?? []).filter((payload) => (data.selectedInputPayloadIds ?? []).includes(payload.id))
  const availableMediaPayloads = selectedInputPayloads.filter((payload) => (payload.kind === 'image' || payload.kind === 'video') && payload.previewUrl)

  const previewClass =
    data.heading === 1
      ? 'text-[30px] leading-tight'
      : data.heading === 2
        ? 'text-[24px] leading-tight'
        : 'text-[19px] leading-snug'

  const closeOverlays = () => {
    update({ modelPickerOpen: false, settingsOpen: false })
  }

  useEffect(() => {
    if (selected) return
    if (!data.modelPickerOpen && !data.settingsOpen) return
    closeOverlays()
  }, [selected, data.modelPickerOpen, data.settingsOpen])

  const onGenerateText = async () => {
    const prompt = data.prompt?.trim() ?? ''
    const linkedPrompt = data.linkedPrompt?.trim() ?? ''
    const imagePayloads = selectedInputPayloads.filter((payload) => payload.kind === 'image' && payload.previewUrl)
    const videoPayloads = selectedInputPayloads.filter((payload) => payload.kind === 'video' && payload.previewUrl)
    const mediaPayloads = [...imagePayloads, ...videoPayloads]

    if (!prompt && !linkedPrompt && mediaPayloads.length === 0) return

    closeOverlays()
    const task = generationTask.startTask(prompt || linkedPrompt || 'connected payload')

    const contentParts: Array<{ type: 'text'; text: string } | { type: 'image_url'; image_url: { url: string; detail?: 'auto' } }> = []
    const promptSegments = [prompt, linkedPrompt].filter((value) => value.length > 0)
    if (promptSegments.length > 0) {
      contentParts.push({
        type: 'text',
        text: promptSegments.join('\n\n'),
      })
    }
    mediaPayloads.forEach((payload) => {
      if (!payload.previewUrl) return
      contentParts.push({
        type: 'image_url',
        image_url: {
          url: payload.previewUrl,
          detail: 'auto',
        },
      })
    })

    const requestPrompt = contentParts.length > 0
      ? contentParts
      : promptSegments.join('\n\n')

    try {
      const result = await generateText({
        provider: 'openrouter',
        prompt: requestPrompt,
        model: data.model ?? resolvedModel.id,
      }, { signal: task.controller.signal })

      if (result.text.trim()) {
        generationTask.finishSuccess(task, { text: result.text.trim() })
        addAsset({ id: `asset-${Date.now()}`, kind: 'text', name: 'generated-text', createdAt: Date.now() })
        return
      }

      generationTask.finishError(task, '文本生成结果为空，请调整提示词后重试。')
    } catch (error) {
      const message = generationTask.resolveErrorMessage(error, '文本生成失败，请稍后重试。')
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
      title="Text"
      icon={<Wand2 className="h-4 w-4" />}
      selected={selected}
      width={data.w}
      height={data.h}
      isConnectionCandidate={data.isConnectionCandidate}
      isConnectionHovered={data.isConnectionHovered}
      belowContent={
        isExpanded ? (
          <div className="relative rounded-[26px] border border-white/8 bg-[#202020] px-4 py-4 opacity-100 shadow-[0_18px_36px_rgba(0,0,0,0.28)] transition-all duration-500 ease-out animate-in fade-in slide-in-from-top-1">
            {data.modelPickerOpen || data.settingsOpen ? (
              <button
                type="button"
                aria-label="close text overlays"
                onClick={closeOverlays}
                className="fixed inset-0 z-10 cursor-default"
              />
            ) : null}

            <div className="mb-3 flex items-center gap-2">
              <NodeTooltip label="选择文本模型">
                <button
                  type="button"
                  onClick={() => update({ modelPickerOpen: !data.modelPickerOpen, settingsOpen: false })}
                  className="nodrag nopan relative z-20 inline-flex items-center gap-2 rounded-full bg-[#2a2a2a] px-3 py-1.5 text-sm text-white/86 transition hover:bg-[#313131]"
                >
                  <Sparkles className="h-4 w-4 text-white/55" />
                  <span>{resolvedModel.label}</span>
                  <ChevronDown className={`h-4 w-4 text-white/45 transition ${data.modelPickerOpen ? 'rotate-180' : ''}`} />
                </button>
              </NodeTooltip>

              <NodeTooltip label="文本样式设置">
                <button
                  type="button"
                  onClick={() => update({ settingsOpen: !data.settingsOpen, modelPickerOpen: false })}
                  className="nodrag nopan relative z-20 inline-flex items-center gap-2 rounded-full bg-[#2a2a2a] px-3 py-1.5 text-sm text-white/78 transition hover:bg-[#313131]"
                >
                  <Settings2 className="h-4 w-4 text-white/55" />
                  <span>{TEXT_FORMATS.find((item) => item.id === data.heading)?.label ?? 'Large'}</span>
                  <ChevronDown className={`h-4 w-4 text-white/45 transition ${data.settingsOpen ? 'rotate-180' : ''}`} />
                </button>
              </NodeTooltip>
            </div>

            {data.modelPickerOpen ? (
              <div className="absolute left-4 top-14 z-30 w-[calc(100%-2rem)] overflow-hidden rounded-[20px] border border-white/10 bg-[#2a2a2a]/98 p-2 shadow-[0_22px_60px_rgba(0,0,0,0.48)] backdrop-blur-xl">
                <div className="canvas-scrollbar max-h-72 overflow-y-auto pr-1">
                  {TEXT_MODELS.map((model) => {
                    const active = model.id === data.model
                    return (
                      <button
                        key={model.id}
                        type="button"
                        onClick={() => update({ model: model.id, modelPickerOpen: false, settingsOpen: false })}
                        className={`flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left transition ${
                          active ? 'bg-white/8 text-white/88' : 'text-white/72 hover:bg-white/6'
                        }`}
                      >
                        <span className="inline-flex h-9 w-9 items-center justify-center rounded-2xl bg-white/6 text-white/60">
                          <Sparkles className="h-4 w-4" />
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-sm">{model.label}</span>
                        </span>
                        <span className="rounded-full bg-white/6 px-2 py-1 text-[11px] text-white/50">{model.eta}</span>
                      </button>
                    )
                  })}
                </div>
              </div>
            ) : null}

            {data.settingsOpen ? (
              <div className="absolute left-4 top-14 z-30 w-[calc(100%-2rem)] rounded-[20px] border border-white/10 bg-[#2a2a2a]/98 p-3 shadow-[0_22px_60px_rgba(0,0,0,0.48)] backdrop-blur-xl">
                <div className="mb-2 text-xs text-white/35">文本样式</div>
                <div className="mb-3 grid grid-cols-3 gap-2 rounded-2xl bg-[#323232] p-2">
                  {TEXT_FORMATS.map((format) => (
                    <button
                      key={format.id}
                      type="button"
                      onClick={() => update({ heading: format.id, settingsOpen: false, modelPickerOpen: false })}
                      className={`rounded-xl px-3 py-2 text-sm transition ${
                        data.heading === format.id ? 'bg-[#4a4a4a] text-white' : 'text-white/38 hover:text-white/72'
                      }`}
                    >
                      {format.label}
                    </button>
                  ))}
                </div>

                <div className="grid grid-cols-2 gap-2 rounded-2xl bg-[#323232] p-2">
                  <button
                    type="button"
                    onClick={() => update({ bold: !data.bold })}
                    className={`rounded-xl px-3 py-2 text-sm transition ${
                      data.bold ? 'bg-[#4a4a4a] text-white' : 'text-white/38 hover:text-white/72'
                    }`}
                  >
                    Bold
                  </button>
                  <button
                    type="button"
                    onClick={() => update({ italic: !data.italic })}
                    className={`rounded-xl px-3 py-2 text-sm transition ${
                      data.italic ? 'bg-[#4a4a4a] text-white' : 'text-white/38 hover:text-white/72'
                    }`}
                  >
                    Italic
                  </button>
                </div>

                <div className="mt-3 grid grid-cols-1 gap-2 rounded-2xl bg-[#323232] p-2">
                  <button
                    type="button"
                    onClick={() => update({ list: !data.list })}
                    className={`flex items-center justify-center gap-2 rounded-xl px-3 py-2 text-sm transition ${
                      data.list ? 'bg-[#4a4a4a] text-white' : 'text-white/38 hover:text-white/72'
                    }`}
                  >
                    <List className="h-4 w-4" />
                    <span>List</span>
                  </button>
                </div>
              </div>
            ) : null}

            <textarea
              value={data.prompt ?? ''}
              onFocus={closeOverlays}
              onChange={(event) => update({ prompt: event.target.value, errorMessage: undefined })}
              placeholder="输入任何你想要生成的内容"
              aria-label="text ai prompt"
              className="nodrag nopan h-24 w-full resize-none border-0 bg-transparent px-0 py-0 text-sm text-white/84 outline-none placeholder:text-white/24"
            />

            {data.linkedPrompt?.trim() ? (
              <div className="mt-2 rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-2 text-xs text-white/58">
                已连接参考
                <div className="mt-1 whitespace-pre-wrap text-white/78">{data.linkedPrompt}</div>
              </div>
            ) : null}

            <div className="mt-2">
              <NodeNotice message={data.errorMessage} />
            </div>

            <div className="mt-3 flex items-center justify-between gap-3">
              <NodeTooltip label="文本当前仅支持单条生成">
                <button
                  type="button"
                  disabled
                  className="nodrag nopan inline-flex h-10 items-center gap-2 rounded-full border border-white/10 bg-[#2a2a2a] px-3 py-1.5 text-sm text-white/65"
                >
                  <Hash className="h-4 w-4 text-white/45" />
                  <span>×1</span>
                </button>
              </NodeTooltip>
              <NodeTooltip label="使用 AI 生成文本">
                <GenerateActionButton
                  label="生成文本"
                  points={25}
                  ariaLabel="generate text"
                  onClick={onGenerateText}
                  disabled={(!data.prompt?.trim() && !data.linkedPrompt?.trim() && availableMediaPayloads.length === 0) || data.isGenerating}
                />
              </NodeTooltip>
            </div>
          </div>
        ) : null
      }
    >
      <div className="flex h-full min-h-0 flex-col gap-2 overflow-visible">
        <div
          data-preview-frame="text"
          data-testid="text-preview-frame"
          onDoubleClick={() => update({ isEditing: true })}
          className={`relative flex h-full shrink-0 items-start justify-start overflow-visible rounded-[24px] bg-[#232323] px-7 py-6 transition-all duration-200 ${
            selected ? 'border-[3px] border-white/52' : 'border border-white/16'
          }           ${data.isConnectionCandidate ? (data.isConnectionHovered ? 'border-white/72 shadow-[0_0_0_1px_rgba(255,255,255,0.18),0_0_36px_rgba(255,255,255,0.12)]' : 'border-white/30') : ''}`}
        >
          <MediaSidePorts
            nodeId={id}
            active={selected}
            isConnecting={Boolean(data.isConnecting)}
            nodeType="text-node"
            inputPayloads={data.inputPayloads ?? []}
            outputPayloads={data.outputPayloads ?? []}
            selectedInputPayloadIds={data.selectedInputPayloadIds ?? []}
            selectedOutputPayloadIds={data.selectedOutputPayloadIds ?? []}
            onToggleInput={(payloadId) => update({ selectedInputPayloadIds: (data.selectedInputPayloadIds ?? []).includes(payloadId) ? (data.selectedInputPayloadIds ?? []).filter((id) => id !== payloadId) : [...(data.selectedInputPayloadIds ?? []), payloadId] })}
            onToggleOutput={(payloadId) => update({ selectedOutputPayloadIds: (data.selectedOutputPayloadIds ?? []).includes(payloadId) ? (data.selectedOutputPayloadIds ?? []).filter((id) => id !== payloadId) : [...(data.selectedOutputPayloadIds ?? []), payloadId] })}
            onSelectAllInputs={() => update({ selectedInputPayloadIds: (data.inputPayloads ?? []).map((payload) => payload.id) })}
            onSelectAllOutputs={(payloads) => update({ selectedOutputPayloadIds: payloads.map((payload) => payload.id) })}
          />
          <GenerationProgress active={Boolean(data.isGenerating)} label="文本生成中…" />

          {data.isEditing ? (
            <textarea
              value={data.text}
              autoFocus
              onBlur={() => update({ isEditing: false })}
              onChange={(event) => update({ text: event.target.value })}
              aria-label="text node editor"
              className={`nodrag nopan h-full w-full resize-none overflow-x-hidden overflow-y-auto bg-transparent text-left outline-none ${previewClass} ${data.bold ? 'font-semibold' : 'font-normal'} ${
                data.italic ? 'italic' : 'not-italic'
              } ${data.list ? 'pl-5' : ''} canvas-scrollbar text-white/90`}
            />
          ) : data.list && data.text?.trim() ? (
            <ul
              data-testid="text-node-display"
              className={`min-h-0 w-full overflow-x-hidden overflow-y-hidden pr-1 text-left list-disc pl-5 ${previewClass} ${data.bold ? 'font-semibold' : 'font-normal'} ${
                data.italic ? 'italic' : 'not-italic'
              } text-white/82`}
            >
              {data.text.split('\n').filter((line) => line.trim()).map((line, index) => (
                <li key={index} className="mb-1 last:mb-0">{line}</li>
              ))}
            </ul>
          ) : (
            <div
              data-testid="text-node-display"
              className={`min-h-0 w-full overflow-x-hidden overflow-y-hidden pr-1 text-left ${previewClass} ${data.bold ? 'font-semibold' : 'font-normal'} ${
                data.italic ? 'italic' : 'not-italic'
              } ${data.text?.trim() ? 'text-white/82' : 'text-white/34'}`}
            >
              {displayText}
            </div>
          )}
        </div>
      </div>
    </FlowNodeShell>
  )
}
