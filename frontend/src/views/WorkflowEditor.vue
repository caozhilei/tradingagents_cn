<template>
  <div class="workflow-editor">
    <el-container class="editor-container">
      <!-- 顶部工具栏 -->
      <el-header class="editor-header">
        <div class="toolbar-left">
          <!-- 文件操作组 -->
          <el-button-group>
            <el-button @click="handleNew" title="新建工作流">
              <el-icon><Plus /></el-icon>
              新建
            </el-button>
            <el-select
              v-model="selectedWorkflowId"
              placeholder="选择工作流..."
              filterable
              clearable
              :loading="loadingWorkflows"
              @change="handleWorkflowSelect"
              style="width: 250px;"
            >
              <el-option
                v-for="workflow in workflowList"
                :key="workflow.id"
                :label="workflow.name"
                :value="workflow.id"
              >
                <div style="display: flex; align-items: center; gap: 8px;">
                  <el-icon><Document /></el-icon>
                  <div style="flex: 1;">
                    <div style="font-weight: 500;">{{ workflow.name }}</div>
                    <div style="color: #8492a6; font-size: 12px; margin-top: 2px;">
                      {{ workflow.description || '无描述' }}
                    </div>
                  </div>
                </div>
              </el-option>
            </el-select>
            <el-button
              @click="loadWorkflowList"
              :loading="loadingWorkflows"
              title="刷新工作流列表"
              circle
            >
              <el-icon><Refresh /></el-icon>
            </el-button>
          </el-button-group>
          
          <el-divider direction="vertical" />
          
          <!-- 保存和导出组 -->
          <el-button-group>
            <el-button
              type="primary"
              @click="handleSave"
              :disabled="!canSave"
              title="保存工作流 (Ctrl+S)"
            >
              <el-icon><Download /></el-icon>
              保存
            </el-button>
            <el-button
              @click="handleExport"
              title="导出工作流配置"
            >
              <el-icon><Upload /></el-icon>
              导出
            </el-button>
            <el-button
              @click="handleValidate"
              title="验证工作流配置"
            >
              <el-icon><Check /></el-icon>
              验证
            </el-button>
            <el-button
              type="success"
              @click="handleRunVerification"
              title="运行验证工作流"
            >
              <el-icon><VideoPlay /></el-icon>
              运行验证
            </el-button>
          </el-button-group>
          
          <el-divider direction="vertical" />
          
          <!-- 编辑操作组 -->
          <el-button-group>
            <el-button 
              @click="handleUndo" 
              :disabled="!canUndo"
              title="撤销 (Ctrl+Z)"
            >
              <el-icon><RefreshLeft /></el-icon>
              撤销
            </el-button>
            <el-button 
              @click="handleRedo" 
              :disabled="!canRedo"
              title="重做 (Ctrl+Y)"
            >
              <el-icon><RefreshRight /></el-icon>
              重做
            </el-button>
            <el-button 
              @click="handleDeleteSelected" 
              :disabled="!selectedNode && !selectedEdge"
              type="danger"
              title="删除选中项 (Delete)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </el-button-group>
        </div>
        
        <div class="toolbar-center">
          <el-input
            v-model="workflowName"
            placeholder="工作流名称"
            style="width: 300px"
            @change="markDirty"
            clearable
          >
            <template #prefix>
              <el-icon><Document /></el-icon>
            </template>
          </el-input>
        </div>
        
        <div class="toolbar-right">
          <el-button
            @click="nodePaletteVisible = !nodePaletteVisible"
            :type="nodePaletteVisible ? 'primary' : 'default'"
            :title="nodePaletteVisible ? '隐藏工具箱' : '显示工具箱'"
            circle
          >
            <el-icon><Tools /></el-icon>
          </el-button>
          <el-button
            @click="configPanelVisible = !configPanelVisible"
            :type="configPanelVisible ? 'primary' : 'default'"
            :title="configPanelVisible ? '隐藏配置' : '显示配置'"
            circle
          >
            <el-icon><Setting /></el-icon>
          </el-button>
        </div>
      </el-header>

      <el-container>
        <!-- 左侧节点工具箱 -->
        <el-aside
          v-if="nodePaletteVisible"
          width="250px"
          class="node-palette-aside"
        >
          <NodePalette />
        </el-aside>

        <!-- 中间画布区域 -->
        <el-main class="canvas-main">
          <FlowCanvas
            ref="flowCanvasRef"
            v-model:nodes="nodes"
            v-model:edges="edges"
            v-model:viewport="viewport"
            :selected-node="selectedNode"
            :selected-edge="selectedEdge"
            @node-select="handleNodeSelect"
            @edge-select="handleEdgeSelect"
            @node-delete="handleNodeDelete"
            @edge-delete="handleEdgeDelete"
            @connect="handleConnect"
            @node-add="handleNodeAdd"
            @context-menu="handleContextMenu"
          />
        </el-main>

        <!-- 右侧配置面板 -->
        <el-aside
          v-if="configPanelVisible"
          width="350px"
          class="config-panel-aside"
        >
          <NodeConfigPanel
            v-if="selectedNode"
            :node="selectedNode"
            @update="handleNodeUpdate"
            @close="selectedNode = null"
          />
          <EdgeConfigPanel
            v-else-if="selectedEdge"
            :edge="selectedEdge"
            @update="handleEdgeUpdate"
            @close="selectedEdge = null"
          />
          <div v-else class="empty-config-panel">
            <el-empty description="请选择一个节点或边进行配置" />
          </div>
        </el-aside>
      </el-container>
    </el-container>

    <!-- 保存对话框 -->
    <el-dialog
      v-model="saveDialogVisible"
      title="保存工作流"
      width="500px"
      @closed="handleSaveDialogClosed"
    >
      <el-form :model="saveForm" label-width="100px">
        <el-form-item label="工作流名称" required>
          <el-input
            v-model="saveForm.name"
            placeholder="请输入工作流名称"
          />
          <div style="margin-top: 4px;" v-if="hasExistingWorkflow">
            <el-text type="info" size="small">同名时将覆盖原模板，不同名时将创建新模板</el-text>
          </div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="saveForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入工作流描述（可选）"
          />
        </el-form-item>
        <el-form-item label="保存方式" v-if="hasExistingWorkflow">
          <el-radio-group v-model="saveMode">
            <el-radio label="update">更新当前工作流</el-radio>
            <el-radio label="create">另存为新工作流</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmSave" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 运行验证对话框 -->
    <el-dialog
      v-model="verificationDialogVisible"
      title="运行验证"
      width="500px"
    >
      <el-form :model="verificationForm" label-width="100px">
        <el-form-item label="股票代码" required>
          <el-input
            v-model="verificationForm.symbol"
            placeholder="请输入股票代码 (如 600519)"
          />
        </el-form-item>
        <el-form-item label="分析深度">
          <el-radio-group v-model="verificationForm.research_depth">
            <el-radio label="快速">快速</el-radio>
            <el-radio label="标准">标准</el-radio>
            <el-radio label="深度">深度</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="分析范围">
           <el-checkbox-group v-model="verificationForm.selected_analysts">
              <el-checkbox label="market">市场分析</el-checkbox>
              <el-checkbox label="fundamentals">基本面分析</el-checkbox>
              <el-checkbox label="news">新闻分析</el-checkbox>
              <el-checkbox label="social">社媒分析</el-checkbox>
           </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="verificationDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmVerification" :loading="verifying">
          开始运行
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useWorkflowStore } from '@/stores/workflow'
import { workflowApi } from '@/api/workflow'
import { analysisApi } from '@/api/analysis'
import FlowCanvas from '@/components/Workflow/FlowCanvas.vue'
import NodePalette from '@/components/Workflow/NodePalette.vue'
import NodeConfigPanel from '@/components/Workflow/NodeConfigPanel.vue'
import EdgeConfigPanel from '@/components/Workflow/EdgeConfigPanel.vue'
import ContextMenu from '@/components/Workflow/ContextMenu.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  RefreshLeft,
  RefreshRight,
  Delete,
  Refresh,
  Plus,
  Upload,
  Download,
  Document,
  Check,
  Setting,
  Tools,
  VideoPlay
} from '@element-plus/icons-vue'
import type { WorkflowListItem } from '@/types/workflow'
import type { FlowNode, FlowEdge } from '@/stores/workflow'

