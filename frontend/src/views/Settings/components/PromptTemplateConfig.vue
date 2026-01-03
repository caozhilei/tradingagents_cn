<template>
  <div class="prompt-template-config">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>智能体提示词配置</h3>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            创建模板
          </el-button>
        </div>
      </template>

      <!-- 智能体类型选择 -->
      <el-tabs v-model="activeAgentType" @tab-change="handleAgentTypeChange">
        <el-tab-pane label="分析师" name="analysts">
          <el-radio-group v-model="selectedAgent" @change="loadTemplates">
            <el-radio
              v-for="agent in agentTypes.analysts"
              :key="agent.type"
              :label="agent.type"
            >
              {{ agent.name }}
            </el-radio>
          </el-radio-group>
        </el-tab-pane>

        <el-tab-pane label="研究员" name="researchers">
          <el-radio-group v-model="selectedAgent" @change="loadTemplates">
            <el-radio
              v-for="agent in agentTypes.researchers"
              :key="agent.type"
              :label="agent.type"
            >
              {{ agent.name }}
            </el-radio>
          </el-radio-group>
        </el-tab-pane>

        <el-tab-pane label="交易员" name="trader">
          <el-radio-group v-model="selectedAgent" @change="loadTemplates">
            <el-radio
              v-for="agent in agentTypes.trader"
              :key="agent.type"
              :label="agent.type"
            >
              {{ agent.name }}
            </el-radio>
          </el-radio-group>
        </el-tab-pane>

        <el-tab-pane label="风险管理" name="risk_management">
          <el-radio-group v-model="selectedAgent" @change="loadTemplates">
            <el-radio
              v-for="agent in agentTypes.risk_management"
              :key="agent.type"
              :label="agent.type"
            >
              {{ agent.name }}
            </el-radio>
          </el-radio-group>
        </el-tab-pane>

        <el-tab-pane label="管理层" name="managers">
          <el-radio-group v-model="selectedAgent" @change="loadTemplates">
            <el-radio
              v-for="agent in agentTypes.managers"
              :key="agent.type"
              :label="agent.type"
            >
              {{ agent.name }}
            </el-radio>
          </el-radio-group>
        </el-tab-pane>
      </el-tabs>

      <!-- 模板列表 -->
      <div v-if="selectedAgent" class="template-list">
        <el-loading v-if="loading" text="加载中..." />
        <el-empty v-else-if="templates.length === 0" description="暂无模板，请创建新模板" />
        <el-table v-else :data="templates" style="width: 100%">
          <el-table-column prop="template_display_name" label="模板名称" width="200" />
          <el-table-column prop="description" label="描述" show-overflow-tooltip />
          <el-table-column prop="is_default" label="默认" width="80" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.is_default" type="success" size="small">默认</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_system" label="类型" width="100" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.is_system" type="info" size="small">系统</el-tag>
              <el-tag v-else type="warning" size="small">自定义</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="version" label="版本" width="80" align="center" />
          <el-table-column prop="usage_count" label="使用次数" width="100" align="center" />
          <el-table-column label="操作" width="320" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="viewTemplate(row)">查看</el-button>
              <el-button 
                v-if="!row.is_system" 
                size="small" 
                @click="editTemplate(row)"
              >
                编辑
              </el-button>
              <el-button 
                size="small" 
                type="primary" 
                @click="setAsDefault(row)"
                :disabled="row.is_default"
              >
                设为默认
              </el-button>
              <el-button 
                size="small" 
                type="success" 
                @click="useTemplate(row)"
              >
                使用
              </el-button>
              <el-button 
                v-if="!row.is_system" 
                size="small" 
                type="danger" 
                @click="handleDeleteTemplate(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑模板' : '创建模板'"
      width="80%"
      @close="handleDialogClose"
    >
      <!-- 导入提示 -->
      <el-alert
        v-if="!isEdit && formData.agent_type"
        title="💡 提示"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      >
        <template #default>
          <span>您可以从默认模板导入内容，然后在基础上进行修改。点击左下角的"导入默认模板"按钮即可。</span>
        </template>
      </el-alert>

      <el-form :model="formData" label-width="120px">
        <el-form-item label="智能体类型">
          <el-input v-model="formData.agent_type" disabled />
        </el-form-item>
        <el-form-item label="模板名称">
          <el-input v-model="formData.template_name" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="formData.template_display_name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" />
        </el-form-item>

        <!-- 系统提示词 -->
        <el-form-item label="系统提示词">
          <el-input
            v-model="formData.content.system_prompt"
            type="textarea"
            :rows="10"
            placeholder="输入系统提示词，支持 {变量名} 格式"
          />
        </el-form-item>

        <!-- 工具调用指导 -->
        <el-form-item label="工具调用指导">
          <el-input
            v-model="formData.content.tool_guidance"
            type="textarea"
            :rows="8"
            placeholder="工具调用指导将根据选择的工具自动生成，也可以手动编辑"
          />
          <div style="margin-top: 8px; font-size: 12px; color: #909399;">
            💡 提示：工具调用指导会根据您选择的工具自动生成。选择工具后，点击"生成工具调用指导"按钮更新。
          </div>
          <el-button 
            v-if="selectedToolIds.length > 0"
            type="primary" 
            size="small" 
            style="margin-top: 8px"
            @click="generateToolGuidance"
          >
            <el-icon><Refresh /></el-icon>
            生成工具调用指导
          </el-button>
        </el-form-item>

        <!-- 分析要求 -->
        <el-form-item label="分析要求">
          <el-input
            v-model="formData.content.analysis_requirements"
            type="textarea"
            :rows="5"
          />
        </el-form-item>

        <!-- 输出格式 -->
        <el-form-item label="输出格式">
          <el-input
            v-model="formData.content.output_format"
            type="textarea"
            :rows="5"
          />
        </el-form-item>

        <el-form-item label="标签">
          <el-select
            v-model="formData.tags"
            multiple
            filterable
            allow-create
            placeholder="选择或输入标签"
          />
        </el-form-item>

        <!-- 工具选择 -->
        <el-form-item label="可用工具">
          <el-select
            v-model="selectedToolIds"
            multiple
            filterable
            placeholder="选择智能体可用的工具（留空则使用默认工具）"
            style="width: 100%"
            :loading="toolsLoading"
            @change="onToolsChange"
          >
            <el-option
              v-for="tool in availableTools"
              :key="tool.id"
              :label="tool.tool_display_name"
              :value="tool.id"
            >
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>{{ tool.tool_display_name }}</span>
                <el-tag v-if="tool.is_default" type="success" size="small" style="margin-left: 8px">
                  默认
                </el-tag>
              </div>
            </el-option>
          </el-select>
          <div style="margin-top: 8px; font-size: 12px; color: #909399;">
            💡 提示：选择的工具将在智能体运行时可用。留空则使用系统默认工具配置。
          </div>
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="formData.is_default">设为默认模板</el-checkbox>
        </el-form-item>
      </el-form>

      <template #footer>
        <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
          <el-button 
            v-if="!isEdit && formData.agent_type" 
            type="info" 
            @click="importDefaultTemplate"
            :loading="importingDefault"
          >
            <el-icon><Download /></el-icon>
            导入默认模板
          </el-button>
          <div style="flex: 1;"></div>
          <div>
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" @click="saveTemplate" :loading="saving">
              保存
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 模板详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="模板详情"
      width="80%"
    >
      <div v-if="currentTemplate">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="模板名称">
            {{ currentTemplate.template_display_name }}
          </el-descriptions-item>
          <el-descriptions-item label="模板ID">
            {{ currentTemplate.template_name }}
          </el-descriptions-item>
          <el-descriptions-item label="智能体类型">
            {{ currentTemplate.agent_name }} ({{ currentTemplate.agent_type }})
          </el-descriptions-item>
          <el-descriptions-item label="版本">
            v{{ currentTemplate.version }}
          </el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag v-if="currentTemplate.is_system" type="info">系统</el-tag>
            <el-tag v-else type="warning">自定义</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="默认模板">
            <el-tag v-if="currentTemplate.is_default" type="success">是</el-tag>
            <span v-else>否</span>
          </el-descriptions-item>
          <el-descriptions-item label="使用次数">
            {{ currentTemplate.usage_count }}
          </el-descriptions-item>
          <el-descriptions-item label="最后使用">
            {{ currentTemplate.last_used_at || '未使用' }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ currentTemplate.description || '无' }}
          </el-descriptions-item>
          <el-descriptions-item label="标签" :span="2">
            <el-tag
              v-for="tag in currentTemplate.tags"
              :key="tag"
              style="margin-right: 8px"
            >
              {{ tag }}
            </el-tag>
            <span v-if="!currentTemplate.tags || currentTemplate.tags.length === 0">无</span>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider>模板内容</el-divider>

        <el-tabs>
          <el-tab-pane label="系统提示词">
            <el-input
              :model-value="currentTemplate.content.system_prompt"
              type="textarea"
              :rows="10"
              readonly
            />
          </el-tab-pane>
          <el-tab-pane label="工具调用指导" v-if="currentTemplate.content.tool_guidance">
            <el-input
              :model-value="currentTemplate.content.tool_guidance"
              type="textarea"
              :rows="10"
              readonly
            />
          </el-tab-pane>
          <el-tab-pane label="分析要求" v-if="currentTemplate.content.analysis_requirements">
            <el-input
              :model-value="currentTemplate.content.analysis_requirements"
              type="textarea"
              :rows="10"
              readonly
            />
          </el-tab-pane>
          <el-tab-pane label="输出格式" v-if="currentTemplate.content.output_format">
            <el-input
              :model-value="currentTemplate.content.output_format"
              type="textarea"
              :rows="10"
              readonly
            />
          </el-tab-pane>
        </el-tabs>

        <el-divider>版本历史</el-divider>
        <el-button @click="loadVersions" :loading="versionsLoading">
          加载版本历史
        </el-button>
        <el-table v-if="versions.length > 0" :data="versions" style="margin-top: 16px">
          <el-table-column prop="version" label="版本" width="100" />
          <el-table-column prop="change_description" label="变更说明" />
          <el-table-column prop="created_at" label="创建时间" width="180" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button
                size="small"
                type="primary"
                @click="handleRestoreVersion(row.version)"
                :disabled="row.version === currentTemplate.version"
              >
                恢复
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button
          v-if="currentTemplate && !currentTemplate.is_system"
          type="primary"
          @click="editTemplate(currentTemplate!)"
        >
          编辑
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Download, Refresh } from '@element-plus/icons-vue'
import {
  getAgentTypes,
  getTemplates,
  getTemplate,
  createTemplate,
  updateTemplate,
  deleteTemplate,
  setUserTemplateConfig,
  getTemplateVersions,
  restoreVersion as restoreTemplateVersion,
  getDefaultTemplate,
  type PromptTemplate,
  type PromptTemplateCreate,
  type AgentTypes
} from '@/api/promptTemplate'
import {
  getAllTools,
  getAgentToolConfig,
  type ToolConfig
} from '@/api/toolConfig'
import { ElMessageBox } from 'element-plus'

