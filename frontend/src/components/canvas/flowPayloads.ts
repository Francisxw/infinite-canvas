import type { Edge } from '@xyflow/react'
import { EMPTY_TEXT_PLACEHOLDER } from '../nodes/flow/common'
import type { AnyFlowNode, FlowPayload, TextNodeData } from '../nodes/flow/types'

export type PendingConnection = {
  nodeId: string
  handleType: 'source' | 'target'
}

function arraysEqual(left: string[], right: string[]) {
  if (left.length !== right.length) return false
  return left.every((value, index) => value === right[index])
}

function payloadsEqual(left: FlowPayload[], right: FlowPayload[]) {
  if (left.length !== right.length) return false
  return left.every((payload, index) => {
    const other = right[index]
    return payload.id === other.id && payload.kind === other.kind && payload.label === other.label && payload.sourceNodeId === other.sourceNodeId && payload.textValue === other.textValue && payload.previewUrl === other.previewUrl
  })
}

function deriveTextPromptFromPayloads(payloads: FlowPayload[]) {
  const lines = payloads.flatMap((payload) => {
    if (payload.kind === 'text' && payload.textValue) return [`文本参考：${payload.textValue}`]
    if (payload.kind === 'image') return [`图像参考：${payload.label}`]
    if (payload.kind === 'video') return [`视频参考：${payload.label}`]
    if (payload.kind === 'audio') return [`音频参考：${payload.label}`]
    return []
  })

  return lines.join('\n')
}

export function buildNodeOutputs(node: AnyFlowNode): FlowPayload[] {
  if (node.type === 'text-node') {
    const value = typeof node.data.text === 'string' ? node.data.text.trim() : ''
    return value
      ? [
          {
            id: `${node.id}-text-output`,
            kind: 'text',
            label: value.length > 18 ? `${value.slice(0, 18)}…` : value,
            sourceNodeId: node.id,
            textValue: value,
          },
        ]
      : []
  }

  if (node.type === 'image-node') {
    const payloads: FlowPayload[] = []

    if (node.data.dataUrl) {
      payloads.push({
        id: `${node.id}-image-output`,
        kind: 'image',
        label: node.data.filename ?? '图像结果',
        sourceNodeId: node.id,
        previewUrl: node.data.dataUrl,
      })
    }

    return payloads
  }

  if (node.type === 'video-node') {
    const payloads: FlowPayload[] = []

    if (node.data.dataUrl || node.data.coverUrl) {
      payloads.push({
        id: `${node.id}-video-output`,
        kind: 'video',
        label: node.data.filename ?? '视频结果',
        sourceNodeId: node.id,
        previewUrl: node.data.coverUrl ?? node.data.dataUrl ?? undefined,
      })
    }

    return payloads
  }

  return []
}

export function buildPotentialNodeOutputs(node: AnyFlowNode): FlowPayload[] {
  if (node.type === 'text-node') {
    return [
      {
        id: `${node.id}-text-potential-output`,
        kind: 'text',
        label: '文本内容',
        sourceNodeId: node.id,
      },
    ]
  }

  if (node.type === 'image-node') {
    return [
      {
        id: `${node.id}-image-potential-output`,
        kind: 'image',
        label: node.data.filename ?? '图像结果',
        sourceNodeId: node.id,
      },
    ]
  }

  return [
    {
      id: `${node.id}-video-potential-output`,
      kind: 'video',
      label: node.data.filename ?? '视频结果',
      sourceNodeId: node.id,
      previewUrl: node.data.coverUrl ?? node.data.dataUrl ?? undefined,
    },
  ]
}

export function isNodeConnectionCompatible(sourceNode: AnyFlowNode, targetNode: AnyFlowNode): boolean {
  const sourcePayloads = buildNodeOutputs(sourceNode)

  if (sourcePayloads.length === 0) {
    return buildPotentialNodeOutputs(sourceNode).some((payload) => acceptsPayload(targetNode, payload))
  }

  const selectedOutputIds = sourceNode.data.selectedOutputPayloadIds ?? sourcePayloads.map((payload) => payload.id)
  return sourcePayloads.some((payload) => selectedOutputIds.includes(payload.id) && acceptsPayload(targetNode, payload))
}

export function acceptsPayload(node: AnyFlowNode, payload: FlowPayload): boolean {
  if (node.type === 'text-node') return payload.kind === 'text' || payload.kind === 'image' || payload.kind === 'video' || payload.kind === 'audio'
  if (node.type === 'image-node') return payload.kind === 'text' || payload.kind === 'image'
  return payload.kind === 'text' || payload.kind === 'image' || payload.kind === 'video'
}