const workflowStore = useWorkflowStore()

// 计算属性
// 拖拽防抖定时器
let dragDebounceTimer: ReturnType<typeof setTimeout> | null = null
let lastNodePositions: Map<string, { x: number; y: number }> = new Map()

const nodes = computed({
  get: () => workflowStore.nodes,
  set: (value) => {
    // 检查是否有位置变化（拖拽）
    let hasPositionChange = false
    if (value.length === workflowStore.nodes.length) {
      // 比较位置变化
      for (const newNode of value) {
        const oldNode = workflowStore.nodes.find(n => n.id === newNode.id)
        if (oldNode) {
          const lastPos = lastNodePositions.get(newNode.id)
          const currentPos = { x: newNode.position.x, y: newNode.position.y }
          
          if (!lastPos || 
              Math.abs(lastPos.x - currentPos.x) > 1 || 
              Math.abs(lastPos.y - currentPos.y) > 1) {
            hasPositionChange = true
            lastNodePositions.set(newNode.id, currentPos)
          }
        }
      }
    }
    
    workflowStore.nodes = value
    workflowStore.isDirty = true
    
    // 如果是位置变化（拖拽），延迟保存历史，避免频繁触发
    if (hasPositionChange) {
      if (dragDebounceTimer) {
        clearTimeout(dragDebounceTimer)
      }
      dragDebounceTimer = setTimeout(() => {
        // 拖拽结束后保存历史
        if (workflowStore.saveHistory) {
          workflowStore.saveHistory()
        }
      }, 500)
    } else {
      // 非位置变化（如添加/删除节点），立即保存历史
      if (workflowStore.saveHistory) {
        workflowStore.saveHistory()
      }
      // 更新位置缓存
      value.forEach(node => {
        lastNodePositions.set(node.id, { x: node.position.x, y: node.position.y })
      })
    }
  }
})