const agentTypes = ref<AgentTypes>({
  analysts: [],
  researchers: [],
  trader: [],
  risk_management: [],
  managers: []
})

const activeAgentType = ref('analysts')
const selectedAgent = ref('')
const templates = ref<PromptTemplate[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const detailDialogVisible = ref(false)
const currentTemplate = ref<PromptTemplate | null>(null)
const versions = ref<any[]>([])
const versionsLoading = ref(false)
const importingDefault = ref(false)
const availableTools = ref<ToolConfig[]>([])
const selectedToolIds = ref<string[]>([])
const toolsLoading = ref(false)

const formData = ref<PromptTemplateCreate>({
  agent_type: '',
  agent_name: '',
  template_name: '',
  template_display_name: '',
  description: '',
  content: {
    system_prompt: '',
    tool_guidance: '',
    analysis_requirements: '',
    output_format: ''
  },
  tags: [],
  is_default: false
})

const currentTemplateId = ref<string>('')

onMounted(async () => {
  await loadAgentTypes()
})

async function loadAgentTypes() {
  try {
    agentTypes.value = await getAgentTypes()
  } catch (error: any) {
    ElMessage.error('加载智能体类型失败: ' + error.message)
  }
}

async function loadTemplates() {
  if (!selectedAgent.value) return

  loading.value = true
  try {
    const response = await getTemplates({
      agent_type: selectedAgent.value,
      is_active: true
    })
    // 处理响应格式
    if (Array.isArray(response)) {
      templates.value = response
    } else if (response && typeof response === 'object' && 'data' in response) {
      templates.value = response.data || []
    } else {
      templates.value = []
    }
  } catch (error: any) {
    console.error('加载模板失败:', error)
    ElMessage.error('加载模板失败: ' + (error.message || '未知错误'))
    templates.value = []
  } finally {
    loading.value = false
  }
}

async function showCreateDialog() {
  if (!selectedAgent.value) {
    ElMessage.warning('请先选择智能体类型')
    return
  }

  const agent = findAgent(selectedAgent.value)
  formData.value = {
    agent_type: selectedAgent.value,
    agent_name: agent?.name || '',
    template_name: '',
    template_display_name: '',
    description: '',
    content: {
      system_prompt: '',
      tool_guidance: '',
      analysis_requirements: '',
      output_format: ''
    },
    tags: [],
    is_default: false
  }
  isEdit.value = false
  dialogVisible.value = true
  
  // 加载可用工具
  await loadAvailableTools()
  
  // 加载用户工具配置
  await loadUserToolConfig()
  
  // 提示用户可以选择导入默认模板
  setTimeout(() => {
    ElMessage.info({
      message: '提示：您可以点击"导入默认模板"按钮，从系统默认模板导入内容',
      duration: 4000
    })
  }, 500)
}

async function importDefaultTemplate() {
  if (!formData.value.agent_type) {
    ElMessage.warning('请先选择智能体类型')
    return
  }

  importingDefault.value = true
  try {
    const defaultTemplate = await getDefaultTemplate(formData.value.agent_type)
    
    if (!defaultTemplate) {
      ElMessage.warning('未找到默认模板')
      return
    }

    // 填充表单数据，但保留用户已输入的内容（如果模板名称为空，则使用默认模板的名称）
    formData.value = {
      agent_type: formData.value.agent_type,
      agent_name: formData.value.agent_name || defaultTemplate.agent_name,
      template_name: formData.value.template_name || '', // 保持用户输入的模板名称
      template_display_name: formData.value.template_display_name || defaultTemplate.template_display_name + ' (副本)',
      description: formData.value.description || defaultTemplate.description || '',
      content: {
        system_prompt: defaultTemplate.content.system_prompt || '',
        tool_guidance: defaultTemplate.content.tool_guidance || '',
        analysis_requirements: defaultTemplate.content.analysis_requirements || '',
        output_format: defaultTemplate.content.output_format || ''
      },
      tags: formData.value.tags.length > 0 ? formData.value.tags : (defaultTemplate.tags || []),
      is_default: false // 导入的模板默认不设为默认模板
    }

    ElMessage.success('已导入默认模板，您可以在基础上进行修改')
  } catch (error: any) {
    console.error('导入默认模板失败:', error)
    ElMessage.error('导入默认模板失败: ' + (error.message || '未知错误'))
  } finally {
    importingDefault.value = false
  }
}

async function editTemplate(template: PromptTemplate) {
  currentTemplate.value = template
  formData.value = {
    agent_type: template.agent_type,
    agent_name: template.agent_name,
    template_name: template.template_name,
    template_display_name: template.template_display_name,
    description: template.description || '',
    content: {
      system_prompt: template.content.system_prompt,
      tool_guidance: template.content.tool_guidance || '',
      analysis_requirements: template.content.analysis_requirements || '',
      output_format: template.content.output_format || ''
    },
    tags: template.tags || [],
    is_default: template.is_default
  }
  currentTemplateId.value = template.id
  isEdit.value = true
  dialogVisible.value = true
  
  // 加载工具配置
  await loadAvailableTools()
  if (template.tool_configs) {
    selectedToolIds.value = template.tool_configs
  } else {
    await loadUserToolConfig()
  }
}

async function saveTemplate() {
  if (!formData.value.template_name || !formData.value.template_display_name) {
    ElMessage.warning('请填写模板名称和显示名称')
    return
  }

  if (!formData.value.content.system_prompt) {
    ElMessage.warning('请填写系统提示词')
    return
  }

  saving.value = true
  try {
    // 准备保存数据，包含工具配置
    const saveData = {
      ...formData.value,
      tool_configs: selectedToolIds.value.length > 0 ? selectedToolIds.value : undefined
    }
    
    // 保存模板
    if (isEdit.value) {
      const response = await updateTemplate(currentTemplateId.value, saveData)
      ElMessage.success('更新模板成功')
    } else {
      const response = await createTemplate(saveData)
      ElMessage.success('创建模板成功')
    }
    
    dialogVisible.value = false
    await loadTemplates()
  } catch (error: any) {
    console.error('保存模板失败:', error)
    ElMessage.error('保存失败: ' + (error.message || error.detail || '未知错误'))
  } finally {
    saving.value = false
  }
}

async function setAsDefault(template: PromptTemplate) {
  try {
    await updateTemplate(template.id, { is_default: true })
    ElMessage.success('设置默认模板成功')
    await loadTemplates()
  } catch (error: any) {
    console.error('设置默认模板失败:', error)
    ElMessage.error('设置失败: ' + (error.message || error.detail || '未知错误'))
  }
}

async function useTemplate(template: PromptTemplate) {
  try {
    await setUserTemplateConfig(template.agent_type, template.id)
    ElMessage.success('已设置为当前使用的模板')
    await loadTemplates()
  } catch (error: any) {
    console.error('设置模板失败:', error)
    ElMessage.error('设置失败: ' + (error.message || '未知错误'))
  }
}

async function viewTemplate(template: PromptTemplate) {
  try {
    // 确保ID是字符串格式
    let templateId: string
    if (template.id) {
      templateId = typeof template.id === 'string' ? template.id : String(template.id)
    } else if ((template as any)._id) {
      templateId = typeof (template as any)._id === 'string' ? (template as any)._id : String((template as any)._id)
    } else {
      ElMessage.error('模板ID不存在')
      return
    }
    
    console.log('查看模板，ID:', templateId, '类型:', typeof templateId)
    
    // 重新获取模板详情以确保数据最新
    const fullTemplate = await getTemplate(templateId)
    if (fullTemplate && typeof fullTemplate === 'object') {
      if ('data' in fullTemplate && fullTemplate.data) {
        currentTemplate.value = fullTemplate.data as PromptTemplate
      } else {
        currentTemplate.value = fullTemplate as PromptTemplate
      }
    } else {
      currentTemplate.value = template
    }
    detailDialogVisible.value = true
    versions.value = []
  } catch (error: any) {
    console.error('获取模板详情失败:', error)
    console.error('模板对象:', template)
    console.error('模板ID:', template.id, '类型:', typeof template.id)
    ElMessage.error('获取模板详情失败: ' + (error.message || error.detail || '未知错误'))
  }
}

async function loadVersions() {
  if (!currentTemplate.value) return

  versionsLoading.value = true
  try {
    const response = await getTemplateVersions(currentTemplate.value.id)
    if (Array.isArray(response)) {
      versions.value = response
    } else if (response && typeof response === 'object' && 'data' in response) {
      versions.value = response.data || []
    } else {
      versions.value = []
    }
  } catch (error: any) {
    console.error('加载版本历史失败:', error)
    ElMessage.error('加载版本历史失败: ' + (error.message || '未知错误'))
  } finally {
    versionsLoading.value = false
  }
}

async function handleRestoreVersion(version: number) {
  if (!currentTemplate.value) return

  try {
    await ElMessageBox.confirm(
      `确定要恢复版本 ${version} 吗？当前版本将被保存为历史版本。`,
      '确认恢复',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    )

    await restoreTemplateVersion(currentTemplate.value.id, version)
    ElMessage.success('版本恢复成功')
    await loadTemplates()
    if (currentTemplate.value) {
      await viewTemplate(currentTemplate.value)
      await loadVersions()
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('恢复版本失败:', error)
      ElMessage.error('恢复版本失败: ' + (error.message || '未知错误'))
    }
  }
}

async function handleDeleteTemplate(template: PromptTemplate) {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板 "${template.template_display_name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    )

    await deleteTemplate(template.id)
    ElMessage.success('删除成功')
    await loadTemplates()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除模板失败:', error)
      ElMessage.error('删除失败: ' + (error.message || '未知错误'))
    }
  }
}

