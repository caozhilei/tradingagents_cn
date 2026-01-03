<template>
  <div class="agent-tool-config">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>智能体工具配置</h3>
        </div>
      </template>

      <!-- 智能体类型选择 -->
      <el-tabs v-model="activeAgentType" @tab-change="handleAgentTypeChange">
        <el-tab-pane label="分析师" name="analysts">
          <el-radio-group v-model="selectedAgent" @change="loadAgentConfig">
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
          <el-radio-group v-model="selectedAgent" @change="loadAgentConfig">
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
          <el-radio-group v-model="selectedAgent" @change="loadAgentConfig">
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
          <el-radio-group v-model="selectedAgent" @change="loadAgentConfig">
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
          <el-radio-group v-model="selectedAgent" @change="loadAgentConfig">
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

      <!-- 工具配置 -->
      <div v-if="selectedAgent" class="tool-config-section">
        <el-loading v-if="loading" text="加载中..." />

        <div v-else class="config-content">
          <div class="section-header">
            <h4>可用工具</h4>
            <el-button type="primary" size="small" @click="handleSave" :loading="saving">
              保存配置
            </el-button>
          </div>

          <!-- 工具选择器 -->
          <el-transfer
            v-model="selectedToolIds"
            :data="availableTools"
            :titles="['可用工具', '已选工具']"
            :props="{ key: 'id', label: 'tool_display_name' }"
            filterable
            filter-placeholder="搜索工具"
            style="margin-top: 20px"
          >
            <template #default="{ option }">
              <div class="tool-item">
                <span class="tool-name">{{ option.tool_display_name }}</span>
                <el-tag size="small" :type="getTypeTagType(option.tool_type)">
                  {{ getTypeLabel(option.tool_type) }}
                </el-tag>
              </div>
            </template>
          </el-transfer>

          <!-- 默认工具设置 -->
          <div class="default-tools-section" style="margin-top: 30px">
            <h4>默认工具</h4>
            <p class="section-desc">设置智能体的默认工具（优先级最高）</p>
            <el-checkbox-group v-model="defaultToolIds">
              <el-checkbox
                v-for="toolId in selectedToolIds"
                :key="toolId"
                :label="toolId"
              >
                {{ getToolName(toolId) }}
              </el-checkbox>
            </el-checkbox-group>
          </div>

          <!-- 工具优先级 -->
          <div class="priority-section" style="margin-top: 30px">
            <h4>工具优先级</h4>
            <p class="section-desc">数字越小优先级越高</p>
            <el-table :data="priorityTools" style="width: 100%">
              <el-table-column prop="tool_display_name" label="工具名称" />
              <el-table-column label="优先级" width="200">
                <template #default="{ row }">
                  <el-input-number
                    v-model="row.priority"
                    :min="1"
                    :max="1000"
                    size="small"
                    @change="updatePriority(row.id, row.priority)"
                  />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getAgentTypes } from '@/api/promptTemplate'
import {
  getAllTools,
  getAgentToolConfig,
  updateAgentToolConfig,
  createAgentToolConfig,
  type ToolConfig,
  type AgentToolConfig
} from '@/api/toolConfig'

// 数据
const loading = ref(false)
const saving = ref(false)
const activeAgentType = ref('analysts')
const selectedAgent = ref('')
const agentTypes = ref({
  analysts: [],
  researchers: [],
  trader: [],
  risk_management: [],
  managers: []
} as any)

const allTools = ref<ToolConfig[]>([])
const agentConfig = ref<AgentToolConfig | null>(null)
const selectedToolIds = ref<string[]>([])
const defaultToolIds = ref<string[]>([])

// 计算属性
const availableTools = computed(() => {
  return allTools.value.map((tool) => ({
    id: tool.id || '',
    tool_display_name: tool.tool_display_name,
    tool_type: tool.tool_type
  }))
})

const priorityTools = computed(() => {
  return selectedToolIds.value
    .map((toolId) => {
      const tool = allTools.value.find((t) => t.id === toolId)
      if (!tool) return null
      return {
        id: toolId,
        tool_display_name: tool.tool_display_name,
        priority: agentConfig.value?.tool_priorities?.[toolId] || 100
      }
    })
    .filter((t) => t !== null) as Array<{ id: string; tool_display_name: string; priority: number }>
})

// 方法
const loadAgentTypes = async () => {
  try {
    agentTypes.value = await getAgentTypes()
  } catch (error: any) {
    ElMessage.error(error.message || '加载智能体类型失败')
  }
}

const loadTools = async () => {
  try {
    allTools.value = await getAllTools({ enabled: true })
  } catch (error: any) {
    ElMessage.error(error.message || '加载工具列表失败')
  }
}

const loadAgentConfig = async () => {
  if (!selectedAgent.value) return

  loading.value = true
  try {
    try {
      agentConfig.value = await getAgentToolConfig(selectedAgent.value)
      selectedToolIds.value = [...(agentConfig.value.tool_configs || [])]
      defaultToolIds.value = [...(agentConfig.value.default_tools || [])]
    } catch (error: any) {
      // 如果配置不存在，创建新配置
      if (error.response?.status === 404) {
        agentConfig.value = null
        selectedToolIds.value = []
        defaultToolIds.value = []
      } else {
        throw error
      }
    }
  } catch (error: any) {
    ElMessage.error(error.message || '加载智能体工具配置失败')
  } finally {
    loading.value = false
  }
}

const handleAgentTypeChange = () => {
  selectedAgent.value = ''
  agentConfig.value = null
  selectedToolIds.value = []
  defaultToolIds.value = []
}

const handleSave = async () => {
  if (!selectedAgent.value) {
    ElMessage.warning('请先选择智能体')
    return
  }

  saving.value = true
  try {
    const priorities: Record<string, number> = {}
    priorityTools.value.forEach((tool) => {
      priorities[tool.id] = tool.priority
    })

    const configData = {
      tool_configs: selectedToolIds.value,
      default_tools: defaultToolIds.value,
      tool_priorities: priorities
    }

    if (agentConfig.value?.id) {
      await updateAgentToolConfig(selectedAgent.value, configData)
      ElMessage.success('工具配置已更新')
    } else {
      await createAgentToolConfig({
        agent_type: selectedAgent.value,
        ...configData
      })
      ElMessage.success('工具配置已创建')
    }

    await loadAgentConfig()
  } catch (error: any) {
    ElMessage.error(error.message || '保存配置失败')
  } finally {
    saving.value = false
  }
}

const updatePriority = (toolId: string, priority: number) => {
  // 优先级更新会实时反映在数据中
}

const getToolName = (toolId: string) => {
  const tool = allTools.value.find((t) => t.id === toolId)
  return tool?.tool_display_name || toolId
}

const getTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    unified: '统一',
    online: '在线',
    offline: '离线'
  }
  return map[type] || type
}

const getTypeTagType = (type: string) => {
  const map: Record<string, string> = {
    unified: 'success',
    online: 'primary',
    offline: 'info'
  }
  return map[type] || ''
}

// 生命周期
onMounted(async () => {
  await loadAgentTypes()
  await loadTools()
})
</script>

<style lang="scss" scoped>
.agent-tool-config {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h3 {
      margin: 0;
    }
  }

  .tool-config-section {
    margin-top: 20px;
    min-height: 400px;
  }

  .config-content {
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;

      h4 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
      }
    }

    .section-desc {
      color: var(--el-text-color-secondary);
      font-size: 14px;
      margin: 5px 0 15px 0;
    }

    .tool-item {
      display: flex;
      align-items: center;
      gap: 10px;

      .tool-name {
        flex: 1;
      }
    }
  }
}
</style>