const edges = computed({
  get: () => workflowStore.edges,
  set: (value) => {
    workflowStore.edges = value
    workflowStore.isDirty = true
  }
})

const viewport = computed({
  get: () => workflowStore.viewport,
  set: (value) => workflowStore.viewport = value
})

const workflowName = computed({
  get: () => workflowStore.workflowName,
  set: (value) => {
    workflowStore.workflowName = value
    workflowStore.isDirty = true
  }
})

const nodePaletteVisible = computed({
  get: () => workflowStore.nodePaletteVisible,
  set: (value) => workflowStore.nodePaletteVisible = value
})

const configPanelVisible = computed({
  get: () => workflowStore.configPanelVisible,
  set: (value) => workflowStore.configPanelVisible = value
})

const selectedNode = computed({
  get: () => workflowStore.selectedNode,
  set: (value) => workflowStore.selectedNode = value
})

const selectedEdge = computed({
  get: () => workflowStore.selectedEdge,
  set: (value) => workflowStore.selectedEdge = value
})

const canSave = computed(() => workflowStore.canSave)
const canUndo = computed(() => workflowStore.canUndo)
const canRedo = computed(() => workflowStore.canRedo)
const flowCanvasRef = ref<InstanceType<typeof FlowCanvas> | null>(null)

// 工作流列表相关
const workflowList = ref<WorkflowListItem[]>([])
const selectedWorkflowId = ref<string>('')
const loadingWorkflows = ref(false)

// 保存对话框状态
const saveDialogVisible = ref(false)
const saving = ref(false)
const saveForm = ref({
  name: '',
  description: ''
})
const saveMode = ref('update')

