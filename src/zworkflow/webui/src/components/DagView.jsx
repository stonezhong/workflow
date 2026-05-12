import { useMemo } from 'react'

const TEXT_FONT_SIZE = 12
const NODE_PADDING = 4
const NODE_HEIGHT = TEXT_FONT_SIZE + NODE_PADDING * 2
const COLUMN_GAP = 48
const ROW_GAP = 20
const PADDING = 20

function nodeWidth(title) {
  return Math.ceil(String(title).length * 7) + NODE_PADDING * 2
}

function normalizeNode(node) {
  if (typeof node === 'string') {
    return {
      key: node,
      title: node,
      color: '#f8fafc',
    }
  }

  return {
    key: node.key,
    title: node.title ?? node.key,
    color: node.color ?? '#f8fafc',
  }
}

function uniqueNodes(nodes, connections) {
  const nodeMap = new Map()

  nodes.map(normalizeNode).forEach(node => {
    if (node.key) nodeMap.set(node.key, node)
  })

  connections.forEach(connection => {
    if (connection.source && !nodeMap.has(connection.source)) {
      nodeMap.set(connection.source, {
        key: connection.source,
        title: connection.source,
        color: '#f8fafc',
      })
    }
    if (connection.destination && !nodeMap.has(connection.destination)) {
      nodeMap.set(connection.destination, {
        key: connection.destination,
        title: connection.destination,
        color: '#f8fafc',
      })
    }
  })

  return Array.from(nodeMap.values())
}

function buildLayout(nodes, connections) {
  const unique = uniqueNodes(nodes, connections)
  const keys = unique.map(node => node.key)
  const nodeByKey = new Map(unique.map(node => [node.key, node]))
  const keySet = new Set(keys)
  const incoming = new Map(keys.map(key => [key, new Set()]))
  const outgoing = new Map(keys.map(key => [key, new Set()]))

  connections.forEach(({ source, destination }) => {
    if (!keySet.has(source) || !keySet.has(destination)) return

    incoming.get(destination).add(source)
    outgoing.get(source).add(destination)
  })

  const inDegree = new Map(keys.map(key => [key, incoming.get(key).size]))
  const levels = new Map(keys.map(key => [key, 0]))
  const queue = keys.filter(key => inDegree.get(key) === 0)
  const visited = new Set()

  while (queue.length > 0) {
    const key = queue.shift()
    visited.add(key)

    outgoing.get(key).forEach(destination => {
      levels.set(destination, Math.max(levels.get(destination), levels.get(key) + 1))
      inDegree.set(destination, inDegree.get(destination) - 1)

      if (inDegree.get(destination) === 0) {
        queue.push(destination)
      }
    })
  }

  keys.forEach(key => {
    if (!visited.has(key)) {
      const sourceLevels = Array.from(incoming.get(key), source => levels.get(source) ?? 0)
      levels.set(key, sourceLevels.length === 0 ? 0 : Math.max(...sourceLevels) + 1)
    }
  })

  const columns = new Map()
  keys.forEach(key => {
    const level = levels.get(key)
    if (!columns.has(level)) columns.set(level, [])
    columns.get(level).push(key)
  })

  const columnWidths = new Map()
  columns.forEach((column, level) => {
    columnWidths.set(level, Math.max(...column.map(key => nodeWidth(nodeByKey.get(key).title))))
  })

  const columnX = new Map()
  let nextX = PADDING
  Array.from(columns.keys())
    .sort((a, b) => a - b)
    .forEach(level => {
      columnX.set(level, nextX)
      nextX += columnWidths.get(level) + COLUMN_GAP
    })

  const positionedNodes = keys.map(key => {
    const node = nodeByKey.get(key)
    const level = levels.get(key)
    const column = columns.get(level)
    const row = column.indexOf(key)
    const width = nodeWidth(node.title)

    return {
      ...node,
      width,
      x: columnX.get(level) + (columnWidths.get(level) - width) / 2,
      y: PADDING + row * (NODE_HEIGHT + ROW_GAP),
    }
  })

  const nodePositions = new Map(positionedNodes.map(node => [node.key, node]))
  const maxRows = Math.max(1, ...Array.from(columns.values(), column => column.length))

  return {
    nodes: positionedNodes,
    connections: connections.filter(
      ({ source, destination }) => nodePositions.has(source) && nodePositions.has(destination),
    ),
    nodePositions,
    width: Math.max(PADDING * 2, nextX - COLUMN_GAP + PADDING),
    height: PADDING * 2 + NODE_HEIGHT + (maxRows - 1) * (NODE_HEIGHT + ROW_GAP),
  }
}

export default function DagView({ nodes = [], connections = [] }) {
  const layout = useMemo(() => buildLayout(nodes, connections), [nodes, connections])

  if (layout.nodes.length === 0) {
    return <p className="empty-note">No DAG nodes defined.</p>
  }

  return (
    <div className="dag-view">
      <svg
        className="dag-canvas"
        viewBox={`0 0 ${layout.width} ${layout.height}`}
        width={layout.width}
        height={layout.height}
        role="img"
        aria-label="DAG view"
      >
        <defs>
          <marker
            id="dag-arrow"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="7"
            markerHeight="7"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" />
          </marker>
        </defs>

        {layout.connections.map(({ source, destination }) => {
          const sourceNode = layout.nodePositions.get(source)
          const destinationNode = layout.nodePositions.get(destination)
          const startX = sourceNode.x + sourceNode.width
          const startY = sourceNode.y + NODE_HEIGHT / 2
          const endX = destinationNode.x
          const endY = destinationNode.y + NODE_HEIGHT / 2
          const midX = startX + Math.max(24, (endX - startX) / 2)

          return (
            <path
              key={`${source}->${destination}`}
              className="dag-edge"
              d={`M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`}
              markerEnd="url(#dag-arrow)"
            />
          )
        })}

        {layout.nodes.map(node => (
          <g key={node.key} className="dag-node" transform={`translate(${node.x} ${node.y})`}>
            <rect width={node.width} height={NODE_HEIGHT} rx="4" fill={node.color} />
            <text x={node.width / 2} y={NODE_HEIGHT / 2} dominantBaseline="middle" textAnchor="middle">
              {node.title}
            </text>
          </g>
        ))}
      </svg>
    </div>
  )
}
