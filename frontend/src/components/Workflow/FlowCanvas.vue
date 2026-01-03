<template>
  <div 
    class="flow-canvas-container"
    @drop="handleDrop"
    @dragover="handleDragOver"
    @dragenter="handleDragEnter"
  >
    <VueFlow
      v-model:nodes="flowNodes"
      v-model:edges="flowEdges"
      v-model:viewport="flowViewport"
      @nodes-change="onNodesChange"
      @edges-change="onEdgesChange"
      @viewport-change="onViewportChange"
      @node-click="onNodeClick"
      @edge-click="onEdgeClick"
      @pane-click="onPaneClick"
      @connect="onConnect"
      @nodes-delete="onNodesDelete"
      @edges-delete="onEdgesDelete"
      class="vue-flow"
      @contextmenu.prevent="onCanvasContextMenu"
      :fit-view-on-init="true"
      :min-zoom="0.2"
      :max-zoom="4"
      :nodes-draggable="true"
      :nodes-connectable="true"
      :nodes-focusable="true"
      :edges-updatable="true"
      :edges-focusable="true"
      :select-nodes-on-drag="false"
    >
      <Background pattern-color="#e5e7eb" :gap="16" />
      <Controls />
      <MiniMap />
    </VueFlow>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, nextTick, ref, onMounted } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import type { FlowNode, FlowEdge, Viewport } from '@/stores/workflow'
import type { Node, Edge, Connection } from '@vue-flow/core'

interface Props {
  nodes: FlowNode[]
  edges: FlowEdge[]
  viewport: Viewport
  selectedNode?: FlowNode | null
  selectedEdge?: FlowEdge | null
}

interface Emits {
  (e: 'update:nodes', nodes: FlowNode[]): void
  (e: 'update:edges', edges: FlowEdge[]): void
  (e: 'update:viewport', viewport: Viewport): void
  (e: 'node-select', node: FlowNode | null): void
  (e: 'edge-select', edge: FlowEdge | null): void
  (e: 'node-delete', nodeId: string): void
  (e: 'edge-delete', edgeId: string): void
  (e: 'connect', connection: { source: string; target: string }): void
  (e: 'node-add', nodeType: string, position: { x: number; y: number }, config?: Record<string, any>): void
  (e: 'context-menu', context: { type: 'node' | 'edge' | 'canvas'; node?: FlowNode; edge?: FlowEdge; position: { x: number; y: number } }): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 使用 Vue Flow 的 composable
const { fitView } = useVueFlow()

// 监听节点变化，在节点加载完成后自动适配视图
let fitViewTimeout: ReturnType<typeof setTimeout> | null = null
watch(() => props.nodes.length, (newLength, oldLength) => {
  // 当节点数量变化且大于0时，延迟触发 fitView
  if (newLength > 0 && newLength !== oldLength) {
    if (fitViewTimeout) {
      clearTimeout(fitViewTimeout)
    }
    fitViewTimeout = setTimeout(() => {
      nextTick(() => {
        try {
          fitView({ padding: 0.2, duration: 300 })
        } catch (error) {
          console.warn('fitView 失败:', error)
        }
      })
    }, 200)
  }
}, { immediate: false })

// 组件挂载后，如果已有节点，也触发一次 fitView
onMounted(() => {
  if (props.nodes.length > 0) {
    nextTick(() => {
      setTimeout(() => {
        try {
          fitView({ padding: 0.2, duration: 300 })
        } catch (error) {
          console.warn('初始 fitView 失败:', error)
        }
      }, 300)
    })
  }
})

// 转换FlowNode到Vue Flow的Node格式
const flowNodes = computed({
  get: () => {
    return props.nodes.map(node => ({
      id: node.id,
      type: node.type || 'default',
      label: node.label,
      position: node.position,
      data: node.data,
      style: node.style,
      // 添加连接点
      sourcePosition: 'right',
      targetPosition: 'left',
      // 添加选中状态
      selected: props.selectedNode?.id === node.id,
      // 所有节点都可以拖拽（包括 START 和 END）
      draggable: true
    } as Node))
  },
  set: (value: Node[]) => {
    const converted = value.map(node => ({
      id: node.id,
      type: node.type || 'default',
      label: node.label || '',
      position: node.position,
      data: node.data || {},
      style: node.style || {}
    } as FlowNode))
    emit('update:nodes', converted)
    
    // 当节点位置变化时（拖拽），标记为已修改
    // 位置变化会通过 v-model 自动同步到 store
  }
})

// 转换FlowEdge到Vue Flow的Edge格式
const flowEdges = computed({
  get: () => {
    return props.edges.map(edge => {
      const isStep = edge.type === 'step'
      return {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: edge.type || 'default',
        label: edge.label,
        data: edge.data,
        animated: isStep, // 条件边使用动画效果
        style: isStep 
          ? { stroke: '#ff6b6b', strokeDasharray: '5,5' } // 条件边：红色虚线
          : { stroke: '#64748b' }, // 直接边：灰色实线
        // 添加选中状态
        selected: props.selectedEdge?.id === edge.id
      } as Edge
    })
  },
  set: (value: Edge[]) => {
    const converted = value.map(edge => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: edge.type === 'step' ? 'conditional' : 'direct',
      label: edge.label,
      data: edge.data
    } as FlowEdge))
    emit('update:edges', converted)
  }
})