const hasExistingWorkflow = computed(() => !!workflowStore.workflowId)

// 右键菜单状态
const contextMenuVisible = ref(false)
const contextMenuPosition = ref({ x: 0, y: 0 })
const contextMenuType = ref<'node' | 'edge' | 'canvas'>('canvas')

// 事件处理
function handleNodeAdd(nodeType: string, position: { x: number; y: number }, config?: Record<string, any>) {
  workflowStore.addNode(nodeType, position, config)
}

function handleNodeSelect(node: FlowNode | null) {
  workflowStore.selectedNode = node
  workflowStore.selectedEdge = null
}

function handleEdgeSelect(edge: FlowEdge | null) {
  workflowStore.selectedEdge = edge
  workflowStore.selectedNode = null
}

function handleNodeDelete(nodeId: string) {
  ElMessageBox.confirm(
    '确定要删除此节点吗？相关的边也会被删除。',
    '确认删除',
    { type: 'warning' }
  ).then(() => {
    workflowStore.deleteNode(nodeId)
    ElMessage.success('节点已删除')
  }).catch(() => {})
}

function handleEdgeDelete(edgeId: string) {
  workflowStore.deleteEdge(edgeId)
  ElMessage.success('边已删除')
}

function handleConnect(connection: { source: string; target: string }) {
  const success = workflowStore.addEdge(connection.source, connection.target)
  if (success) {
    ElMessage.success('连接已添加')
  } else {
    ElMessage.warning('连接失败：连接已存在或无效')
  }
}

function handleUndo() {
  workflowStore.undo()
  ElMessage.success('已撤销')
}

function handleRedo() {
  workflowStore.redo()
  ElMessage.success('已重做')
}

function handleDeleteSelected() {
  if (workflowStore.selectedNode) {
    handleNodeDelete(workflowStore.selectedNode.id)
  } else if (workflowStore.selectedEdge) {
    handleEdgeDelete(workflowStore.selectedEdge.id)
  }
}

function handleContextMenu(context: { type: 'node' | 'edge' | 'canvas'; node?: FlowNode; edge?: FlowEdge; position: { x: number; y: number } }) {
  contextMenuVisible.value = true
  contextMenuPosition.value = context.position
  contextMenuType.value = context.type
}

function handleContextMenuDelete() {
  contextMenuVisible.value = false
  handleDeleteSelected()
}

// 点击其他地方关闭右键菜单
function handleDocumentClick() {
  contextMenuVisible.value = false
}

function handleNodeUpdate(nodeId: string, config: Record<string, any>) {
  workflowStore.updateNodeConfig(nodeId, config)
}

function handleEdgeUpdate(edgeId: string, config: Record<string, any>) {
  workflowStore.updateEdgeConfig(edgeId, config)
}

function handleSave() {
  // 打开保存对话框
  const currentConfig = workflowStore.exportConfig()
  saveForm.value = {
    name: currentConfig.name || '新工作流',
    description: currentConfig.description || ''
  }
  
  saveDialogVisible.value = true
}

function handleSaveDialogClosed() {
  // 对话框关闭时重置表单
  saveForm.value = {
    name: '',
    description: ''
  }
  saveMode.value = 'update'
}

