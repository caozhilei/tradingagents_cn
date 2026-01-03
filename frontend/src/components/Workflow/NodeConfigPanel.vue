<template>
  <div class="node-config-panel">
    <el-card v-loading="loading">
      <template #header>
        <div class="panel-header">
          <span>节点配置</span>
          <el-button text type="danger" @click="$emit('close')">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </template>

      <el-form :model="formData" label-width="120px" @submit.prevent>
        <!-- 基础信息 -->
        <el-form-item label="节点名称">
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="节点类型">
          <el-input v-model="formData.type" disabled />
        </el-form-item>

        <!-- 智能体类型选择 -->
        <el-form-item v-if="showAgentTypeSelector" label="智能体类型">
          <el-select 
            v-model="formData.config.agent_type" 
            @change="handleAgentTypeChange" 
            style="width: 100%"
          >
            <el-option
              v-for="opt in agentTypeOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>

        <!-- 提示词模板选择 -->
        <template v-if="showAgentTypeSelector && formData.config.agent_type">
          <el-form-item label="提示词模板">
            <el-select
              v-model="formData.config.template_id"
              filterable
              placeholder="请选择提示词模板"
              :loading="templatesLoading"
              style="width: 100%"
              @change="handleTemplateChange"
              @update:modelValue="handleTemplateChange"
            >
              <el-option
                v-for="template in templateOptions"
                :key="template.id"
                :label="template.cleanName"
                :value="template.id"
              />
            </el-select>
            <div class="form-tip">
              💡 提示：{{ getTemplateTip }}
            </div>
          </el-form-item>
        </template>

        <!-- 工具配置 -->
        <template v-if="showAgentTypeSelector && formData.config.agent_type">
          <el-form-item label="工具配置">
            <el-radio-group v-model="toolConfigMode" @change="handleToolModeChange">
              <el-radio label="default">使用默认配置</el-radio>
              <el-radio label="override">覆盖配置</el-radio>
            </el-radio-group>
            
            <!-- 默认工具展示 -->
            <div v-if="toolConfigMode === 'default'" class="default-tools-preview">
              <div class="label">默认工具列表：</div>
              <div v-if="defaultToolNames.length > 0" class="tool-tags">
                <el-tag v-for="name in defaultToolNames" :key="name" size="small">{{ name }}</el-tag>
              </div>
              <div v-else class="empty-text">暂无默认工具</div>
            </div>

            <!-- 自定义工具选择 -->
            <div v-if="toolConfigMode === 'override'" class="override-tools-select">
              <el-select
                v-model="overrideToolIds"
                multiple
                filterable
                placeholder="请选择工具"
                style="width: 100%"
              >
                <el-option
                  v-for="tool in toolOptions"
                  :key="tool.id"
                  :label="tool.displayName"
                  :value="tool.id"
                >
                  <div class="tool-option">
                    <span>{{ tool.displayName }}</span>
                    <el-tag :type="tool.tagType" size="small">{{ tool.typeLabel }}</el-tag>
                  </div>
                </el-option>
              </el-select>
            </div>
          </el-form-item>
        </template>

        <!-- 开始节点：用户输入要求 -->
        <template v-if="isStartNode">
          <el-divider />
          <el-form-item label="输入要求说明">
            <el-input
              v-model="startInputDescription"
              type="textarea"
              :rows="3"
              placeholder="向用户说明需要提供哪些信息及格式"
            />
          </el-form-item>
          <el-form-item label="必填输入字段">
            <el-select
              v-model="startInputFields"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="添加或选择需要用户填写的字段"
              style="width: 100%"
            >
              <el-option v-for="f in commonInputFields" :key="f" :label="f" :value="f" />
            </el-select>
          </el-form-item>
        </template>

        <!-- 结束节点：输出内容与格式 -->
        <template v-if="isEndNode">
          <el-divider />
          <el-form-item label="输出内容字段">
            <el-select
              v-model="endOutputFields"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="选择或添加最终输出字段"
              style="width: 100%"
            >
              <el-option v-for="f in commonOutputFields" :key="f" :label="f" :value="f" />
            </el-select>
          </el-form-item>
          <el-form-item label="输出格式">
            <el-input
              v-model="endOutputFormat"
              type="textarea"
              :rows="4"
              placeholder="定义最终输出的格式说明（如Markdown结构、JSON模板等）"
            />
          </el-form-item>
        </template>

        <!-- 输入输出字段 -->
        <template v-if="showAgentTypeSelector">
          <el-divider />
          <el-form-item label="输入字段">
            <el-select
              v-model="formData.config.inputs"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="定义输入字段"
              style="width: 100%"
            >
              <el-option v-for="f in commonInputFields" :key="f" :label="f" :value="f" />
            </el-select>
          </el-form-item>
          <el-form-item label="输出字段">
            <el-select
              v-model="formData.config.outputs"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="定义输出字段"
              style="width: 100%"
            >
              <el-option v-for="f in commonOutputFields" :key="f" :label="f" :value="f" />
            </el-select>
          </el-form-item>
        </template>

        <!-- 工具节点专用配置 -->
        <template v-if="formData.type === 'tool_node'">
          <el-form-item label="选择工具">
            <el-select
              v-model="formData.config.tool_configs"
              multiple
              filterable
              placeholder="请选择工具"
              style="width: 100%"
            >
              <el-option
                v-for="tool in toolOptions"
                :key="tool.id"
                :label="tool.displayName"
                :value="tool.id"
              />
            </el-select>
          </el-form-item>
        </template>

        <el-form-item>
          <el-button type="primary" @click="handleSave">保存配置</el-button>
          <el-button @click="$emit('close')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Close } from '@element-plus/icons-vue'
