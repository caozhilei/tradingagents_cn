<template>
  <div class="custom-node" :class="nodeCategory">
    <div class="node-header">
      <span class="node-label">{{ node.label }}</span>
    </div>
    <div class="node-content">
      <el-icon><component :is="iconComponent" /></el-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Document, User, Setting, Wallet, Tools } from '@element-plus/icons-vue'
import type { FlowNode } from '@/stores/workflow'

interface Props {
  node: FlowNode
}

const props = defineProps<Props>()

const nodeCategory = computed(() => {
  const categoryMap: Record<string, string> = {
    analyst: 'analyst',
    researcher: 'researcher',
    manager: 'manager',
    trader: 'trader',
    risk_analyst: 'risk_analyst',
    tool_node: 'tool',
    message_clear: 'utility'
  }
  return categoryMap[props.node.type] || 'utility'
})

const iconComponent = computed(() => {
  const iconMap: Record<string, any> = {
    analyst: Document,
    researcher: User,
    manager: Setting,
    trader: Wallet,
    risk_analyst: Tools,
    tool_node: Tools,
    message_clear: Tools
  }
  return iconMap[props.node.type] || Tools
})
</script>

<style scoped>
.custom-node {
  padding: 10px;
  border-radius: 8px;
  min-width: 120px;
  cursor: pointer;
}

.node-header {
  font-weight: bold;
  margin-bottom: 8px;
  text-align: center;
}

.node-content {
  display: flex;
  justify-content: center;
  align-items: center;
}

.analyst {
  background: #e3f2fd;
  border: 2px solid #1976d2;
}

.researcher {
  background: #f3e5f5;
  border: 2px solid #7b1fa2;
}

.manager {
  background: #fff3e0;
  border: 2px solid #ef6c00;
}

.trader {
  background: #e8f5e9;
  border: 2px solid #388e3c;
}

.risk_analyst {
  background: #ffebee;
  border: 2px solid #c62828;
}

.tool {
  background: #f1f8e9;
  border: 2px solid #689f38;
}

.utility {
  background: #fafafa;
  border: 2px solid #424242;
}
</style>

