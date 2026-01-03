/**
 * 工具配置API接口
 */

import request from './request'

export interface ToolParameter {
  name: string
  type: string
  description: string
  required: boolean
  default?: any
}

export interface ToolConfig {
  id?: string
  tool_name: string
  tool_display_name: string
  description: string
  category: string
  tool_type: string
  supported_markets: string[]
  parameters: ToolParameter[]
  default_config: Record<string, any>
  enabled: boolean
  priority: number
  is_system: boolean
  created_at?: string
  updated_at?: string
  usage_count?: number
  last_used_at?: string
}

export interface AgentToolConfig {
  id?: string
  agent_type: string
  tool_configs: string[]
  default_tools: string[]
  tool_priorities: Record<string, number>
  created_at?: string
  updated_at?: string
}

export interface ToolConfigCreate {
  tool_name: string
  tool_display_name: string
  description: string
  category: string
  tool_type: string
  supported_markets?: string[]
  parameters?: ToolParameter[]
  default_config?: Record<string, any>
  enabled?: boolean
  priority?: number
}

export interface ToolConfigUpdate {
  tool_display_name?: string
  description?: string
  category?: string
  tool_type?: string
  supported_markets?: string[]
  parameters?: ToolParameter[]
  default_config?: Record<string, any>
  enabled?: boolean
  priority?: number
}

export interface AgentToolConfigCreate {
  agent_type: string
  tool_configs?: string[]
  default_tools?: string[]
  tool_priorities?: Record<string, number>
}

export interface AgentToolConfigUpdate {
  tool_configs?: string[]
  default_tools?: string[]
  tool_priorities?: Record<string, number>
}

/**
 * 获取所有工具列表
 */
export function getAllTools(params?: {
  category?: string
  tool_type?: string
  enabled?: boolean
}): Promise<ToolConfig[]> {
  return request({
    url: '/api/tools',
    method: 'get',
    params
  })
}

/**
 * 获取工具详情
 */
export function getToolById(toolId: string): Promise<ToolConfig> {
  return request({
    url: `/api/tools/${toolId}`,
    method: 'get'
  })
}

/**
 * 创建工具配置
 */
export function createToolConfig(data: ToolConfigCreate): Promise<ToolConfig> {
  return request({
    url: '/api/tools',
    method: 'post',
    data
  })
}

/**
 * 更新工具配置
 */
export function updateToolConfig(toolId: string, data: ToolConfigUpdate): Promise<ToolConfig> {
  return request({
    url: `/api/tools/${toolId}`,
    method: 'put',
    data
  })
}

/**
 * 删除工具配置
 */
export function deleteToolConfig(toolId: string): Promise<void> {
  return request({
    url: `/api/tools/${toolId}`,
    method: 'delete'
  })
}

/**
 * 获取智能体工具配置
 */
export function getAgentToolConfig(agentType: string): Promise<AgentToolConfig> {
  return request({
    url: `/api/tools/agent/${agentType}`,
    method: 'get'
  })
}

/**
 * 更新智能体工具配置
 */
export function updateAgentToolConfig(
  agentType: string,
  data: AgentToolConfigUpdate
): Promise<AgentToolConfig> {
  return request({
    url: `/api/tools/agent/${agentType}`,
    method: 'put',
    data
  })
}

/**
 * 创建智能体工具配置
 */
export function createAgentToolConfig(data: AgentToolConfigCreate): Promise<AgentToolConfig> {
  return request({
    url: '/api/tools/agent',
    method: 'post',
    data
  })
}

/**
 * 初始化工具到数据库
 */
export function initializeTools(): Promise<{
  message: string
  initialized: number
  skipped: number
  errors: number
}> {
  return request({
    url: '/api/tools/initialize',
    method: 'post'
  })
}
