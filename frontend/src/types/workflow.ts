/**
 * 工作流配置类型定义
 */

export enum NodeType {
  ANALYST = 'analyst',
  RESEARCHER = 'researcher',
  MANAGER = 'manager',
  TRADER = 'trader',
  RISK_ANALYST = 'risk_analyst',
  TOOL_NODE = 'tool_node',
  MESSAGE_CLEAR = 'message_clear'
}

export enum EdgeType {
  DIRECT = 'direct',
  CONDITIONAL = 'conditional',
  LOOP = 'loop'
}

export interface Position {
  x: number
  y: number
}

export interface ConditionConfig {
  function: string
  mapping: Record<string, string>
}

// 🔥 新增：智能体配置引用
export interface AgentConfigRef {
  template_id?: string  // 引用的提示词模板ID
  tool_config_ref?: string  // 引用的工具配置ID（可选，默认使用agent_type对应的工具配置）
}

// 🔥 新增：节点配置覆盖
export interface NodeConfigOverrides {
  template_variables?: Record<string, any>  // 模板变量覆盖
  tool_overrides?: string[]  // 工具列表覆盖（可选）
}

export interface NodeConfig {
  id: string
  type: NodeType
  name: string
  category: string
  config: Record<string, any>
  position?: Position
  
  // 🔥 新增字段：基于单智能体配置
  agent_type?: string  // 引用的智能体类型
  agent_config_ref?: AgentConfigRef  // 智能体配置引用
  config_overrides?: NodeConfigOverrides  // 节点特定配置覆盖
  
  // 🔥 新增：输入输出定义
  inputs?: string[]  // 输入字段列表（从上游节点接收）
  outputs?: string[]  // 输出字段列表（发送给下游节点）
}

export interface EdgeConfig {
  id: string
  source: string
  target: string
  type: EdgeType
  condition?: ConditionConfig
  label?: string  // 边的标签（可选）
  
  // 🔥 新增：数据映射定义
  data_mapping?: Record<string, string>  // source_output -> target_input 的映射
}

export interface WorkflowConfig {
  version: string
  name: string
  description?: string
  metadata?: {
    created_at?: string
    updated_at?: string
    author?: string
    is_default?: boolean
    [key: string]: any
  }
  nodes: NodeConfig[]
  edges: EdgeConfig[]
  parameters?: Record<string, any>
}

export interface WorkflowListItem {
  id: string
  name: string
  description?: string
  created_at: string
  updated_at: string
  author?: string
}

export interface WorkflowValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
}

