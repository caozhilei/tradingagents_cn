<template>
  <div class="agent-settings">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        智能体设置
      </h1>
      <p class="page-description">
        配置和管理智能体的提示词模板和工具配置，自定义智能体的行为和功能
      </p>
    </div>

    <!-- 标签页切换 -->
    <el-tabs v-model="activeTab" class="settings-tabs">
      <el-tab-pane label="提示词配置" name="prompt">
        <PromptTemplateConfig />
      </el-tab-pane>
      <el-tab-pane label="工具配置" name="tool">
        <ToolConfig />
      </el-tab-pane>
      <el-tab-pane label="智能体工具配置" name="agent-tool">
        <AgentToolConfig />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import PromptTemplateConfig from './components/PromptTemplateConfig.vue'
import ToolConfig from './components/ToolConfig.vue'
import AgentToolConfig from './components/AgentToolConfig.vue'

const activeTab = ref('prompt')
</script>

<style lang="scss" scoped>
.agent-settings {
  padding: 24px;

  .page-header {
    margin-bottom: 24px;

    .page-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 24px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin: 0 0 8px 0;
    }

    .page-description {
      color: var(--el-text-color-regular);
      margin: 0;
      font-size: 14px;
    }
  }

  .settings-tabs {
    :deep(.el-tab-pane) {
      padding-top: 20px;
    }
  }
}
</style>