import type { FlowNode } from '@/stores/workflow'
import { getAllTools, getAgentToolConfig, type ToolConfig, type AgentToolConfig } from '@/api/toolConfig'
import { getTemplates, getDefaultTemplate, type PromptTemplate } from '@/api/promptTemplate'
import { useWorkflowStore } from '@/stores/workflow'
import { workflowApi } from '@/api/workflow'

// --- Interfaces ---
interface Props {
  node: FlowNode
}

interface TemplateOption {
  id: string
  cleanName: string
  displayName: string
  isDefault: boolean
  isSystem: boolean
  version: number
  raw: PromptTemplate
}

interface ToolOption {
  id: string
  displayName: string
  type: string
  typeLabel: string
  tagType: string
  raw: ToolConfig
}

// --- Props & Emits ---
const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update', nodeId: string, config: any): void
  (e: 'close'): void
}>()

// --- State ---
const loading = ref(false)
const templatesLoading = ref(false)

// Form Data (Single Source of Truth)
const formData = ref({
  name: '',
  type: '',
  config: {
    agent_type: '',
    template_id: '', // Always string
    inputs: [] as string[],
    outputs: [] as string[],
    tool_configs: [] as string[], // For tool nodes or explicit list
    config_overrides: {} as any,
    agent_config_ref: {} as any,
    // Redundant fields for display/export
    template_name: '',
    template_display_name: '',
    template_version: 0
  }
})

// UI Helper State
const toolConfigMode = ref<'default' | 'override'>('default')
const overrideToolIds = ref<string[]>([])
const defaultTemplateId = ref<string>('')

// Data Sources
const templateOptions = ref<TemplateOption[]>([])
const toolOptions = ref<ToolOption[]>([])
const currentAgentToolConfig = ref<AgentToolConfig | null>(null)

// --- Constants ---
const commonInputFields = [
  'company_of_interest', 'trade_date', 'market_report', 'sentiment_report',
  'news_report', 'fundamentals_report', 'investment_plan', 'trader_investment_plan',
  'risk_debate_state', 'messages'
]
const commonOutputFields = [
  'market_report', 'sentiment_report', 'news_report', 'fundamentals_report',
  'investment_plan', 'trader_investment_plan', 'final_trade_decision',
  'risk_debate_state', 'investment_debate_state', 'messages'
]

// --- Computed ---
const showAgentTypeSelector = computed(() => {
  return ['analyst', 'researcher', 'manager', 'risk_analyst', 'trader'].includes(formData.value.type)
})