function handleAgentTypeChange() {
  selectedAgent.value = ''
  templates.value = []
}

async function loadAvailableTools() {
  if (!formData.value.agent_type) return
  
  toolsLoading.value = true
  try {
    // 加载所有启用的工具
    const allTools = await getAllTools({ enabled: true })
    
    // 尝试加载智能体的工具配置，获取默认工具
    try {
      const agentConfig = await getAgentToolConfig(formData.value.agent_type)
      if (agentConfig && agentConfig.tool_configs) {
        // 只显示智能体配置的工具
        availableTools.value = allTools.filter(tool => 
          agentConfig.tool_configs.includes(tool.id || '')
        )
      } else {
        // 如果没有配置，显示所有工具
        availableTools.value = allTools
      }
    } catch {
      // 如果智能体配置不存在，显示所有工具
      availableTools.value = allTools
    }
  } catch (error: any) {
    console.error('加载工具列表失败:', error)
    ElMessage.error('加载工具列表失败: ' + (error.message || '未知错误'))
    availableTools.value = []
  } finally {
    toolsLoading.value = false
  }
}

async function loadUserToolConfig() {
  if (!formData.value.agent_type) return
  
  try {
    // 从模板中加载工具配置
    if (currentTemplate.value && currentTemplate.value.tool_configs) {
      selectedToolIds.value = currentTemplate.value.tool_configs
      if (selectedToolIds.value.length > 0) {
        generateToolGuidance()
      }
    } else {
      // 尝试加载智能体的默认工具配置
      try {
        const agentConfig = await getAgentToolConfig(formData.value.agent_type)
        if (agentConfig && agentConfig.default_tools) {
          selectedToolIds.value = agentConfig.default_tools
        } else {
          selectedToolIds.value = []
        }
      } catch {
        selectedToolIds.value = []
      }
    }
  } catch (error: any) {
    console.error('加载工具配置失败:', error)
    selectedToolIds.value = []
  }
}

