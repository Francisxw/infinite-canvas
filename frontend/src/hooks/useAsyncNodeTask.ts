import { useCallback, useEffect, useRef, type Dispatch, type SetStateAction } from 'react'
import { patchNodeData } from '../components/nodes/flow/common'
import type { AnyFlowNode } from '../components/nodes/flow/types'
import { getRequestErrorMessage, isRequestCanceled } from '../services/api'
import { useCanvasDockStore } from '../stores/canvasDockStore'

type AsyncTaskKind = 'image' | 'text' | 'video'

type StartedTask = {
  controller: AbortController
  historyId: string
}

export function useAsyncNodeTask<TNode extends AnyFlowNode>({
  kind,
  nodeId,
  setNodes,
}: {
  kind: AsyncTaskKind
  nodeId: string
  setNodes: Dispatch<SetStateAction<TNode[]>>
}) {
  const addHistory = useCanvasDockStore((state) => state.addHistory)
  const updateHistory = useCanvasDockStore((state) => state.updateHistory)
  const controllerRef = useRef<AbortController | null>(null)

  const patchData = useCallback((patch: Partial<TNode['data']>) => {
    patchNodeData<TNode>(setNodes, nodeId, patch)
  }, [nodeId, setNodes])

  const abortActive = useCallback(() => {
    controllerRef.current?.abort()
  }, [])

  useEffect(() => () => {
    controllerRef.current?.abort()
  }, [])

  const startTask = useCallback((prompt: string): StartedTask => {
    controllerRef.current?.abort()
    const controller = new AbortController()
    controllerRef.current = controller
    patchData({ isGenerating: true, errorMessage: undefined } as Partial<TNode['data']>)

    const historyId = `history-${Date.now()}`
    addHistory({
      id: historyId,
      kind,
      prompt,
      createdAt: Date.now(),
      status: 'running',
    })

    return { controller, historyId }
  }, [addHistory, kind, patchData])

  const finishSuccess = useCallback((task: StartedTask, patch?: Partial<TNode['data']>) => {
    if (controllerRef.current === task.controller) {
      controllerRef.current = null
    }

    patchData({ isGenerating: false, errorMessage: undefined, ...patch } as Partial<TNode['data']>)
    updateHistory(task.historyId, { status: 'done' })
  }, [patchData, updateHistory])

  const finishError = useCallback((task: StartedTask, message: string) => {
    if (controllerRef.current === task.controller) {
      controllerRef.current = null
    }

    patchData({ isGenerating: false, errorMessage: message } as Partial<TNode['data']>)
    updateHistory(task.historyId, { status: 'error' })
  }, [patchData, updateHistory])

  const finishCancelled = useCallback((task: StartedTask) => {
    if (controllerRef.current === task.controller) {
      controllerRef.current = null
    }

    patchData({ isGenerating: false } as Partial<TNode['data']>)
    updateHistory(task.historyId, { status: 'cancelled' })
  }, [patchData, updateHistory])

  const resolveErrorMessage = useCallback((error: unknown, fallback: string) => {
    if (isRequestCanceled(error)) {
      return null
    }

    return getRequestErrorMessage(error, fallback)
  }, [])

  return {
    abortActive,
    finishCancelled,
    finishError,
    finishSuccess,
    resolveErrorMessage,
    startTask,
  }
}