const agentTypeOptions = computed(() => {
  const type = formData.value.type
  if (type === 'analyst') return [
    { label: '市场分析师', value: 'market_analyst' },
    { label: '基本面分析师', value: 'fundamentals_analyst' },
    { label: '新闻分析师', value: 'news_analyst' },
    { label: '社交媒体分析师', value: 'social_media_analyst' }
  ]
  if (type === 'researcher') return [
    { label: '看涨研究员', value: 'bull_researcher' },
    { label: '看跌研究员', value: 'bear_researcher' }
  ]
  if (type === 'manager') return [
    { label: '研究经理', value: 'research_manager' },
    { label: '风险经理', value: 'risk_manager' }
  ]
  if (type === 'risk_analyst') return [
    { label: '激进辩论者', value: 'aggressive_debator' },
    { label: '保守辩论者', value: 'conservative_debator' },
    { label: '中性辩论者', value: 'neutral_debator' }
  ]
  if (type === 'trader') return [
    { label: '交易员', value: 'trader' }
  ]
  return []
})

const getTemplateTip = computed(() => {
  const currentId = formData.value.config.template_id
  if (!currentId) return '未选择模板'
  if (currentId === defaultTemplateId.value) return '当前使用默认模板'
  return '已选择自定义模板'
})

const defaultToolNames = computed(() => {
  if (!currentAgentToolConfig.value?.tool_configs) return []
  return currentAgentToolConfig.value.tool_configs
    .map(id => toolOptions.value.find(t => t.id === String(id))?.displayName || String(id))
})

// --- Core Logic ---

// Workflow store & 开始节点输入要求
const store = useWorkflowStore()
const isStartNode = computed(() => formData.value.type === 'start')
const startInputFields = ref<string[]>([])
const startInputDescription = ref<string>('')

// 结束节点设置
const isEndNode = computed(() => formData.value.type === 'end')
const endOutputFields = ref<string[]>([])
const endOutputFormat = ref<string>('')

// 1. Normalize ID to String
function normalizeId(id: any): string {
  if (id === null || id === undefined) return ''
  return String(id).trim()
}

function extractId(obj: any): string {
  if (!obj) return ''
  const cand = (obj._id ?? obj.id ?? obj)
  return normalizeId(cand)
}

// 2. Initialize Data & Form
async function initData() {
  loading.value = true
  try {
    // Basic Form Init
    formData.value.name = props.node.label
    formData.value.type = props.node.type
    // Deep copy config to avoid mutation references
    const nodeData = JSON.parse(JSON.stringify(props.node.data || {}))
    
    // Normalize Agent Type
    if (showAgentTypeSelector.value) {
      nodeData.agent_type = normalizeAgentType(nodeData)
    }
    
    // Assign to form
    formData.value.config = {
      ...formData.value.config,
      ...nodeData,
      // Ensure template_id is string
      template_id: normalizeId(nodeData.template_id)
    }

    // 初始化开始节点的输入要求
    if (isStartNode.value) {
      const p: any = store.workflowParameters || {}
      const u: any = p.user_input || {}
      startInputFields.value = Array.isArray(u.required_fields) ? u.required_fields.slice() : []
      startInputDescription.value = typeof u.description === 'string' ? u.description : ''
    }

    // 初始化结束节点的输出设置
    if (isEndNode.value) {
      const p: any = store.workflowParameters || {}
      const fo: any = p.final_output || {}
      endOutputFields.value = Array.isArray(fo.fields) ? fo.fields.slice() : []
      endOutputFormat.value = typeof fo.format === 'string' ? fo.format : ''
    }

    // Load Dependencies
    await loadAllTools() // Always load tools
    if (showAgentTypeSelector.value && formData.value.config.agent_type) {
      await Promise.all([
        loadTemplates(formData.value.config.agent_type),
        loadAgentConfig(formData.value.config.agent_type)
      ])
    }

    // Apply WYSIWYG Logic
    applySelectionLogic()

  } catch (e) {
    console.error('Init failed', e)
    ElMessage.error('初始化配置失败')
  } finally {
    loading.value = false
  }
}