// Viewport
const flowViewport = computed({
  get: () => props.viewport,
  set: (value: Viewport) => {
    emit('update:viewport', value)
  }
})

// 事件处理
let isDragging = false
let dragStartTime = 0

function onNodesChange(changes: unknown) {
  // Vue Flow内部节点变化，会自动更新flowNodes
  const changesArray = changes as Array<any>
  
  // 检查是否有拖拽开始
  const dragStart = changesArray.find((change: any) => 
    change.type === 'position' && change.dragging === true
  )
  if (dragStart && !isDragging) {
    isDragging = true
    dragStartTime = Date.now()
  }
  
  // 检查是否有位置变化完成（拖拽结束）
  const dragEnd = changesArray.find((change: any) => 
    change.type === 'position' && change.dragging === false
  )
  if (dragEnd && isDragging) {
    isDragging = false
    const dragDuration = Date.now() - dragStartTime
    // 位置变化完成，节点位置已通过 v-model 自动更新
    // 拖拽功能正常工作，无需额外处理
  }
}

function onEdgesChange(_changes: unknown) {
  // Vue Flow内部边变化，会自动更新flowEdges
  // 这里可以添加额外的处理逻辑
}

function onViewportChange(viewport: Viewport) {
  emit('update:viewport', viewport)
}

function onNodeClick(event: { node: Node }) {
  const flowNode = props.nodes.find(n => n.id === event.node.id)
  emit('node-select', flowNode || null)
}

function onEdgeClick(event: { edge: Edge }) {
  const flowEdge = props.edges.find(e => e.id === event.edge.id)
  emit('edge-select', flowEdge || null)
}

function onConnect(connection: Connection) {
  if (connection.source && connection.target) {
    emit('connect', {
      source: connection.source,
      target: connection.target
    })
  }
}

function onNodesDelete(nodes: Node[]) {
  nodes.forEach(node => {
    emit('node-delete', node.id)
  })
}

function onEdgesDelete(edges: Edge[]) {
  edges.forEach(edge => {
    emit('edge-delete', edge.id)
  })
}

function onPaneClick(_event: unknown) {
  // 点击画布空白处，取消选择
  emit('node-select', null)
  emit('edge-select', null)
}

// 右键菜单处理
function onCanvasContextMenu(event: MouseEvent) {
  event.preventDefault()
  
  // 检查是否点击在节点或边上（通过事件目标判断）
  const target = event.target as HTMLElement
  const nodeElement = target.closest('.vue-flow__node')
  const edgeElement = target.closest('.vue-flow__edge')
  
  if (nodeElement) {
    const nodeId = nodeElement.getAttribute('data-id') || (nodeElement.querySelector('[data-id]') as HTMLElement)?.getAttribute('data-id')
    if (nodeId) {
      const flowNode = props.nodes.find(n => n.id === nodeId)
      emit('context-menu', {
        type: 'node',
        node: flowNode,
        position: { x: event.clientX, y: event.clientY }
      })
    }
  } else if (edgeElement) {
    // 边的ID通常存储在SVG路径的data-id属性中
    const edgeId = edgeElement.getAttribute('data-id') || (edgeElement.querySelector('[data-id]') as HTMLElement)?.getAttribute('data-id')
    if (edgeId) {
      const flowEdge = props.edges.find(e => e.id === edgeId)
      emit('context-menu', {
        type: 'edge',
        edge: flowEdge,
        position: { x: event.clientX, y: event.clientY }
      })
    }
  } else {
    // 点击在画布空白处
    emit('context-menu', {
      type: 'canvas',
      position: { x: event.clientX, y: event.clientY }
    })
  }
}

