<template>
  <div class="node-palette">
    <el-card>
      <template #header>
        <div class="palette-header">
          <span>节点工具箱</span>
          <el-button
            text
            size="small"
            @click="loadAgentTypes"
            :loading="loading"
            title="刷新"
          >
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
      </template>
      
      <el-scrollbar height="600px">
        <el-loading v-if="loading" text="加载中..." />
        <div v-else class="node-categories">
          <!-- 分析师节点 -->
          <div v-if="analystNodes.length > 0" class="category">
            <div class="category-title">分析师</div>
            <div class="node-items">
              <div
                v-for="item in analystNodes"
                :key="`${item.type}-${item.agentType}`"
                class="node-item"
                draggable="true"
                @dragstart="handleDragStart($event, item)"
              >
                <el-icon><Document /></el-icon>
                <span>{{ item.label }}</span>
              </div>
            </div>
          </div>

          <!-- 研究员节点 -->
          <div v-if="researcherNodes.length > 0" class="category">
            <div class="category-title">研究员</div>
            <div class="node-items">
              <div
                v-for="item in researcherNodes"
                :key="`${item.type}-${item.agentType}`"
                class="node-item"
                draggable="true"
                @dragstart="handleDragStart($event, item)"
              >
                <el-icon><User /></el-icon>
                <span>{{ item.label }}</span>
              </div>
            </div>
          </div>

          <!-- 交易员节点 -->
          <div v-if="traderNodes.length > 0" class="category">
            <div class="category-title">交易员</div>
            <div class="node-items">
              <div
                v-for="item in traderNodes"
                :key="`${item.type}-${item.agentType}`"
                class="node-item"
                draggable="true"
                @dragstart="handleDragStart($event, item)"
              >
                <el-icon><Money /></el-icon>
                <span>{{ item.label }}</span>
              </div>
            </div>
          </div>

          <!-- 风险管理节点 -->
          <div v-if="riskManagementNodes.length > 0" class="category">
            <div class="category-title">风险管理</div>
            <div class="node-items">
              <div
                v-for="item in riskManagementNodes"
                :key="`${item.type}-${item.agentType}`"
                class="node-item"
                draggable="true"
                @dragstart="handleDragStart($event, item)"
              >
                <el-icon><Warning /></el-icon>
                <span>{{ item.label }}</span>
              </div>
            </div>
          </div>

          <!-- 管理层节点 -->
          <div v-if="managerNodes.length > 0" class="category">
            <div class="category-title">管理层</div>
            <div class="node-items">
              <div
                v-for="item in managerNodes"
                :key="`${item.type}-${item.agentType}`"
                class="node-item"
                draggable="true"
                @dragstart="handleDragStart($event, item)"
              >
                <el-icon><Setting /></el-icon>
                <span>{{ item.label }}</span>
              </div>
            </div>
          </div>

          <!-- 工具节点（固定） -->
          <div v-if="toolNodes.length > 0" class="category">
            <div class="category-title">工具</div>
            <div class="node-items">
              <div
                v-for="item in toolNodes"
                :key="item.type"
                class="node-item"
                draggable="true"
                @dragstart="handleDragStart($event, item)"
              >
                <el-icon><Grid /></el-icon>
                <span>{{ item.label }}</span>
              </div>
            </div>
          </div>
        </div>
      </el-scrollbar>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, User, Setting, Grid, Money, Warning, Refresh } from '@element-plus/icons-vue'
import { getAgentTypes, type AgentTypes, type AgentType } from '@/api/promptTemplate'

interface NodeItem {
  type: string
  label: string
  agentType: string // 智能体类型（来自API）
  config: Record<string, any>
}

interface Emits {
  (e: 'node-add', nodeType: string, position: { x: number; y: number }, config?: Record<string, any>): void
}

const emit = defineEmits<Emits>()