export function syncNodeInputs(nodes: AnyFlowNode[], edges: Edge[]): { nodes: AnyFlowNode[]; changed: boolean } {
  const nodeMap = new Map(nodes.map((node) => [node.id, node]))
  let changed = false

  const nextNodes = nodes.map((node) => {
    const outputs = buildNodeOutputs(node)
    const incoming = edges.filter((edge) => edge.target === node.id)
    const payloads = incoming.flatMap((edge) => {
      const source = nodeMap.get(edge.source)
      if (!source) return []
      const sourceOutputs = buildNodeOutputs(source)
      const selectedOutputIds = source.data.selectedOutputPayloadIds ?? sourceOutputs.map((payload) => payload.id)
      return sourceOutputs.filter((payload) => acceptsPayload(node, payload) && selectedOutputIds.includes(payload.id))
    })

    const previousInputPayloads = node.data.inputPayloads ?? []
    const previousSelectedInputs = node.data.selectedInputPayloadIds ?? []
    const selected = previousSelectedInputs.filter((id) => payloads.some((payload) => payload.id === id))
    const shouldAutoSelectInputs = previousSelectedInputs.length === 0 && previousInputPayloads.length === 0 && payloads.length > 0
    const nextSelected = shouldAutoSelectInputs ? payloads.map((payload) => payload.id) : selected
    const selectedPayloads = payloads.filter((payload) => nextSelected.includes(payload.id))
    const previousOutputPayloads = node.data.outputPayloads ?? []
    const previousSelectedOutputs = node.data.selectedOutputPayloadIds ?? []
    const filteredOutputSelection = previousSelectedOutputs.filter((id) => outputs.some((payload) => payload.id === id))
    const shouldAutoSelectOutputs = previousSelectedOutputs.length === 0 && previousOutputPayloads.length === 0 && outputs.length > 0
    const nextOutputSelection = shouldAutoSelectOutputs ? outputs.map((payload) => payload.id) : filteredOutputSelection

    const baseData = {
      ...node.data,
      inputPayloads: payloads,
      outputPayloads: outputs,
      selectedInputPayloadIds: nextSelected,
      selectedOutputPayloadIds: nextOutputSelection,
    }

    let nextNode: AnyFlowNode = {
      ...node,
      data: baseData,
    } as AnyFlowNode

    if (node.type === 'text-node') {
      const textPayload = selectedPayloads.find((payload) => payload.kind === 'text' && payload.textValue)
      const derivedPrompt = deriveTextPromptFromPayloads(selectedPayloads)
      const currentText = typeof node.data.text === 'string' ? node.data.text : ''
      const isPlaceholderText = currentText.trim().length === 0 || currentText === EMPTY_TEXT_PLACEHOLDER
      const nextData: TextNodeData = {
        ...node.data,
        inputPayloads: payloads,
        outputPayloads: outputs,
        selectedInputPayloadIds: nextSelected,
        selectedOutputPayloadIds: nextOutputSelection,
        linkedPrompt: derivedPrompt,
      }

      if (textPayload && isPlaceholderText && !node.data.isEditing) {
        nextData.text = textPayload.textValue ?? currentText
      }

      nextNode = {
        ...node,
        data: nextData,
      } as AnyFlowNode
    }

    if (node.type === 'image-node') {
      const textPayload = selectedPayloads.find((payload) => payload.kind === 'text' && payload.textValue)
      if (textPayload && !node.data.prompt.trim()) {
        nextNode = {
          ...node,
          data: {
            ...baseData,
            prompt: textPayload.textValue ?? node.data.prompt,
          },
        } as AnyFlowNode
      }
    }

    if (node.type === 'video-node') {
      const textPayload = selectedPayloads.find((payload) => payload.kind === 'text' && payload.textValue)
      if (textPayload && !node.data.prompt.trim()) {
        nextNode = {
          ...node,
          data: {
            ...baseData,
            prompt: textPayload.textValue ?? node.data.prompt,
          },
        } as AnyFlowNode
      }
    }

    const inputChanged = !payloadsEqual(node.data.inputPayloads ?? [], nextNode.data.inputPayloads ?? [])
    const outputChanged = !payloadsEqual(node.data.outputPayloads ?? [], nextNode.data.outputPayloads ?? [])
    const selectedInputChanged = !arraysEqual(node.data.selectedInputPayloadIds ?? [], nextNode.data.selectedInputPayloadIds ?? [])
    const selectedOutputChanged = !arraysEqual(node.data.selectedOutputPayloadIds ?? [], nextNode.data.selectedOutputPayloadIds ?? [])
    const promptChanged = (node.type === 'image-node' || node.type === 'video-node') && nextNode.data.prompt !== node.data.prompt
    const textChanged = node.type === 'text-node' && (nextNode.data as TextNodeData).text !== node.data.text
    const linkedPromptChanged = node.type === 'text-node' && (nextNode.data as TextNodeData).linkedPrompt !== node.data.linkedPrompt

    if (inputChanged || outputChanged || selectedInputChanged || selectedOutputChanged || promptChanged || textChanged || linkedPromptChanged) {
      changed = true
    }

    return nextNode
  })

  return { nodes: nextNodes, changed }
}

export function attachConnectionHints(nodes: AnyFlowNode[], pendingConnection: PendingConnection | null, hoverTargetNodeId: string | null): AnyFlowNode[] {
  return nodes.map((node) => ({
    ...node,
    data: {
      ...node.data,
      outputPayloads: buildNodeOutputs(node),
      isConnecting: Boolean(pendingConnection),
      isConnectionCandidate: pendingConnection ? node.id !== pendingConnection.nodeId : false,
      isConnectionHovered: hoverTargetNodeId === node.id,
    },
  })) as AnyFlowNode[]
}