async function handleConfirmSave() {
  // 验证表单
  if (!saveForm.value.name || saveForm.value.name.trim() === '') {
    ElMessage.warning('请输入工作流名称')
    return
  }

  saving.value = true
  try {
    const config = workflowStore.exportConfig()
    let result: any

    // 检查是否存在同名工作流
    const workflowsResult = await workflowApi.listWorkflows()
    const workflows = Array.isArray(workflowsResult) ? workflowsResult : (workflowsResult?.data || [])
    const existingWorkflow = workflows.find((w: any) => w.name === saveForm.value.name.trim())

    if (existingWorkflow) {
      // 存在同名工作流
      if (hasExistingWorkflow.value && existingWorkflow.id === workflowStore.workflowId) {
        // 同名且是当前工作流，直接更新
        result = await workflowApi.updateWorkflow(workflowStore.workflowId!, {
          name: saveForm.value.name,
          description: saveForm.value.description,
          config
        })
        
        if (result.success) {
          ElMessage.success('工作流已更新')
          workflowStore.workflowName = saveForm.value.name
          workflowStore.workflowDescription = saveForm.value.description
          workflowStore.isDirty = false
          saveDialogVisible.value = false
          
          // 刷新工作流列表
          await loadWorkflowList()
        }
      } else {
        // 同名但不是当前工作流，提示用户是否覆盖
        try {
          await ElMessageBox.confirm(
            `工作流 "${saveForm.value.name}" 已存在，是否覆盖？`,
            '确认覆盖',
            {
              confirmButtonText: '覆盖',
              cancelButtonText: '取消',
              type: 'warning'
            }
          )
          
          // 用户确认覆盖，更新同名工作流
          result = await workflowApi.updateWorkflow(existingWorkflow.id, {
            name: saveForm.value.name,
            description: saveForm.value.description,
            config
          })
          
          if (result.success) {
            ElMessage.success('工作流已覆盖')
            // 如果覆盖的是当前工作流，更新 store
            if (hasExistingWorkflow.value && existingWorkflow.id === workflowStore.workflowId) {
              workflowStore.workflowName = saveForm.value.name
              workflowStore.workflowDescription = saveForm.value.description
            }
            workflowStore.isDirty = false
            saveDialogVisible.value = false
            
            // 刷新工作流列表
            await loadWorkflowList()
          }
        } catch {
          // 用户取消，不执行任何操作
          saving.value = false
          return
        }
      }
    } else {
      // 不存在同名工作流
      if (saveMode.value === 'update' && hasExistingWorkflow.value) {
        // 用户选择更新模式，但名称已改变，更新当前工作流
        result = await workflowApi.updateWorkflow(workflowStore.workflowId!, {
          name: saveForm.value.name,
          description: saveForm.value.description,
          config
        })
        
        if (result.success) {
          ElMessage.success('工作流已更新')
          workflowStore.workflowName = saveForm.value.name
          workflowStore.workflowDescription = saveForm.value.description
          workflowStore.isDirty = false
          saveDialogVisible.value = false
          
          // 刷新工作流列表
          await loadWorkflowList()
        }
      } else {
        // 创建新模板
        result = await workflowApi.createWorkflow({
          name: saveForm.value.name,
          description: saveForm.value.description,
          config
        })
        
        if (result.success && result.data) {
          const createdData = result.data as any
          if (createdData?.id) {
            // 如果用户选择创建新模板，不更新当前的 workflowId
            // 这样用户可以继续编辑原工作流，新模板作为副本保存
            ElMessage.success('新模板已创建')
            workflowStore.isDirty = false
            saveDialogVisible.value = false
            
            // 刷新工作流列表
            await loadWorkflowList()
          }
        }
      }
    }
  } catch (error: any) {
    // 处理后端返回的同名错误
    if (error.message && error.message.includes('已存在')) {
      // 如果后端返回同名错误，说明在检查后又有同名创建了，提示用户
      ElMessage.warning('工作流名称已存在，请使用其他名称或覆盖现有工作流')
    } else {
      ElMessage.error(error.message || '保存失败')
    }
  } finally {
    saving.value = false
  }
}

// 加载工作流列表
async function loadWorkflowList() {
  loadingWorkflows.value = true
  try {
    const result = await workflowApi.listWorkflows()
    // 处理数组或 ApiResponse 格式
    if (Array.isArray(result)) {
      workflowList.value = result
    } else if (result && typeof result === 'object' && 'data' in result) {
      workflowList.value = Array.isArray(result.data) ? result.data : []
    } else {
      workflowList.value = []
    }
  } catch (error: any) {
    ElMessage.error(error.message || '加载工作流列表失败')
    workflowList.value = []
  } finally {
    loadingWorkflows.value = false
  }
}

