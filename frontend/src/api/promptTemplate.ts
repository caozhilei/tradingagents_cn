/**
 * 提示词模板API
 */

import request from './request'

export interface PromptTemplateContent {
  system_prompt: string
  tool_guidance?: string
  analysis_requirements?: string
  output_format?: string
  constraints?: {
    forbidden?: string[]
    required?: string[]
  }
  variables?: Record<string, string>
}

export interface PromptTemplate {
  id: string
  agent_type: string
  agent_name: string
  template_name: string
  template_display_name: string
  description?: string
  content: PromptTemplateContent
  version: number
  is_system: boolean
  is_default: boolean
  is_active: boolean
  created_by?: string
  updated_by?: string
  tags: string[]
  category?: string
  tool_configs?: string[]  // 工具ID列表，覆盖智能体默认配置
  created_at: string
  updated_at: string
  usage_count: number
  last_used_at?: string
}

export interface PromptTemplateCreate {
  agent_type: string
  agent_name: string
  template_name: string
  template_display_name: string
  description?: string
  content: PromptTemplateContent
  tags?: string[]
  category?: string
  is_default?: boolean
  tool_configs?: string[]  // 工具ID列表，覆盖智能体默认配置
}

export interface PromptTemplateUpdate {
  template_display_name?: string
  description?: string
  content?: PromptTemplateContent
  tags?: string[]
  category?: string
  is_default?: boolean
  is_active?: boolean
  change_description?: string
  tool_configs?: string[]  // 工具ID列表，覆盖智能体默认配置
}

export interface AgentType {
  type: string
  name: string
}

export interface AgentTypes {
  analysts: AgentType[]
  researchers: AgentType[]
  trader: AgentType[]
  risk_management: AgentType[]
  managers: AgentType[]
}

/**
 * 获取所有智能体类型
 */
export async function getAgentTypes(): Promise<AgentTypes> {
  try {
    const response = await request.get('/api/prompt-templates/agents', {
      skipErrorHandler: false
    })
    // 处理响应格式：可能是直接返回数据，也可能是包装在 ApiResponse 中
    if (response && typeof response === 'object') {
      // 如果响应有 data 字段，说明是 ApiResponse 格式
      if ('data' in response && response.data) {
        return response.data as AgentTypes
      }
      // 如果响应本身就是 AgentTypes 格式（直接返回字典）
      if ('analysts' in response || 'researchers' in response) {
        return response as AgentTypes
      }
    }
    return response as AgentTypes
  } catch (error: any) {
    console.error('获取智能体类型失败:', error)
    throw error
  }
}

/**
 * 创建模板
 */
export async function createTemplate(data: PromptTemplateCreate): Promise<PromptTemplate> {
  const response = await request.post('/api/prompt-templates', data)
  // 处理响应格式
  if (response && typeof response === 'object') {
    if ('data' in response && response.data) {
      return response.data as PromptTemplate
    }
    if ('id' in response || 'template_name' in response) {
      return response as PromptTemplate
    }
  }
  return response as PromptTemplate
}

/**
 * 获取模板列表
 */
export async function getTemplates(params?: {
  agent_type?: string
  is_system?: boolean
  is_active?: boolean
}): Promise<PromptTemplate[]> {
  const response = await request.get('/api/prompt-templates', { params })
  // 处理响应格式
  if (Array.isArray(response)) {
    return response
  } else if (response && typeof response === 'object' && 'data' in response) {
    return response.data || []
  }
  return []
}

/**
 * 获取模板详情
 */
export async function getTemplate(templateId: string): Promise<PromptTemplate> {
  // 确保ID是字符串格式
  const id = typeof templateId === 'string' ? templateId : String(templateId)
  
  try {
    const response = await request.get(`/api/prompt-templates/${encodeURIComponent(id)}`)
    // 处理响应格式
    if (response && typeof response === 'object') {
      if ('data' in response && response.data) {
        return response.data as PromptTemplate
      }
      // 直接返回数据
      if ('id' in response || 'template_name' in response) {
        return response as PromptTemplate
      }
    }
    return response as PromptTemplate
  } catch (error: any) {
    console.error('获取模板详情API调用失败:', error)
    console.error('模板ID:', id, '类型:', typeof id)
    throw error
  }
}

/**
 * 更新模板
 */
export async function updateTemplate(
  templateId: string,
  data: PromptTemplateUpdate
): Promise<PromptTemplate> {
  const response = await request.put(`/api/prompt-templates/${templateId}`, data)
  // 处理响应格式
  if (response && typeof response === 'object') {
    if ('data' in response && response.data) {
      return response.data as PromptTemplate
    }
    if ('id' in response || 'template_name' in response) {
      return response as PromptTemplate
    }
  }
  return response as PromptTemplate
}

/**
 * 删除模板
 */
export function deleteTemplate(templateId: string): Promise<void> {
  return request.delete(`/api/prompt-templates/${templateId}`)
}

/**
 * 获取模板版本历史
 */
export async function getTemplateVersions(templateId: string): Promise<any[]> {
  const response = await request.get(`/api/prompt-templates/${templateId}/versions`)
  // 处理响应格式
  if (Array.isArray(response)) {
    return response
  } else if (response && typeof response === 'object' && 'data' in response) {
    return response.data || []
  }
  return []
}

/**
 * 恢复指定版本
 */
export async function restoreVersion(templateId: string, version: number): Promise<PromptTemplate> {
  const response = await request.post(`/api/prompt-templates/${templateId}/restore/${version}`)
  // 处理响应格式
  if (response && typeof response === 'object') {
    if ('data' in response && response.data) {
      return response.data as PromptTemplate
    }
    if ('id' in response || 'template_name' in response) {
      return response as PromptTemplate
    }
  }
  return response as PromptTemplate
}

/**
 * 获取默认模板
 */
export async function getDefaultTemplate(agentType: string): Promise<PromptTemplate> {
  const response = await request.get(`/api/prompt-templates/agent/${agentType}/default`)
  // 处理响应格式
  if (response && typeof response === 'object') {
    if ('data' in response && response.data) {
      return response.data as PromptTemplate
    }
    if ('id' in response || 'template_name' in response) {
      return response as PromptTemplate
    }
  }
  return response as PromptTemplate
}

/**
 * 设置用户模板配置
 */
export function setUserTemplateConfig(
  agentType: string,
  templateId: string
): Promise<any> {
  return request.post('/api/prompt-templates/user-config', null, {
    params: { agent_type: agentType, template_id: templateId }
  })
}

/**
 * 获取用户配置的模板
 */
export function getUserTemplate(agentType: string): Promise<PromptTemplate> {
  return request.get(`/api/prompt-templates/user-config/${agentType}`)
}

