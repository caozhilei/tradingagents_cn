<template>
  <div
    v-if="visible"
    class="context-menu"
    :style="{ left: `${position.x}px`, top: `${position.y}px` }"
    @click.stop
  >
    <div
      v-for="item in menuItems"
      :key="item.key"
      class="context-menu-item"
      :class="{ disabled: item.disabled }"
      @click="handleItemClick(item)"
    >
      <el-icon v-if="item.icon" class="menu-icon">
        <component :is="item.icon" />
      </el-icon>
      <span>{{ item.label }}</span>
      <span v-if="item.shortcut" class="shortcut">{{ item.shortcut }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Delete, CopyDocument, DocumentAdd, RefreshLeft } from '@element-plus/icons-vue'

interface MenuItem {
  key: string
  label: string
  icon?: any
  shortcut?: string
  disabled?: boolean
  action: () => void
}

interface Props {
  visible: boolean
  position: { x: number; y: number }
  type: 'node' | 'edge' | 'canvas'
  canDelete?: boolean
  canUndo?: boolean
  canRedo?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  canDelete: true,
  canUndo: false,
  canRedo: false
})

const emit = defineEmits<{
  delete: []
  copy: []
  paste: []
  duplicate: []
  undo: []
  redo: []
}>()

const menuItems = computed<MenuItem[]>(() => {
  const items: MenuItem[] = []

  if (props.type === 'node') {
    items.push(
      {
        key: 'delete',
        label: '删除节点',
        icon: Delete,
        shortcut: 'Delete',
        disabled: !props.canDelete,
        action: () => emit('delete')
      },
      {
        key: 'duplicate',
        label: '复制节点',
        icon: CopyDocument,
        shortcut: 'Ctrl+D',
        action: () => emit('duplicate')
      }
    )
  } else if (props.type === 'edge') {
    items.push({
      key: 'delete',
      label: '删除连接',
      icon: Delete,
      shortcut: 'Delete',
      disabled: !props.canDelete,
      action: () => emit('delete')
    })
  } else if (props.type === 'canvas') {
    items.push(
      {
        key: 'paste',
        label: '粘贴',
        icon: DocumentAdd,
        shortcut: 'Ctrl+V',
        action: () => emit('paste')
      },
      {
        key: 'undo',
        label: '撤销',
        icon: RefreshLeft,
        shortcut: 'Ctrl+Z',
        disabled: !props.canUndo,
        action: () => emit('undo')
      }
    )
  }

  return items
})

function handleItemClick(item: MenuItem) {
  if (item.disabled) return
  item.action()
}
</script>

<style scoped>
.context-menu {
  position: fixed;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  padding: 4px 0;
  z-index: 9999;
  min-width: 160px;
}

.context-menu-item {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  color: #606266;
  transition: background-color 0.2s;
}

.context-menu-item:hover:not(.disabled) {
  background-color: #f5f7fa;
}

.context-menu-item.disabled {
  color: #c0c4cc;
  cursor: not-allowed;
}

.menu-icon {
  margin-right: 8px;
  font-size: 16px;
}

.shortcut {
  margin-left: auto;
  color: #909399;
  font-size: 12px;
}
</style>

