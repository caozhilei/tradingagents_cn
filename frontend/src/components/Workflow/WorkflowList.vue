<template>
  <div class="workflow-list" v-loading="loading" element-loading-text="加载中..." style="min-height: 200px;">
    <!-- 调试信息 - 始终显示在最顶部 -->
    <div style="padding: 10px; background: yellow; border: 2px solid red; margin-bottom: 10px;">
      <strong>⚠️ 组件已渲染！如果看不到这个黄色框，说明组件没有挂载！</strong>
    </div>
    <!-- 调试信息 - 始终显示在最顶部 -->
    <div style="margin-bottom: 10px; padding: 10px; background: #f5f5f5; border-radius: 4px; font-size: 12px; border: 1px solid #ddd;">
      <div><strong>🔍 调试信息：</strong></div>
      <div>工作流数量: <strong>{{ workflows.length }}</strong></div>
      <div>加载状态: <strong>{{ loading ? '加载中' : '已完成' }}</strong></div>
      <div>是否有数据: <strong :style="{ color: workflows.length > 0 ? 'green' : 'red' }">{{ workflows.length > 0 ? '是' : '否' }}</strong></div>
      <div>强制更新标记: <strong>{{ forceUpdate }}</strong></div>
      <div>workflows 是否为数组: <strong>{{ Array.isArray(workflows) ? '是' : '否' }}</strong></div>
      <div v-if="workflows.length > 0" style="margin-top: 8px; padding: 8px; background: white; border-radius: 4px;">
        <div><strong>第一个工作流详情：</strong></div>
        <pre style="font-size: 11px; overflow: auto; max-height: 200px;">{{ JSON.stringify(workflows[0], null, 2) }}</pre>
      </div>
      <div v-else style="margin-top: 8px; color: #999;">
        暂无工作流数据
      </div>
    </div>
    
    <el-table
      v-if="workflows.length > 0"
      :key="`table-${forceUpdate}`"
      :data="workflows"
      style="width: 100%"
      @row-click="handleRowClick"
      stripe
      highlight-current-row
    >
      <el-table-column prop="name" label="名称" min-width="150" />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column prop="author" label="作者" width="120" v-if="hasAuthor" />
      <el-table-column prop="updated_at" label="更新时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.updated_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button
            size="small"
            type="primary"
            @click.stop="handleSelect(row.id)"
          >
            选择
          </el-button>
          <el-button
            size="small"
            type="danger"
            @click.stop="handleDelete(row.id, row.name)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-else-if="!loading" description="暂无工作流模板" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { workflowApi } from '@/api/workflow'
import type { WorkflowListItem } from '@/types/workflow'
import { ElMessage, ElMessageBox } from 'element-plus'

interface Emits {
  (e: 'select', workflowId: string): void
  (e: 'delete', workflowId: string): void
}

const emit = defineEmits<Emits>()
const workflows = ref<WorkflowListItem[]>([])
const loading = ref(false)
const forceUpdate = ref(0) // 强制更新标记

// 检查是否有作者信息
const hasAuthor = computed(() => {
  return workflows.value.some(w => w.author)
})

// 格式化日期
function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}

async function loadWorkflows() {
  loading.value = true
  try {
    const result = await workflowApi.listWorkflows()
    console.log('🔍 [WorkflowList] API响应原始数据:', result)
    console.log('🔍 [WorkflowList] 响应类型:', typeof result, '是否为数组:', Array.isArray(result))
    console.log('🔍 [WorkflowList] 响应构造函数:', result?.constructor?.name)
    
    // 后端直接返回数组，而不是包装在 ApiResponse 中
    // 所以需要检查 result 是数组还是 ApiResponse
    let finalData: WorkflowListItem[] = []
    
    if (Array.isArray(result)) {
      finalData = result
      console.log('✅ [WorkflowList] 直接使用数组，工作流数量:', finalData.length)
    } else if (result && typeof result === 'object' && 'data' in result) {
      // 可能是包装在 ApiResponse 中
      if (Array.isArray(result.data)) {
        finalData = result.data
        console.log('✅ [WorkflowList] 从 result.data 获取数组，工作流数量:', finalData.length)
      } else {
        console.warn('⚠️ [WorkflowList] result.data 不是数组:', result.data)
      }
    } else {
      console.warn('⚠️ [WorkflowList] 响应格式异常:', result)
    }
    
    // 使用 Vue 的响应式更新
    workflows.value = finalData
    
    console.log('🔍 [WorkflowList] 设置后的 workflows.value:', workflows.value)
    console.log('🔍 [WorkflowList] workflows.value.length:', workflows.value.length)
    console.log('🔍 [WorkflowList] workflows.value 是否为数组:', Array.isArray(workflows.value))
    
    if (workflows.value.length === 0) {
      console.log('⚠️ [WorkflowList] 工作流列表为空')
    } else {
      console.log(`✅ [WorkflowList] 成功加载 ${workflows.value.length} 个工作流模板`)
      workflows.value.forEach((w, index) => {
        console.log(`  📋 工作流 ${index + 1}:`, {
          id: w.id,
          name: w.name,
          description: w.description,
          updated_at: w.updated_at
        })
      })
    }
    
    // 强制触发视图更新
    await nextTick()
    forceUpdate.value++
    console.log('🔄 [WorkflowList] 强制更新视图，forceUpdate:', forceUpdate.value)
    console.log('🔄 [WorkflowList] 当前 workflows.value:', workflows.value)
  } catch (error: any) {
    console.error('❌ [WorkflowList] 加载工作流列表失败:', error)
    ElMessage.error(error?.message || '加载工作流列表失败，请稍后重试')
    workflows.value = []
  } finally {
    loading.value = false
    console.log('✅ [WorkflowList] 加载完成，loading状态:', loading.value)
    console.log('✅ [WorkflowList] 最终 workflows.value.length:', workflows.value.length)
  }
}

onMounted(() => {
  console.log('🔍 [WorkflowList] ========== 组件已挂载 ==========')
  console.log('🔍 [WorkflowList] 当前 workflows.value:', workflows.value)
  console.log('🔍 [WorkflowList] 当前 workflows.value.length:', workflows.value.length)
  console.log('🔍 [WorkflowList] 开始调用 loadWorkflows()')
  loadWorkflows()
  console.log('🔍 [WorkflowList] loadWorkflows() 调用完成')
})

// 监听 workflows 变化，确保视图更新
watch(
  () => workflows.value,
  (newVal) => {
    console.log('workflows 数据变化:', newVal.length, '条记录')
    forceUpdate.value++
  },
  { deep: true }
)

// 监听 loading 变化
watch(
  () => loading.value,
  (newVal) => {
    console.log('loading 状态变化:', newVal)
  }
)

function handleRowClick(row: WorkflowListItem) {
  handleSelect(row.id)
}

function handleSelect(workflowId: string) {
  emit('select', workflowId)
}

async function handleDelete(workflowId: string, workflowName: string) {
  try {
    await ElMessageBox.confirm(
      `确定要删除工作流 "${workflowName}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    )
    
    await workflowApi.deleteWorkflow(workflowId)
    ElMessage.success('删除成功')
    emit('delete', workflowId)
    await loadWorkflows() // 刷新列表
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error?.message || '删除失败')
    }
  }
}

// 暴露刷新方法，供父组件调用
defineExpose({
  refresh: loadWorkflows
})
</script>

<style scoped>
.workflow-list {
  width: 100%;
  min-height: 300px;
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}

:deep(.el-button + .el-button) {
  margin-left: 8px;
}

:deep(.el-button--danger:hover) {
  background-color: #f56c6c;
  border-color: #f56c6c;
}
</style>

