import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { WorkflowConfig, Position } from '@/types/workflow'
import { getAgentTypes, type AgentTypes } from '@/api/promptTemplate'

// Viewport 类型定义
export interface Viewport {
  x: number
  y: number
  zoom: number
}

// Vue Flow的Node和Edge类型（简化版，实际使用时从@vue-flow/core导入）
export interface FlowNode {
  id: string
  type: string
  label: string
  position: Position
  data: Record<string, any>
  style?: Record<string, string>
}

export interface FlowEdge {
  id: string
  source: string
  target: string
  type?: string
  label?: string
  data?: Record<string, any>
}

export const useWorkflowStore = defineStore('workflow', () => {
  // 当前编辑的工作流配置
  const currentConfig = ref<WorkflowConfig | null>(null)
  const workflowId = ref<string | null>(null)
  const workflowName = ref<string>('新工作流')
  const workflowDescription = ref<string>('')
  const workflowParameters = ref<Record<string, any>>({})

  // Vue Flow状态
  const nodes = ref<FlowNode[]>([])
  const edges = ref<FlowEdge[]>([])
  const viewport = ref<Viewport>({ x: 0, y: 0, zoom: 1 })

  // UI状态
  const selectedNode = ref<FlowNode | null>(null)
  const selectedEdge = ref<FlowEdge | null>(null)
  const isDirty = ref(false) // 是否有未保存的更改

  // 节点工具箱状态
  const nodePaletteVisible = ref(true)
  const configPanelVisible = ref(false)

  // 撤销/重做历史
  interface HistoryState {
    nodes: FlowNode[]
    edges: FlowEdge[]
  }
  const history = ref<HistoryState[]>([])
  const historyIndex = ref(-1)
  const maxHistorySize = 50

  // 计算属性
  const hasChanges = computed(() => isDirty.value)
  const canSave = computed(() => nodes.value.length > 0)

  // Actions
  async function loadWorkflow(config: WorkflowConfig) {
    currentConfig.value = config
    workflowName.value = config.name
    workflowDescription.value = config.description || ''
    workflowParameters.value = config.parameters || {}

    // 获取所有智能体类型（用于更新节点名称）
    let agentTypes: AgentTypes | null = null
    try {
      agentTypes = await getAgentTypes()
    } catch (error) {
      console.warn('获取智能体类型失败，将使用节点原有名称:', error)
    }

    // 转换配置为Vue Flow格式，并更新节点标签以与工具箱对齐
    const regularNodes = config.nodes.map(node => {
      let nodeLabel = node.name // 默认使用节点原有名称

      // 对于智能体节点，尝试从 API 获取对应的智能体名称
      if (agentTypes && (node.type === 'analyst' || node.type === 'researcher' || 
          node.type === 'trader' || node.type === 'risk_analyst' || node.type === 'manager')) {
        const inferredAgentType = inferAgentTypeFromConfig(node.type, node.config || {})
        if (inferredAgentType) {
          const agentName = findAgentName(inferredAgentType, agentTypes)
          if (agentName) {
            nodeLabel = agentName
          }
        }
      }

      return {
        id: node.id,
        type: node.type,
        label: nodeLabel,
        position: node.position || { x: 0, y: 0 },
        data: node.config,
        style: getNodeStyle(node.category)
      }
    })

    // 添加 START 和 END 节点到可视化中
    // 计算节点位置：START 在最左侧，END 在最右侧
    const allNodePositions = regularNodes.map(n => n.position.x)
    const allNodeYPositions = regularNodes.map(n => n.position.y)
    const minX = allNodePositions.length > 0 ? Math.min(...allNodePositions) : 0
    const maxX = allNodePositions.length > 0 ? Math.max(...allNodePositions) : 800
    const minY = allNodeYPositions.length > 0 ? Math.min(...allNodeYPositions) : 0
    const maxY = allNodeYPositions.length > 0 ? Math.max(...allNodeYPositions) : 600
    const centerY = (minY + maxY) / 2

    // START 节点：放在最左侧，垂直居中
    const startNode: FlowNode = {
      id: 'START',
      type: 'start',
      label: '开始',
      position: { x: Math.max(0, minX - 250), y: centerY },
      data: {},
      style: {
        background: '#4caf50',
        border: '2px solid #2e7d32',
        color: 'white',
        fontWeight: 'bold'
      }
    }

    // END 节点：放在最右侧，垂直居中
    const endNode: FlowNode = {
      id: 'END',
      type: 'end',
      label: '结束',
      position: { x: maxX + 250, y: centerY },
      data: {},
      style: {
        background: '#f44336',
        border: '2px solid #c62828',
        color: 'white',
        fontWeight: 'bold'
      }
    }

    // 合并所有节点（包括 START 和 END）
    nodes.value = [startNode, ...regularNodes, endNode]

    // 处理边：条件边需要为每个映射目标创建独立的边
    const processedEdges: FlowEdge[] = []
    const nodeIdSet = new Set(nodes.value.map(n => n.id)) // 用于验证节点是否存在（包括 START 和 END）
    
    for (const edge of config.edges) {
      // 验证边的source和target都是有效的节点ID（包括 START 和 END）
      if (!nodeIdSet.has(edge.source)) {
        console.warn(`跳过无效的边: ${edge.source} -> ${edge.target} (源节点不存在)`)
        continue
      }
      if (!nodeIdSet.has(edge.target)) {
        console.warn(`跳过无效的边: ${edge.source} -> ${edge.target} (目标节点不存在)`)
        continue
      }
      
      // 修复：检查条件边时，不仅检查type，还要检查是否有condition.mapping
      // 因为数据库中可能将条件边保存为type: 'direct'，但有condition.mapping
      if ((edge.type === 'conditional' || edge.condition?.mapping) && edge.condition?.mapping) {
        // 条件边处理逻辑
        // 关键修复：检查是否已经是拆分后的边（即 mapping 中只包含当前 target）
        // 如果 mapping 中包含多个目标，说明是聚合边，需要拆分
        // 如果 mapping 中只包含当前 target，说明已经是拆分边，直接使用
        const mapping = edge.condition.mapping
        const targets = Object.values(mapping)
        
        // 如果 mapping 中只有一个目标，且该目标就是当前边的 target，说明这是已经拆分好的边
        // 直接作为一条边加载，不再拆分，也不添加 ID 后缀
        if (targets.length === 1 && targets[0] === edge.target) {
             processedEdges.push({
                id: edge.id, // 保持原 ID
                source: edge.source,
                target: edge.target,
                type: 'step',
                label: edge.label || '条件',
                data: {
                  ...edge.condition,
                  conditionResult: Object.keys(mapping)[0]
                }
             })
             continue
        }

        // 否则（聚合边），需要拆分
        let edgeIndex = 0
        for (const [conditionResult, targetNodeId] of Object.entries(mapping)) {
          // 验证目标节点是否存在（包括 START 和 END）
          if (!nodeIdSet.has(targetNodeId)) {
            console.warn(`跳过无效的条件边目标: ${edge.source} -> ${targetNodeId} (节点不存在)`)
            continue
          }
          
          // 为每个映射目标创建一条边
          processedEdges.push({
            id: `${edge.id}_${edgeIndex}`,
            source: edge.source,
            target: targetNodeId, // 使用mapping中的节点ID
            type: 'step',
            label: edge.label || '条件', // 使用保存的 label，如果没有则使用默认值
            data: {
              ...edge.condition,
              // 保留原始条件配置，但标记这是哪条路径
              conditionResult // 条件函数返回的值
            }
          })
          edgeIndex++
        }
      } else {
        // 直接边（包括 START 和 END 的边）
        processedEdges.push({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          type: 'default',
          label: edge.label || '', // 使用保存的 label
          data: undefined
        })
      }
    }
    
    edges.value = processedEdges

    // 重置历史
    history.value = []
    historyIndex.value = -1
    saveHistory() // 保存初始状态
    
    isDirty.value = false
    
    // 触发视图更新，确保所有节点可见
    // 注意：实际的 fitView 操作需要在 FlowCanvas 组件中通过 nextTick 触发
  }

  function addNode(nodeType: string, position: Position, config?: Record<string, any>) {
    saveHistory()
    
    // 如果提供了配置，使用提供的配置；否则使用默认配置
    const nodeConfig = config || getNodeDefaultConfig(nodeType)
    
    // 确保配置中包含 agent_type（优先使用 agent_type，向后兼容从特定类型字段推断）
    if (!nodeConfig.agent_type) {
      if (nodeConfig.analyst_type) {
        nodeConfig.agent_type = nodeConfig.analyst_type
      } else if (nodeConfig.researcher_type) {
        nodeConfig.agent_type = nodeConfig.researcher_type
      } else if (nodeConfig.manager_type) {
        nodeConfig.agent_type = nodeConfig.manager_type
      } else if (nodeConfig.risk_type) {
        nodeConfig.agent_type = nodeConfig.risk_type
      } else if (nodeType === 'trader') {
        nodeConfig.agent_type = 'trader'
      }
    }
    
    // 根据 agent_type 生成节点名称（优先使用 agent_type）
    let nodeLabel = getNodeDefaultName(nodeType)
    const agentType = nodeConfig.agent_type
    if (agentType) {
      // 根据 agent_type 生成节点名称
      const agentTypeNames: Record<string, string> = {
        // 分析师类型
        market_analyst: '市场分析师',
        fundamentals_analyst: '基本面分析师',
        news_analyst: '新闻分析师',
        social_media_analyst: '社交媒体分析师',
        // 研究员类型
        bull_researcher: '看涨研究员',
        bear_researcher: '看跌研究员',
        // 管理者类型
        research_manager: '研究经理',
        risk_manager: '风险经理',
        // 风险分析师类型
        aggressive_debator: '激进风险分析师',
        conservative_debator: '保守风险分析师',
        neutral_debator: '中性风险分析师',
        // 交易员类型
        trader: '交易员',
        // 向后兼容简短形式
        market: '市场分析师',
        fundamentals: '基本面分析师',
        news: '新闻分析师',
        social: '社交媒体分析师',
        bull: '看涨研究员',
        bear: '看跌研究员',
        research: '研究经理',
        risk: '风险经理',
        risky: '激进风险分析师',
        safe: '保守风险分析师',
        neutral: '中性风险分析师'
      }
      nodeLabel = agentTypeNames[agentType] || nodeLabel
    }
    
    // 清理多余的特定类型字段，只保留 agent_type
    const cleanedConfig = { ...nodeConfig }
    delete cleanedConfig.analyst_type
    delete cleanedConfig.researcher_type
    delete cleanedConfig.manager_type
    delete cleanedConfig.risk_type
    
    const newNode: FlowNode = {
      id: `node_${Date.now()}`,
      type: nodeType,
      label: nodeLabel,
      position,
      data: cleanedConfig,
      style: getNodeStyle(getNodeCategory(nodeType))
    }
    nodes.value.push(newNode)
    isDirty.value = true
  }

  function deleteNode(nodeId: string) {
    // 不允许删除 START 和 END 节点
    if (nodeId === 'START' || nodeId === 'END') {
      console.warn('不能删除 START 或 END 节点')
      return
    }
    saveHistory()
    nodes.value = nodes.value.filter(n => n.id !== nodeId)
    edges.value = edges.value.filter(e => e.source !== nodeId && e.target !== nodeId)
    if (selectedNode.value?.id === nodeId) {
      selectedNode.value = null
    }
    isDirty.value = true
  }

  // 更新节点位置（用于拖拽后保存位置）
  function updateNodePosition(nodeId: string, position: Position) {
    const node = nodes.value.find(n => n.id === nodeId)
    if (node) {
      // 不保存历史，因为拖拽是连续操作，只在拖拽结束时保存
      node.position = position
      isDirty.value = true
    }
  }

  function addEdge(source: string, target: string, type: 'direct' | 'conditional' = 'direct') {
    // 验证连接是否有效
    if (source === target) {
      return false // 不能连接到自身
    }
    
    // 检查是否已存在相同的连接
    const existingEdge = edges.value.find(
      e => e.source === source && e.target === target
    )
    if (existingEdge) {
      return false // 连接已存在
    }
    
    saveHistory()
    
    const newEdge: FlowEdge = {
      id: `edge_${Date.now()}`,
      source,
      target,
      type: type === 'conditional' ? 'step' : 'default',
      label: type === 'conditional' ? '条件' : '',
      data: type === 'conditional' ? { function: '', mapping: {} } : undefined
    }
    edges.value.push(newEdge)
    isDirty.value = true
    return true
  }

  function deleteEdge(edgeId: string) {
    saveHistory()
    edges.value = edges.value.filter(e => e.id !== edgeId)
    if (selectedEdge.value?.id === edgeId) {
      selectedEdge.value = null
    }
    isDirty.value = true
  }

  function updateNodeConfig(nodeId: string, config: Record<string, any>) {
    const node = nodes.value.find(n => n.id === nodeId)
    if (node) {
      saveHistory()
      // 清理多余的特定类型字段，只保留 agent_type
      const cleanedConfig = { ...config }
      delete cleanedConfig.analyst_type
      delete cleanedConfig.researcher_type
      delete cleanedConfig.manager_type
      delete cleanedConfig.risk_type
      
      node.data = { ...node.data, ...cleanedConfig }
      node.label = config.name || node.label
      isDirty.value = true
    }
  }

  function updateEdgeConfig(edgeId: string, config: Record<string, any>) {
    const edge = edges.value.find(e => e.id === edgeId)
    if (edge) {
      saveHistory()
      edge.data = { ...edge.data, ...config }
      edge.type = config.type === 'conditional' ? 'step' : 'default'
      edge.label = config.type === 'conditional' ? '条件' : ''
      isDirty.value = true
    }
  }

  // 删除选中的节点或边
  function deleteSelected() {
    if (selectedNode.value) {
      deleteNode(selectedNode.value.id)
    } else if (selectedEdge.value) {
      deleteEdge(selectedEdge.value.id)
    }
  }

  // 清理节点配置，移除多余的特定类型字段
  function cleanNodeConfig(config: Record<string, any>): Record<string, any> {
    if (!config || typeof config !== 'object') {
      return config
    }
    
    const cleaned = { ...config }
    // 移除特定类型字段，只保留 agent_type
    delete cleaned.analyst_type
    delete cleaned.researcher_type
    delete cleaned.manager_type
    delete cleaned.risk_type
    
    return cleaned
  }

  function exportConfig(): WorkflowConfig {
    // 过滤掉 START 和 END 节点，它们只是可视化用的虚拟节点
    const regularNodes = nodes.value.filter(node => node.id !== 'START' && node.id !== 'END')
    
    return {
      version: '1.0',
      name: workflowName.value,
      description: workflowDescription.value,
      metadata: {
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      nodes: regularNodes.map(node => ({
        id: node.id,
        type: node.type as any,
        name: node.label as string,
        category: getNodeCategory(node.type),
        config: cleanNodeConfig(node.data || {}),
        position: node.position
      })),
      edges: edges.value.map(edge => {
        const edgeConfig: any = {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          type: edge.type === 'step' ? ('conditional' as const) : ('direct' as const)
        }
        if (edge.data && Object.keys(edge.data).length > 0) {
          // 只保留后端需要的字段
          if (edgeConfig.type === 'conditional') {
             // 关键修复：保存时，mapping 只保留当前路径的映射
             // 这样下次加载时，就不会被视为聚合边而再次拆分
             const conditionResult = edge.data.conditionResult
             let mapping = edge.data.mapping
             
             // 如果有明确的 conditionResult，构建最小化 mapping
             if (conditionResult && mapping && mapping[conditionResult] === edge.target) {
                 mapping = { [conditionResult]: edge.target }
             }
             
             edgeConfig.condition = {
               function: edge.data.function,
               mapping: mapping
             }
          } else {
             edgeConfig.condition = edge.data
          }
        }
        // 保存 label 属性（如果存在）
        if (edge.label) {
          edgeConfig.label = edge.label
        }
        return edgeConfig
      }),
      parameters: workflowParameters.value || {}
    }
  }

  function reset() {
    currentConfig.value = null
    workflowId.value = null
    workflowName.value = '新工作流'
    workflowDescription.value = ''
    nodes.value = []
    edges.value = []
    selectedNode.value = null
    selectedEdge.value = null
    isDirty.value = false
    history.value = []
    historyIndex.value = -1
  }

  // 保存历史状态
  function saveHistory() {
    const state: HistoryState = {
      nodes: JSON.parse(JSON.stringify(nodes.value)),
      edges: JSON.parse(JSON.stringify(edges.value))
    }
    
    // 如果当前不在历史末尾，删除后面的历史
    if (historyIndex.value < history.value.length - 1) {
      history.value = history.value.slice(0, historyIndex.value + 1)
    }
    
    // 添加新状态
    history.value.push(state)
    historyIndex.value = history.value.length - 1
    
    // 限制历史大小
    if (history.value.length > maxHistorySize) {
      history.value.shift()
      historyIndex.value = history.value.length - 1
    }
  }

  // 撤销
  function undo() {
    if (historyIndex.value > 0) {
      historyIndex.value--
      const state = history.value[historyIndex.value]
      nodes.value = JSON.parse(JSON.stringify(state.nodes))
      edges.value = JSON.parse(JSON.stringify(state.edges))
      isDirty.value = true
    }
  }

  // 重做
  function redo() {
    if (historyIndex.value < history.value.length - 1) {
      historyIndex.value++
      const state = history.value[historyIndex.value]
      nodes.value = JSON.parse(JSON.stringify(state.nodes))
      edges.value = JSON.parse(JSON.stringify(state.edges))
      isDirty.value = true
    }
  }

  // 检查是否可以撤销
  const canUndo = computed(() => historyIndex.value > 0)
  
  // 检查是否可以重做
  const canRedo = computed(() => historyIndex.value < history.value.length - 1)

  // 辅助函数
  function getNodeStyle(category: string): Record<string, string> {
    const styles: Record<string, Record<string, string>> = {
      analyst: { background: '#e3f2fd', border: '2px solid #1976d2' },
      researcher: { background: '#f3e5f5', border: '2px solid #7b1fa2' },
      manager: { background: '#fff3e0', border: '2px solid #ef6c00' },
      trader: { background: '#e8f5e9', border: '2px solid #388e3c' },
      risk_analyst: { background: '#ffebee', border: '2px solid #c62828' },
      tool: { background: '#f1f8e9', border: '2px solid #689f38' },
      utility: { background: '#fafafa', border: '2px solid #424242' }
    }
    return styles[category] || styles.utility
  }

  function getNodeCategory(nodeType: string): string {
    if (nodeType === 'analyst') return 'analyst'
    if (nodeType === 'researcher') return 'researcher'
    if (nodeType === 'manager') return 'manager'
    if (nodeType === 'trader') return 'trader'
    if (nodeType === 'risk_analyst') return 'risk_analyst'
    if (nodeType === 'tool_node') return 'tool'
    if (nodeType === 'message_clear') return 'utility'
    return 'utility'
  }

  function getNodeDefaultName(nodeType: string): string {
    const names: Record<string, string> = {
      analyst: '分析师',
      researcher: '研究员',
      manager: '经理',
      trader: '交易员',
      risk_analyst: '风险分析师',
      tool_node: '工具节点',
      message_clear: '消息清理'
    }
    return names[nodeType] || '节点'
  }

  // 从节点配置推断 agent_type
  function inferAgentTypeFromConfig(nodeType: string, config: Record<string, any>): string | null {
    // 优先使用 agent_type
    if (config.agent_type) {
      return config.agent_type
    }

    // 向后兼容：如果没有 agent_type，尝试从特定类型字段推断
    if (nodeType === 'analyst' && config.analyst_type) {
      return config.analyst_type
    }
    if (nodeType === 'researcher' && config.researcher_type) {
      return config.researcher_type
    }
    if (nodeType === 'trader') {
      return config.trader_type || 'trader'
    }
    if (nodeType === 'risk_analyst' && config.risk_type) {
      return config.risk_type
    }
    if (nodeType === 'manager' && config.manager_type) {
      return config.manager_type
    }

    // 无法推断
    return null
  }

  // 在 AgentTypes 中查找对应的智能体名称
  function findAgentName(agentType: string, agentTypes: AgentTypes): string | null {
    // 遍历所有类别
    const categories: Array<keyof AgentTypes> = ['analysts', 'researchers', 'trader', 'risk_management', 'managers']
    
    for (const category of categories) {
      const agents = agentTypes[category]
      if (Array.isArray(agents)) {
        const agent = agents.find(a => a.type === agentType)
        if (agent) {
          return agent.name
        }
      }
    }
    
    return null
  }

  function getNodeDefaultConfig(nodeType: string): Record<string, any> {
    const configs: Record<string, Record<string, any>> = {
      analyst: { agent_type: 'market_analyst', llm_type: 'quick_thinking' },
      researcher: { agent_type: 'bull_researcher' },
      manager: { agent_type: 'research_manager' },
      trader: { agent_type: 'trader' },
      risk_analyst: { agent_type: 'aggressive_debator' },
      tool_node: {},
      message_clear: {}
    }
    return configs[nodeType] || {}
  }

  return {
    // State
    currentConfig,
    workflowId,
    workflowName,
    workflowDescription,
    workflowParameters,
    nodes,
    edges,
    viewport,
    selectedNode,
    selectedEdge,
    isDirty,
    nodePaletteVisible,
    configPanelVisible,

    // Getters
    hasChanges,
    canSave,
    canUndo,
    canRedo,

    // Actions
    loadWorkflow,
    addNode,
    deleteNode,
    deleteSelected,
    addEdge,
    deleteEdge,
    updateNodeConfig,
    updateNodePosition,
    updateEdgeConfig,
    exportConfig,
    undo,
    redo,
    reset,
    saveHistory
  }
})

