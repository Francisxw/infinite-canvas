export function isPaneTarget(target: EventTarget | null): boolean {
  if (!(target instanceof Element)) return false
  // Must be within the pane
  if (!target.closest('.react-flow__pane')) return false
  // But not on a node - nodes have data-node-id attribute
  if (target.closest('[data-node-id]')) return false
  return true
}

export function getNodeIdFromPoint(clientX: number, clientY: number, excludeNodeId?: string) {
  const elements = document.elementsFromPoint(clientX, clientY)

  for (const element of elements) {
    const container = element.closest('[data-node-id]')
    const nodeId = container?.getAttribute('data-node-id')
    if (nodeId && nodeId !== excludeNodeId) {
      return nodeId
    }
  }

  return null
}
