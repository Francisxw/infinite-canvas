import type { Editor, TLBinding, TLShape } from 'tldraw'

const NODE_TYPES = new Set(['image-node', 'ai-prompt-node', 'text-node', 'video-node'])

function isNodeShape(shape: TLShape | undefined): boolean {
  return !!shape && NODE_TYPES.has(shape.type)
}

function isValidArrowBinding(editor: Editor, binding: TLBinding): boolean {
  if (binding.type !== 'arrow') return true

  const fromShape = editor.getShape(binding.fromId)
  const toShape = editor.getShape(binding.toId)

  if (!fromShape || fromShape.type !== 'arrow') return false
  if (!isNodeShape(toShape)) return false
  return true
}

function hasArrowSelfConnection(editor: Editor, arrowId: TLShape['id']): boolean {
  const bindings = editor.getBindingsFromShape(arrowId, 'arrow')
  const toIds = bindings.map((item) => item.toId)
  return new Set(toIds).size < toIds.length
}

export function registerWorkflowRules(editor: Editor): () => void {
  const disposers: Array<() => void> = []

  disposers.push(
    editor.sideEffects.registerAfterCreateHandler('binding', (binding) => {
      if (!isValidArrowBinding(editor, binding)) {
        editor.deleteBinding(binding.id)
      }
    })
  )

  disposers.push(
    editor.sideEffects.registerAfterChangeHandler('binding', (_prev, next) => {
      if (!isValidArrowBinding(editor, next)) {
        editor.deleteBinding(next.id)
      }
    })
  )

  disposers.push(
    editor.sideEffects.registerOperationCompleteHandler(() => {
      const arrows = editor.getCurrentPageShapes().filter((shape) => shape.type === 'arrow')
      for (const arrow of arrows) {
        if (hasArrowSelfConnection(editor, arrow.id)) {
          editor.deleteShapes([arrow.id])
        }
      }
    })
  )

  disposers.push(
    editor.sideEffects.registerBeforeDeleteHandler('shape', (shape) => {
      if (shape.type === 'arrow' || !NODE_TYPES.has(shape.type)) return

      const bindings = editor.getBindingsInvolvingShape(shape.id, 'arrow')
      if (bindings.length > 0) {
        const arrowIds = Array.from(new Set(bindings.map((binding) => binding.fromId)))
        const arrowShapes = arrowIds
          .map((id) => editor.getShape(id))
          .filter((item): item is TLShape => !!item && item.type === 'arrow')

        if (arrowShapes.length > 0) {
          editor.deleteShapes(arrowShapes)
        }
      }

      return
    })
  )

  return () => {
    for (const dispose of disposers) dispose()
  }
}