// 3. Load Templates & Process
async function loadTemplates(type: string) {
  templatesLoading.value = true
  try {
    const list = await getTemplates({ agent_type: type }) || []
    const defTemplate = await getDefaultTemplate(type)
    
    defaultTemplateId.value = extractId(defTemplate)

    // Transform to Options
    templateOptions.value = list.map(t => {
      const id = extractId(t)
      const name = t.template_display_name || t.template_name || '未命名'
      const isDefault = id === defaultTemplateId.value // Only check ID match for default status
      
      return {
        id,
        cleanName: name,
        displayName: isDefault ? `${name} (默认)` : name,
        isDefault,
        isSystem: !!t.is_system,
        version: t.version || 1,
        raw: t
      }
    })

    console.log('[Templates] agent=', type, 'count=', templateOptions.value.length, 'defaultId=', defaultTemplateId.value)
  } catch (e) {
    console.error(e)
  } finally {
    templatesLoading.value = false
  }
}

// 4. Load Tools & Agent Config
async function loadAllTools() {
  const tools = await getAllTools({ enabled: true }) || []
  toolOptions.value = tools.map(t => ({
    id: normalizeId(t.id),
    displayName: t.tool_display_name || t.tool_name,
    type: t.tool_type,
    typeLabel: { unified: '统一', online: '在线', offline: '离线' }[t.tool_type] || t.tool_type,
    tagType: { unified: 'success', online: 'primary', offline: 'info' }[t.tool_type] || '',
    raw: t
  }))
}

async function loadAgentConfig(type: string) {
  try {
    currentAgentToolConfig.value = await getAgentToolConfig(type)
  } catch {
    currentAgentToolConfig.value = null
  }
}

// 5. Apply Selection Logic (WYSIWYG)
function applySelectionLogic() {
  const config = formData.value.config
  
  // A. Template Selection
  if (showAgentTypeSelector.value) {
    let targetId = config.template_id
    
    // If empty, try to get from ref
    if (!targetId && config.agent_config_ref?.template_id) {
      targetId = normalizeId(config.agent_config_ref.template_id)
    }

    // Validate existence
    const exists = templateOptions.value.some(t => t.id === targetId)
    
    if (exists) {
      config.template_id = targetId
    } else {
      // If invalid or empty, use default
      if (defaultTemplateId.value) {
        config.template_id = defaultTemplateId.value
      } else {
        // Fallback: pick first available option to ensure visible selection
        config.template_id = templateOptions.value[0]?.id || ''
      }
    }

    console.log('[ApplySelection] targetId=', targetId, 'exists=', exists, 'finalId=', config.template_id, 'options=', templateOptions.value.map(t => t.id))
  }

  // B. Tool Configuration
  if (config.config_overrides?.tool_overrides) {
    toolConfigMode.value = 'override'
    overrideToolIds.value = config.config_overrides.tool_overrides.map(normalizeId)
  } else {
    toolConfigMode.value = 'default'
    overrideToolIds.value = []
  }

  // C. Tool Node
  if (formData.value.type === 'tool_node') {
    if (Array.isArray(config.tool_configs)) {
      config.tool_configs = config.tool_configs.map(normalizeId)
    }
  }
}

// Helper: Normalize Agent Type (Legacy Support)
function normalizeAgentType(data: any): string {
  if (data.agent_type) return data.agent_type
  // Mappings for old data
  if (data.analyst_type) return data.analyst_type
  if (data.researcher_type) return { bull: 'bull_researcher', bear: 'bear_researcher' }[data.researcher_type as string] || data.researcher_type
  if (data.manager_type) return { research: 'research_manager', risk: 'risk_manager' }[data.manager_type as string] || data.manager_type
  if (data.risk_type) return { risky: 'aggressive_debator', safe: 'conservative_debator', neutral: 'neutral_debator' }[data.risk_type as string] || data.risk_type
  if (props.node.type === 'trader') return 'trader'
  return ''
}

// --- Event Handlers ---

async function handleAgentTypeChange() {
  const type = formData.value.config.agent_type
  if (!type) return
  
  await Promise.all([
    loadTemplates(type),
    loadAgentConfig(type)
  ])
  
  // Auto-select default on type change
  if (defaultTemplateId.value) {
    formData.value.config.template_id = defaultTemplateId.value
  } else {
    formData.value.config.template_id = ''
  }
  
  // Reset tools
  toolConfigMode.value = 'default'
  overrideToolIds.value = []
}

