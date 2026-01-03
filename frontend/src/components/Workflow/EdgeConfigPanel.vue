<template>
  <div class="edge-config-panel">
    <el-card>
      <template #header>
        <div class="panel-header">
          <span>边配置</span>
          <el-button
            text
            type="danger"
            @click="$emit('close')"
          >
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </template>

      <el-form
        :model="formData"
        label-width="100px"
      >
        <el-form-item label="源节点">
          <el-input v-model="formData.source" disabled />
        </el-form-item>

        <el-form-item label="目标节点">
          <el-input v-model="formData.target" disabled />
        </el-form-item>

        <el-form-item label="边类型">
          <el-select v-model="formData.type">
            <el-option label="直接边" value="direct" />
            <el-option label="条件边" value="conditional" />
            <el-option label="循环边" value="loop" />
          </el-select>
        </el-form-item>

        <template v-if="formData.type === 'conditional'">
          <el-divider content-position="left">条件配置</el-divider>
          <el-form-item label="条件函数">
            <el-input 
              v-model="formData.function" 
              placeholder="例如: should_continue_market_analyst"
            />
            <div class="form-tip">控制路由逻辑的函数名称</div>
          </el-form-item>
          
          <el-form-item label="条件结果">
            <el-input 
              v-model="formData.conditionResult" 
              placeholder="例如: tools_market"
            />
            <div class="form-tip">函数返回此值时走这条边</div>
          </el-form-item>
        </template>

        <el-form-item>
          <el-button type="primary" @click="handleSave">保存</el-button>
          <el-button @click="$emit('close')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Close } from '@element-plus/icons-vue'
import type { FlowEdge } from '@/stores/workflow'

interface Props {
  edge: FlowEdge
}

interface Emits {
  (e: 'update', edgeId: string, config: Record<string, any>): void
  (e: 'close'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 从 edge.data 中提取初始值
const getInitialData = (edge: FlowEdge) => {
  const data = edge.data || {}
  // 尝试从 mapping 中找到对应当前 target 的 key
  let conditionResult = ''
  if (data.mapping) {
    // 找到值为 target 的 key
    const entry = Object.entries(data.mapping).find(([_, target]) => target === edge.target)
    if (entry) {
      conditionResult = entry[0]
    }
  }
  // 如果没有 mapping 但有 conditionResult (旧数据或临时数据)，则使用它
  if (!conditionResult && data.conditionResult) {
    conditionResult = data.conditionResult
  }

  return {
    source: edge.source,
    target: edge.target,
    type: edge.type === 'step' ? 'conditional' : 'direct',
    function: data.function || '',
    conditionResult: conditionResult
  }
}

const formData = ref(getInitialData(props.edge))

watch(() => props.edge, (newEdge) => {
  formData.value = getInitialData(newEdge)
}, { deep: true })

function handleSave() {
  const config: Record<string, any> = {
    type: formData.value.type
  }

  if (formData.value.type === 'conditional') {
    // 构建 mapping: { [conditionResult]: target }
    const mapping: Record<string, string> = {}
    if (formData.value.conditionResult) {
      mapping[formData.value.conditionResult] = props.edge.target
    }
    
    config.function = formData.value.function
    config.mapping = mapping
    // 同时保存 conditionResult 方便前端回显
    config.conditionResult = formData.value.conditionResult
  }

  emit('update', props.edge.id, config)
}
</script>

<style scoped>
.edge-config-panel {
  width: 100%;
  height: 100%;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.2;
  margin-top: 4px;
}
</style>

