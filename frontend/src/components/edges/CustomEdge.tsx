import { memo, useState } from 'react'
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
  useReactFlow,
} from '@xyflow/react'

function CustomEdgeComponent({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  selected,
}: EdgeProps) {
  const { setEdges } = useReactFlow()
  const [isHovered, setIsHovered] = useState(false)

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    curvature: 0.35,
  })

  const remove = () => {
    setEdges((edges) => edges.filter((edge) => edge.id !== id))
  }

  const showDeleteButton = selected || isHovered

  return (
    <>
      {/* Invisible wider path for easier hover detection */}
      <path
        d={edgePath}
        fill="none"
        stroke="transparent"
        strokeWidth={12}
        className="cursor-pointer"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      />

      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: selected
            ? 'var(--primary-400, #60a5fa)'
            : isHovered
              ? 'var(--primary-500, #3b82f6)'
              : 'var(--gray-400, #9ca3af)',
          strokeWidth: selected ? 2.5 : isHovered ? 2.25 : 2,
          transition: 'stroke 200ms ease, stroke-width 200ms ease',
        }}
      />

      <EdgeLabelRenderer>
        <div
          className={`nodrag nopan pointer-events-auto absolute flex h-7 w-7 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/10 bg-[#0f0f0f]/95 text-xs text-gray-100 shadow-lg backdrop-blur-sm transition-all duration-200 ${showDeleteButton ? 'scale-100 opacity-100' : 'scale-75 opacity-0'}`}
          style={{
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
          }}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          <button
            type="button"
            aria-label="delete edge"
            onClick={remove}
            className="flex h-full w-full items-center justify-center rounded-full transition-colors hover:bg-[#1f1f1f] hover:text-red-400"
          >
            ×
          </button>
        </div>
      </EdgeLabelRenderer>
    </>
  )
}

export const CustomEdge = memo(CustomEdgeComponent)