const loading = ref(false)
const agentTypes = ref<AgentTypes>({
  analysts: [],
  researchers: [],
  trader: [],
  risk_management: [],
  managers: []
})

// 将智能体类型映射到节点类型
function mapAgentTypeToNodeType(agentType: string, category: keyof AgentTypes): string {
  if (category === 'analysts') return 'analyst'
  if (category === 'researchers') return 'researcher'
  if (category === 'trader') return 'trader'
  if (category === 'risk_management') return 'risk_analyst'
  if (category === 'managers') return 'manager'
  return 'analyst' // 默认
}

// 根据智能体类型生成节点配置（统一使用 agent_type）
function generateNodeConfig(agentType: string, category: keyof AgentTypes): Record<string, any> {
  const config: Record<string, any> = {
    agent_type: agentType
  }
  
  // 分析师节点需要额外的配置
  if (category === 'analysts') {
    config.llm_type = 'quick_thinking'
    config.max_tool_calls = 3
  }
  
  return config
}

// 动态生成节点列表
const analystNodes = computed(() => {
  return agentTypes.value.analysts.map(agent => ({
    type: mapAgentTypeToNodeType(agent.type, 'analysts'),
    label: agent.name,
    agentType: agent.type,
    config: generateNodeConfig(agent.type, 'analysts')
  }))
})

const researcherNodes = computed(() => {
  return agentTypes.value.researchers.map(agent => ({
    type: mapAgentTypeToNodeType(agent.type, 'researchers'),
    label: agent.name,
    agentType: agent.type,
    config: generateNodeConfig(agent.type, 'researchers')
  }))
})

const traderNodes = computed(() => {
  return agentTypes.value.trader.map(agent => ({
    type: mapAgentTypeToNodeType(agent.type, 'trader'),
    label: agent.name,
    agentType: agent.type,
    config: generateNodeConfig(agent.type, 'trader')
  }))
})

const riskManagementNodes = computed(() => {
  return agentTypes.value.risk_management.map(agent => ({
    type: mapAgentTypeToNodeType(agent.type, 'risk_management'),
    label: agent.name,
    agentType: agent.type,
    config: generateNodeConfig(agent.type, 'risk_management')
  }))
})

const managerNodes = computed(() => {
  return agentTypes.value.managers.map(agent => ({
    type: mapAgentTypeToNodeType(agent.type, 'managers'),
    label: agent.name,
    agentType: agent.type,
    config: generateNodeConfig(agent.type, 'managers')
  }))
})

// 固定的工具节点
const toolNodes: NodeItem[] = [
  { 
    type: 'tool_node', 
    label: '工具节点',
    agentType: '',
    config: {}
  },
  { 
    type: 'message_clear', 
    label: '消息清理',
    agentType: '',
    config: {}
  }
]

async function loadAgentTypes() {
  loading.value = true
  try {
    agentTypes.value = await getAgentTypes()
  } catch (error: any) {
    console.error('加载智能体类型失败:', error)
    ElMessage.error('加载智能体类型失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

function handleDragStart(event: DragEvent, item: NodeItem) {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/node-type', item.type)
    event.dataTransfer.setData('application/node-config', JSON.stringify(item.config))
    event.dataTransfer.setData('application/agent-type', item.agentType || '')
    event.dataTransfer.effectAllowed = 'copy'
  }
}

onMounted(() => {
  loadAgentTypes()
})
</script>

<style scoped>
.node-palette {
  width: 100%;
  height: 100%;
}

.palette-header {
  font-weight: bold;
  font-size: 16px;
}

.node-categories {
  padding: 10px 0;
}

.category {
  margin-bottom: 20px;
}

.category-title {
  font-weight: bold;
  margin-bottom: 10px;
  color: #409eff;
  font-size: 14px;
}

.node-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.node-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: grab;
  transition: all 0.2s;
}

.node-item:hover {
  background: #ecf5ff;
  border-color: #409eff;
}

.node-item:active {
  cursor: grabbing;
}
</style>