// 处理工作流选择
function handleWorkflowSelect(workflowId: string | null) {
  if (!workflowId) {
    return
  }
  loadWorkflow(workflowId)
  // 选择后清空选择，以便下次可以重新选择同一个工作流
  nextTick(() => {
    selectedWorkflowId.value = ''
  })
}

async function loadWorkflow(id: string) {
  try {
    const result = await workflowApi.getWorkflow(id)
    // API拦截器已经返回了response.data，所以result就是{success, data, message}
    if (result.success && result.data) {
      await workflowStore.loadWorkflow(result.data)
      workflowStore.workflowId = id
      // 初始化位置缓存，用于检测拖拽
      nextTick(() => {
        workflowStore.nodes.forEach(node => {
          lastNodePositions.set(node.id, { x: node.position.x, y: node.position.y })
        })
      })
      ElMessage.success('工作流已加载')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '加载失败')
  }
}

function handleNew() {
  if (workflowStore.isDirty) {
    ElMessageBox.confirm(
      '当前工作流有未保存的更改，确定要新建吗？',
      '确认',
      { type: 'warning' }
    ).then(() => {
      workflowStore.reset()
    }).catch(() => {})
  } else {
    workflowStore.reset()
  }
}

function handleExport() {
  const config = workflowStore.exportConfig()
  const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${workflowName.value || 'workflow'}.json`
  a.click()
  URL.revokeObjectURL(url)
}

async function handleValidate() {
  try {
    if (!workflowStore.workflowId) {
      ElMessage.warning('请先保存工作流')
      return
    }
    const result = await workflowApi.validateWorkflow(workflowStore.workflowId)
    // API拦截器已经返回了response.data，所以result就是{success, data, message}
    if (result.success) {
      if (result.data.valid) {
        ElMessage.success('工作流验证通过')
      } else {
        ElMessage.error(`工作流验证失败: ${result.data.errors?.join(', ')}`)
      }
    } else {
      ElMessage.error(result.message || '验证失败')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '验证失败')
  }
}

function markDirty() {
  workflowStore.isDirty = true
}

// 键盘快捷键处理
function handleKeyDown(event: KeyboardEvent) {
  // 检查是否在输入框中
  const target = event.target as HTMLElement
  if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
    return // 在输入框中，不处理快捷键
  }

  // Ctrl+Z: 撤销
  if (event.ctrlKey && event.key === 'z' && !event.shiftKey) {
    event.preventDefault()
    if (canUndo.value) {
      handleUndo()
    }
    return
  }

  // Ctrl+Y 或 Ctrl+Shift+Z: 重做
  if ((event.ctrlKey && event.key === 'y') || (event.ctrlKey && event.shiftKey && event.key === 'z')) {
    event.preventDefault()
    if (canRedo.value) {
      handleRedo()
    }
    return
  }

  // Delete: 删除选中项
  if (event.key === 'Delete' || event.key === 'Backspace') {
    event.preventDefault()
    if (workflowStore.selectedNode || workflowStore.selectedEdge) {
      handleDeleteSelected()
    }
    return
  }
}

// 验证相关
const verificationDialogVisible = ref(false)
const verifying = ref(false)
const verificationForm = ref({
  symbol: '',
  research_depth: '标准',
  selected_analysts: ['market', 'fundamentals', 'news']
})

function handleRunVerification() {
  verificationDialogVisible.value = true
}

async function confirmVerification() {
  if (!verificationForm.value.symbol) {
    ElMessage.warning('请输入股票代码')
    return
  }
  
  verifying.value = true
  try {
    const config = workflowStore.exportConfig()
    
    // 构建分析请求
    const request = {
      symbol: verificationForm.value.symbol,
      parameters: {
        research_depth: verificationForm.value.research_depth,
        selected_analysts: verificationForm.value.selected_analysts,
        workflow_config: config // 注入当前工作流配置
      }
    }
    
    // 使用 startSingleAnalysis 而不是 submitSingleAnalysis (根据API定义)
    const response = await analysisApi.startSingleAnalysis(request)
    
    // 检查响应格式，有些API返回直接数据，有些返回ApiResponse
    const result = response.data || response
    
    if (result && result.task_id) {
       ElMessage.success('验证任务已启动，请在任务中心查看进度')
       verificationDialogVisible.value = false
       
       // 打开新窗口查看任务列表
       // 注意：这里假设前端路由结构
       const routeUrl = window.location.origin + '/#/tasks'
       window.open(routeUrl, '_blank')
    } else {
      ElMessage.error('任务启动失败')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '验证请求失败')
  } finally {
    verifying.value = false
  }
}

// 页面初始化时自动加载默认工作流
onMounted(async () => {
  // 添加键盘事件监听
  window.addEventListener('keydown', handleKeyDown)
  // 添加点击事件监听（用于关闭右键菜单）
  document.addEventListener('click', handleDocumentClick)
  // 阻止画布右键默认菜单
  document.addEventListener('contextmenu', (e) => {
    const target = e.target as HTMLElement
    if (target.closest('.vue-flow')) {
      e.preventDefault()
    }
  })
  
  // 加载工作流列表
  await loadWorkflowList()
  
  try {
    // 尝试加载默认工作流配置
    const result = await workflowApi.getDefaultWorkflow()
    // API拦截器已经返回了response.data，所以result就是{success, data, message}
    if (result.success && result.data) {
      await workflowStore.loadWorkflow(result.data)
      
      // 如果默认工作流在列表中，更新选择器显示
      // 注意：默认工作流可能没有 id（如果是生成的配置），所以需要根据名称匹配
      if (workflowStore.workflowId) {
        const defaultWorkflow = workflowList.value.find(w => w.id === workflowStore.workflowId)
        if (defaultWorkflow) {
          selectedWorkflowId.value = defaultWorkflow.id
        }
      } else {
        // 如果没有 id，尝试根据名称匹配
        const defaultWorkflow = workflowList.value.find(w => w.name === workflowStore.workflowName)
        if (defaultWorkflow) {
          selectedWorkflowId.value = defaultWorkflow.id
          workflowStore.workflowId = defaultWorkflow.id
        }
      }
      
      // 初始化位置缓存，用于检测拖拽
      nextTick(() => {
        workflowStore.nodes.forEach(node => {
          lastNodePositions.set(node.id, { x: node.position.x, y: node.position.y })
        })
      })
      ElMessage.success('已加载默认工作流')
    } else {
      console.warn('默认工作流加载失败: 未返回有效数据')
    }
  } catch (error: any) {
    console.warn('加载默认工作流失败:', error)
    // 静默失败，用户可以手动创建或加载
  }
})

onUnmounted(() => {
  // 移除事件监听
  window.removeEventListener('keydown', handleKeyDown)
  document.removeEventListener('click', handleDocumentClick)
})
</script>

<style scoped>
.workflow-editor {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.editor-container {
  height: 100%;
}

.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: linear-gradient(to bottom, #ffffff 0%, #f8f9fa 100%);
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
  min-height: 64px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-center {
  flex: 0 0 auto;
  display: flex;
  justify-content: center;
  margin: 0 20px;
}

:deep(.el-button-group) {
  display: inline-flex;
}

:deep(.el-button-group .el-button) {
  margin-left: 0;
}

:deep(.el-button-group .el-button + .el-button) {
  margin-left: -1px;
}

:deep(.el-select) {
  margin-right: 0;
}

:deep(.el-divider--vertical) {
  margin: 0 8px;
  height: 24px;
}

.node-palette-aside {
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
}

.canvas-main {
  background: #fafafa;
  padding: 0;
  overflow: hidden;
}

.config-panel-aside {
  background: #f5f7fa;
  border-left: 1px solid #e4e7ed;
}

.empty-config-panel {
  padding: 20px;
}
</style>