// 拖拽事件处理
function handleDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'copy'
  }
}

function handleDragEnter(event: DragEvent) {
  event.preventDefault()
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  
  const nodeType = event.dataTransfer?.getData('application/node-type')
  const configStr = event.dataTransfer?.getData('application/node-config')
  const agentType = event.dataTransfer?.getData('application/agent-type')
  
  if (!nodeType) return
  
  // 找到Vue Flow的视口容器
  const container = event.currentTarget as HTMLElement
  const vueFlowContainer = container.querySelector('.vue-flow') as HTMLElement
  if (!vueFlowContainer) return
  
  // 计算相对于画布的位置（需要考虑视口的偏移和缩放）
  const rect = vueFlowContainer.getBoundingClientRect()
  const x = (event.clientX - rect.left) / props.viewport.zoom - props.viewport.x
  const y = (event.clientY - rect.top) / props.viewport.zoom - props.viewport.y
  
  // 解析配置
  let config: Record<string, any> = {}
  try {
    if (configStr) {
      config = JSON.parse(configStr)
    }
  } catch (e) {
    console.warn('Failed to parse node config:', e)
  }
  
  // 如果从拖拽中获取了 agent_type，添加到配置中
  if (agentType) {
    config.agent_type = agentType
  }
  
  emit('node-add', nodeType, { x, y }, config)
}
</script>

<style scoped>
.flow-canvas-container {
  width: 100%;
  height: 100%;
  background: #fafafa;
  position: relative;
}

.vue-flow {
  width: 100%;
  height: 100%;
}

/* 自定义节点样式 */
:deep(.vue-flow__node) {
  border-radius: 8px;
  font-size: 12px;
  cursor: move; /* 显示可拖拽光标 */
  transition: box-shadow 0.2s ease;
}

:deep(.vue-flow__node:hover) {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

:deep(.vue-flow__node.dragging) {
  opacity: 0.8;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
  z-index: 1000;
}

:deep(.vue-flow__node-default) {
  padding: 10px;
  background: white;
  border: 2px solid #64748b;
}

/* START 节点样式 */
:deep(.vue-flow__node-start) {
  padding: 12px 16px;
  background: #4caf50 !important;
  border: 2px solid #2e7d32 !important;
  color: white !important;
  font-weight: bold;
  border-radius: 8px;
  min-width: 80px;
  text-align: center;
}

/* END 节点样式 */
:deep(.vue-flow__node-end) {
  padding: 12px 16px;
  background: #f44336 !important;
  border: 2px solid #c62828 !important;
  color: white !important;
  font-weight: bold;
  border-radius: 8px;
  min-width: 80px;
  text-align: center;
  cursor: move; /* 允许拖拽 */
}

/* 拖拽时的视觉反馈 */
:deep(.vue-flow__node.dragging) {
  transform: scale(1.05);
  transition: transform 0.1s ease;
}

/* 节点连接点样式优化 */
:deep(.vue-flow__handle) {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #409eff;
  border: 2px solid white;
  transition: all 0.2s ease;
}

:deep(.vue-flow__handle:hover) {
  width: 12px;
  height: 12px;
  background: #66b1ff;
}

:deep(.vue-flow__edge-path) {
  stroke-width: 2;
}

:deep(.vue-flow__edge.selected .vue-flow__edge-path) {
  stroke: #3b82f6;
  stroke-width: 3;
}

/* 将Controls组件移到左下方 */
:deep(.vue-flow__controls) {
  position: absolute;
  bottom: 20px !important;
  left: 20px !important;
  right: auto !important;
  top: auto !important;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  padding: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* Controls按钮样式 */
:deep(.vue-flow__controls-button) {
  width: 32px;
  height: 32px;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

:deep(.vue-flow__controls-button:hover) {
  background: #f5f7fa;
  border-color: #409eff;
}

:deep(.vue-flow__controls-button svg) {
  width: 16px;
  height: 16px;
  fill: #606266;
}

:deep(.vue-flow__controls-button:hover svg) {
  fill: #409eff;
}
</style>