function onToolsChange() {
  // 当工具选择发生变化时，自动生成工具调用指导
  if (selectedToolIds.value.length > 0) {
    generateToolGuidance()
  } else {
    // 如果清空了工具选择，清空工具调用指导
    formData.value.content.tool_guidance = ''
  }
}

function handleDialogClose() {
  formData.value = {
    agent_type: '',
    agent_name: '',
    template_name: '',
    template_display_name: '',
    description: '',
    content: {
      system_prompt: '',
      tool_guidance: '',
      analysis_requirements: '',
      output_format: ''
    },
    tags: [],
    is_default: false
  }
  currentTemplateId.value = ''
  isEdit.value = false
  selectedToolIds.value = []
  availableTools.value = []
}

function generateToolGuidance() {
  if (selectedToolIds.value.length === 0) {
    ElMessage.warning('请先选择工具')
    return
  }

  // 获取选中的工具信息
  const selectedTools = availableTools.value.filter(tool => 
    selectedToolIds.value.includes(tool.id || '')
  )

  if (selectedTools.length === 0) {
    ElMessage.warning('未找到选中的工具信息')
    return
  }

  // 按优先级排序（数字越小优先级越高）
  selectedTools.sort((a, b) => (a.priority || 100) - (b.priority || 100))

  // 生成工具调用指导文本
  let guidance = '## 工具调用指导\n\n'
  guidance += '您可以使用以下工具来获取数据和分析信息：\n\n'

  selectedTools.forEach((tool, index) => {
    guidance += `### ${index + 1}. ${tool.tool_display_name}\n\n`
    guidance += `**工具名称**: \`${tool.tool_name}\`\n\n`
    
    if (tool.description) {
      guidance += `**描述**: ${tool.description}\n\n`
    }

    // 根据工具名称生成示例参数
    let exampleParams = generateExampleParams(tool.tool_name, tool.parameters)
    
    guidance += `**调用示例**:\n`
    guidance += `\`\`\`\n`
    guidance += `🔴 立即调用 ${tool.tool_name} 工具\n`
    if (exampleParams) {
      guidance += `参数：${exampleParams}\n`
    }
    guidance += `\`\`\`\n\n`
  })

  guidance += '### 使用说明\n\n'
  guidance += '- 根据分析需求，选择合适的工具获取数据\n'
  guidance += '- 工具调用时，请确保参数格式正确\n'
  guidance += '- 可以连续调用多个工具来获取更全面的信息\n'
  guidance += '- 工具返回的数据可以直接用于分析和报告生成\n'

  formData.value.content.tool_guidance = guidance
  ElMessage.success('工具调用指导已生成')
}

