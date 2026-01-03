import { ApiClient } from './request'
import type {
  WorkflowConfig,
  WorkflowListItem,
  WorkflowValidationResult
} from '@/types/workflow'

export interface WorkflowCreateRequest {
  name: string
  description?: string
  config: WorkflowConfig
}

export interface WorkflowUpdateRequest {
  name?: string
  description?: string
  config?: WorkflowConfig
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
}

export const workflowApi = {
  // 获取工作流列表
  listWorkflows: (skip = 0, limit = 100) =>
    ApiClient.get<WorkflowListItem[]>('/api/workflows', { skip, limit }),

  // 获取工作流详情
  getWorkflow: (workflowId: string) =>
    ApiClient.get<ApiResponse<WorkflowConfig>>(`/api/workflows/${workflowId}`),

  // 创建工作流
  createWorkflow: (data: WorkflowCreateRequest) =>
    ApiClient.post<ApiResponse<WorkflowConfig>>('/api/workflows', data),

  // 更新工作流
  updateWorkflow: (workflowId: string, data: WorkflowUpdateRequest) =>
    ApiClient.put<ApiResponse<WorkflowConfig>>(`/api/workflows/${workflowId}`, data),

  // 删除工作流
  deleteWorkflow: (workflowId: string) =>
    ApiClient.delete<ApiResponse<void>>(`/api/workflows/${workflowId}`),

  // 验证工作流
  validateWorkflow: (workflowId: string) =>
    ApiClient.post<WorkflowValidationResult>(`/api/workflows/${workflowId}/validate`),

  // 获取默认工作流配置
  getDefaultWorkflow: (selectedAnalysts?: string[]) =>
    ApiClient.get<ApiResponse<WorkflowConfig>>('/api/workflows/default/config', 
      selectedAnalysts ? { selected_analysts: selectedAnalysts.join(',') } : undefined
    ),

  // 🔥 新增：获取智能体配置
  getAgentConfigs: () =>
    ApiClient.get<ApiResponse<{
      agent_types: any
      tool_configs: Record<string, any>
    }>>('/api/workflows/agent-configs'),

  // 🔥 新增：获取节点模板
  getNodeTemplates: (agentType?: string) =>
    ApiClient.get<ApiResponse<Record<string, any[]>>>('/api/workflows/node-templates',
      agentType ? { agent_type: agentType } : undefined
    )
}

