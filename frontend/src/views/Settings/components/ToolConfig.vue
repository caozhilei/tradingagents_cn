<template>
  <div class="tool-config">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>工具配置管理</h3>
          <div>
            <el-button type="primary" @click="handleInitialize">
              <el-icon><Refresh /></el-icon>
              初始化工具
            </el-button>
            <el-button type="success" @click="showCreateDialog">
              <el-icon><Plus /></el-icon>
              创建工具
            </el-button>
          </div>
        </div>
      </template>

      <!-- 筛选器 -->
      <div class="filters">
        <el-select
          v-model="filters.category"
          placeholder="工具分类"
          clearable
          style="width: 150px; margin-right: 10px"
          @change="loadTools"
        >
          <el-option label="市场数据" value="market_data" />
          <el-option label="基本面" value="fundamentals" />
          <el-option label="新闻" value="news" />
          <el-option label="情绪" value="sentiment" />
          <el-option label="其他" value="other" />
        </el-select>

        <el-select
          v-model="filters.tool_type"
          placeholder="工具类型"
          clearable
          style="width: 150px; margin-right: 10px"
          @change="loadTools"
        >
          <el-option label="统一工具" value="unified" />
          <el-option label="在线工具" value="online" />
          <el-option label="离线工具" value="offline" />
        </el-select>

        <el-select
          v-model="filters.enabled"
          placeholder="启用状态"
          clearable
          style="width: 120px; margin-right: 10px"
          @change="loadTools"
        >
          <el-option label="已启用" :value="true" />
          <el-option label="已禁用" :value="false" />
        </el-select>

        <el-input
          v-model="searchKeyword"
          placeholder="搜索工具名称"
          clearable
          style="width: 200px"
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <!-- 工具列表 -->
      <el-table
        v-loading="loading"
        :data="filteredTools"
        style="width: 100%; margin-top: 20px"
      >
        <el-table-column prop="tool_display_name" label="工具名称" width="200" />
        <el-table-column prop="tool_name" label="函数名" width="250" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="100">
          <template #default="{ row }">
            <el-tag :type="getCategoryTagType(row.category)">
              {{ getCategoryLabel(row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="tool_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.tool_type)">
              {{ getTypeLabel(row.tool_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="supported_markets" label="支持市场" width="150">
          <template #default="{ row }">
            <el-tag
              v-for="market in row.supported_markets"
              :key="market"
              size="small"
              style="margin-right: 5px"
            >
              {{ market }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="80" align="center" />
        <el-table-column prop="enabled" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.enabled"
              @change="handleToggleEnabled(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="usage_count" label="使用次数" width="100" align="center" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewTool(row)">查看</el-button>
            <el-button size="small" type="primary" @click="editTool(row)">编辑</el-button>
            <el-button
              v-if="!row.is_system"
              size="small"
              type="danger"
              @click="deleteTool(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 工具详情/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="800px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="120px"
      >
        <el-form-item label="工具函数名" prop="tool_name">
          <el-input
            v-model="formData.tool_name"
            :disabled="isEdit"
            placeholder="如: get_stock_market_data_unified"
          />
        </el-form-item>

        <el-form-item label="显示名称" prop="tool_display_name">
          <el-input v-model="formData.tool_display_name" placeholder="工具显示名称" />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="4"
            placeholder="工具描述"
          />
        </el-form-item>

        <el-form-item label="分类" prop="category">
          <el-select v-model="formData.category" placeholder="选择分类">
            <el-option label="市场数据" value="market_data" />
            <el-option label="基本面" value="fundamentals" />
            <el-option label="新闻" value="news" />
            <el-option label="情绪" value="sentiment" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>

        <el-form-item label="工具类型" prop="tool_type">
          <el-select v-model="formData.tool_type" placeholder="选择类型">
            <el-option label="统一工具" value="unified" />
            <el-option label="在线工具" value="online" />
            <el-option label="离线工具" value="offline" />
          </el-select>
        </el-form-item>

        <el-form-item label="支持市场">
          <el-checkbox-group v-model="formData.supported_markets">
            <el-checkbox label="A股" />
            <el-checkbox label="港股" />
            <el-checkbox label="美股" />
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="优先级" prop="priority">
          <el-input-number
            v-model="formData.priority"
            :min="1"
            :max="1000"
            placeholder="数字越小优先级越高"
          />
        </el-form-item>

        <el-form-item label="启用状态">
          <el-switch v-model="formData.enabled" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import {
  getAllTools,
  createToolConfig,
  updateToolConfig,
  deleteToolConfig,
  initializeTools,
  type ToolConfig,
  type ToolConfigCreate,
  type ToolConfigUpdate
} from '@/api/toolConfig'

// 数据
const loading = ref(false)
const saving = ref(false)
const tools = ref<ToolConfig[]>([])
const searchKeyword = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()

// 筛选器
const filters = ref({
  category: '',
  tool_type: '',
  enabled: undefined as boolean | undefined
})

// 表单数据
const formData = ref({
  tool_name: '',
  tool_display_name: '',
  description: '',
  category: 'other',
  tool_type: 'offline',
  supported_markets: [] as string[],
  priority: 100,
  enabled: true
})

// 计算属性
const dialogTitle = computed(() => (isEdit.value ? '编辑工具' : '创建工具'))

const filteredTools = computed(() => {
  let result = tools.value

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(
      (tool) =>
        tool.tool_name.toLowerCase().includes(keyword) ||
        tool.tool_display_name.toLowerCase().includes(keyword) ||
        tool.description.toLowerCase().includes(keyword)
    )
  }

  return result
})

// 表单验证规则
const rules: FormRules = {
  tool_name: [{ required: true, message: '请输入工具函数名', trigger: 'blur' }],
  tool_display_name: [{ required: true, message: '请输入显示名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入描述', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  tool_type: [{ required: true, message: '请选择类型', trigger: 'change' }]
}

// 方法
const loadTools = async () => {
  loading.value = true
  try {
    tools.value = await getAllTools({
      category: filters.value.category || undefined,
      tool_type: filters.value.tool_type || undefined,
      enabled: filters.value.enabled
    })
  } catch (error: any) {
    ElMessage.error(error.message || '加载工具列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  // 搜索逻辑已在computed中处理
}

const handleInitialize = async () => {
  try {
    await ElMessageBox.confirm('确定要初始化工具吗？这将扫描Toolkit类中的所有工具。', '确认初始化', {
      type: 'warning'
    })

    loading.value = true
    const result = await initializeTools()
    ElMessage.success(
      `初始化完成：成功 ${result.initialized} 个，跳过 ${result.skipped} 个，错误 ${result.errors} 个`
    )
    await loadTools()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '初始化工具失败')
    }
  } finally {
    loading.value = false
  }
}

const showCreateDialog = () => {
  isEdit.value = false
  formData.value = {
    tool_name: '',
    tool_display_name: '',
    description: '',
    category: 'other',
    tool_type: 'offline',
    supported_markets: [],
    priority: 100,
    enabled: true
  }
  dialogVisible.value = true
}

const viewTool = (tool: ToolConfig) => {
  isEdit.value = false
  formData.value = {
    tool_name: tool.tool_name,
    tool_display_name: tool.tool_display_name,
    description: tool.description,
    category: tool.category,
    tool_type: tool.tool_type,
    supported_markets: [...tool.supported_markets],
    priority: tool.priority,
    enabled: tool.enabled
  }
  dialogVisible.value = true
}

const editTool = (tool: ToolConfig) => {
  isEdit.value = true
  formData.value = {
    tool_name: tool.tool_name,
    tool_display_name: tool.tool_display_name,
    description: tool.description,
    category: tool.category,
    tool_type: tool.tool_type,
    supported_markets: [...tool.supported_markets],
    priority: tool.priority,
    enabled: tool.enabled
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      if (isEdit.value) {
        const tool = tools.value.find((t) => t.tool_name === formData.value.tool_name)
        if (tool?.id) {
          const updateData: ToolConfigUpdate = {
            tool_display_name: formData.value.tool_display_name,
            description: formData.value.description,
            category: formData.value.category,
            tool_type: formData.value.tool_type,
            supported_markets: formData.value.supported_markets,
            priority: formData.value.priority,
            enabled: formData.value.enabled
          }
          await updateToolConfig(tool.id, updateData)
          ElMessage.success('工具配置已更新')
        }
      } else {
        const createData: ToolConfigCreate = {
          ...formData.value
        }
        await createToolConfig(createData)
        ElMessage.success('工具配置已创建')
      }

      dialogVisible.value = false
      await loadTools()
    } catch (error: any) {
      ElMessage.error(error.message || '保存失败')
    } finally {
      saving.value = false
    }
  })
}

const handleToggleEnabled = async (tool: ToolConfig) => {
  if (!tool.id) return

  try {
    await updateToolConfig(tool.id, { enabled: tool.enabled })
    ElMessage.success('状态已更新')
  } catch (error: any) {
    tool.enabled = !tool.enabled // 回滚
    ElMessage.error(error.message || '更新状态失败')
  }
}

const deleteTool = async (tool: ToolConfig) => {
  if (!tool.id) return

  try {
    await ElMessageBox.confirm('确定要删除此工具配置吗？', '确认删除', {
      type: 'warning'
    })

    await deleteToolConfig(tool.id)
    ElMessage.success('工具配置已删除')
    await loadTools()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
}

// 辅助方法
const getCategoryLabel = (category: string) => {
  const map: Record<string, string> = {
    market_data: '市场数据',
    fundamentals: '基本面',
    news: '新闻',
    sentiment: '情绪',
    other: '其他'
  }
  return map[category] || category
}

const getCategoryTagType = (category: string) => {
  const map: Record<string, string> = {
    market_data: 'primary',
    fundamentals: 'success',
    news: 'info',
    sentiment: 'warning',
    other: ''
  }
  return map[category] || ''
}

const getTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    unified: '统一工具',
    online: '在线工具',
    offline: '离线工具'
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
onMounted(() => {
  loadTools()
})
</script>

<style lang="scss" scoped>
.tool-config {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h3 {
      margin: 0;
    }
  }

  .filters {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
  }
}
</style>