function generateExampleParams(toolName: string, parameters?: any[]): string {
  // 根据工具名称生成示例参数
  if (toolName.includes('fundamentals')) {
    return "ticker='{ticker}', start_date='{start_date}', end_date='{current_date}', curr_date='{current_date}'"
  } else if (toolName.includes('market_data') || toolName.includes('YFin') || toolName.includes('market')) {
    return "ticker='{ticker}', start_date='{start_date}', end_date='{current_date}'"
  } else if (toolName.includes('news')) {
    return "ticker='{ticker}', curr_date='{current_date}'"
  } else if (toolName.includes('sentiment')) {
    return "ticker='{ticker}', curr_date='{current_date}'"
  } else if (toolName.includes('overview')) {
    return "curr_date='{current_date}'"
  } else if (parameters && Array.isArray(parameters) && parameters.length > 0) {
    // 如果有参数定义，使用参数定义生成
    const paramList: string[] = []
    for (const [key, value] of Object.entries(parameters)) {
      if (typeof value === 'object' && value !== null && 'type' in value) {
        const paramType = (value as any).type
        if (paramType === 'string') {
          paramList.push(`${key}='{${key}}'`)
        } else if (paramType === 'number' || paramType === 'integer') {
          paramList.push(`${key}={${key}}`)
        } else {
          paramList.push(`${key}='{${key}}'`)
        }
      } else {
        paramList.push(`${key}='{${key}}'`)
      }
    }
    return paramList.join(', ')
  }
  
  return "ticker='{ticker}'"
}

function findAgent(agentType: string) {
  const allAgents = [
    ...agentTypes.value.analysts,
    ...agentTypes.value.researchers,
    ...agentTypes.value.trader,
    ...agentTypes.value.risk_management,
    ...agentTypes.value.managers
  ]
  return allAgents.find(a => a.type === agentType)
}
</script>

<style scoped>
.prompt-template-config {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.template-list {
  margin-top: 20px;
}
</style>