function handleToolModeChange() {
  if (toolConfigMode.value === 'override' && currentAgentToolConfig.value?.tool_configs) {
    // Pre-fill with defaults for easier editing
    overrideToolIds.value = currentAgentToolConfig.value.tool_configs.map(normalizeId)
  }
}

function handleTemplateChange(newId: string) {
  const selected = templateOptions.value.find(t => t.id === newId)
  console.log('[TemplateChange] id=', newId, 'selected=', selected)
  formData.value.config.template_id = newId
  if (selected) {
    formData.value.config.template_name = selected.raw.template_name
    formData.value.config.template_display_name = selected.raw.template_display_name
    formData.value.config.template_version = selected.version
    if (!formData.value.config.agent_config_ref) formData.value.config.agent_config_ref = {}
    formData.value.config.agent_config_ref.template_id = newId
  }
}

function handleSave() {
  const config = { ...formData.value.config }
  
  // 1. Prepare Template Data
  if (showAgentTypeSelector.value) {
    const selectedId = config.template_id
    const selectedOpt = templateOptions.value.find(t => t.id === selectedId)
    
    if (selectedOpt) {
      // Save ID
      config.template_id = selectedId
      // Save Metadata
      config.template_name = selectedOpt.raw.template_name
      config.template_display_name = selectedOpt.raw.template_display_name
      config.template_version = selectedOpt.version
      
      // Update Ref
      if (!config.agent_config_ref) config.agent_config_ref = {}
      config.agent_config_ref.template_id = selectedId
    } else {
      // Should not happen if logic is correct, but safe fallback
      delete config.template_id
      delete config.template_name
      delete config.template_display_name
      delete config.template_version
    }

    // 2. Prepare Tools
    if (toolConfigMode.value === 'override') {
      if (!config.config_overrides) config.config_overrides = {}
      config.config_overrides.tool_overrides = overrideToolIds.value
    } else {
      if (config.config_overrides) delete config.config_overrides.tool_overrides
    }
  }

  // 3. Clean Legacy Fields
  delete config.analyst_type
  delete config.researcher_type
  delete config.manager_type
  delete config.risk_type

  emit('update', props.node.id, {
    name: formData.value.name,
    ...config
  })
  ElMessage.success('配置已保存')

  // 持久化开始节点输入要求到工作流参数
  if (isStartNode.value) {
    const wp: any = { ...(store.workflowParameters || {}) }
    wp.user_input = {
      required_fields: startInputFields.value,
      description: startInputDescription.value
    }
    store.workflowParameters = wp
  }

  // 持久化结束节点输出设置到工作流参数
  if (isEndNode.value) {
    const wp: any = { ...(store.workflowParameters || {}) }
    wp.final_output = {
      fields: endOutputFields.value,
      format: endOutputFormat.value
    }
    store.workflowParameters = wp
  }

  // 🔄 自动持久化到服务器（如果当前工作流已加载）
  try {
    const store = useWorkflowStore()
    if (store.workflowId) {
      const current = store.exportConfig()
      workflowApi.updateWorkflow(store.workflowId, {
        name: store.workflowName,
        description: store.workflowDescription,
        config: current
      }).then(() => {
        ElMessage.success('已同步到服务器')
      }).catch(() => {
        ElMessage.warning('本地已保存，服务器同步失败，请稍后在顶部“保存”重试')
      })
    } else {
      ElMessage.info('本地配置已更新，如需持久化请点击顶部“保存”')
    }
  } catch {}
}

// --- Watchers ---
watch(() => props.node.id, initData, { immediate: true })

// 监听模板ID变化，确保无论事件来源都能同步元数据与日志
watch(() => formData.value.config.template_id, (newId, oldId) => {
  if (newId !== oldId) {
    console.log('[Watch template_id] new=', newId, 'old=', oldId)
    if (newId) handleTemplateChange(newId)
  }
})

</script>

<style scoped>
.node-config-panel {
  height: 100%;
  overflow-y: auto;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
.template-option, .tool-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.tags {
  display: flex;
  gap: 4px;
}
.form-tip {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}
.default-tools-preview {
  margin-top: 10px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}
.tool-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}
.empty-text {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
}
.override-tools-select {
  margin-top: 10px;
}
</style>
