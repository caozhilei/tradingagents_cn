# TDX数据源配置对话框API Key和Endpoint显示修复

## 问题描述

在配置验证界面（`http://localhost:3000/settings/config`）编辑TDX数据源时，显示了API地址和API Key字段，但TDX数据源不需要这些配置。

## 问题原因

`DataSourceConfigDialog.vue` 组件中，API Key和API Secret字段对所有数据源都显示，没有针对TDX数据源做特殊处理。

## 修复内容

### 1. API Key字段条件显示

**文件**: `frontend/src/views/Settings/components/DataSourceConfigDialog.vue`

**修改前**：
```vue
<!-- API Key 输入框 -->
<el-form-item label="API Key" prop="api_key">
  <el-input
    v-model="formData.api_key"
    type="password"
    placeholder="输入 API Key（可选，留空则使用环境变量）"
    show-password
    clearable
  />
  <div class="form-tip">
    优先级：数据库配置 > 环境变量。留空则使用 .env 文件中的配置
  </div>
</el-form-item>
```

**修改后**：
```vue
<!-- API Key 输入框（TDX数据源不需要） -->
<el-form-item v-if="!isTdxDataSource" label="API Key" prop="api_key">
  <el-input
    v-model="formData.api_key"
    type="password"
    placeholder="输入 API Key（可选，留空则使用环境变量）"
    show-password
    clearable
  />
  <div class="form-tip">
    优先级：数据库配置 > 环境变量。留空则使用 .env 文件中的配置
  </div>
</el-form-item>

<!-- TDX 特殊提示：不需要API Key -->
<el-form-item v-if="isTdxDataSource" label="API Key">
  <el-input
    v-model="formData.api_key"
    placeholder="通达信无需填写API Key（留空即可）"
    disabled
  />
  <div class="form-tip">
    💡 通达信数据源直接连接到通达信服务器，无需配置API Key。系统会自动连接。
  </div>
</el-form-item>
```

### 2. API Secret字段条件显示

**修改前**：
```vue
<!-- API Secret 输入框（某些数据源需要） -->
<el-form-item v-if="needsApiSecret" label="API Secret" prop="api_secret">
  ...
</el-form-item>
```

**修改后**：
```vue
<!-- API Secret 输入框（某些数据源需要，TDX不需要） -->
<el-form-item v-if="needsApiSecret && !isTdxDataSource" label="API Secret" prop="api_secret">
  ...
</el-form-item>
```

### 3. 保存时删除TDX不需要的字段

**修改前**：
```typescript
if (isTdxDataSource.value) {
  delete payload.endpoint
  console.log('🔍 [保存] TDX数据源：删除endpoint字段（TDX不需要API端点）')
}
```

**修改后**：
```typescript
if (isTdxDataSource.value) {
  delete payload.endpoint
  delete payload.api_key
  delete payload.api_secret
  console.log('🔍 [保存] TDX数据源：删除endpoint、api_key、api_secret字段（TDX不需要这些配置）')
}
```

### 4. 测试连接时处理TDX不需要的字段

**修改前**：
```typescript
// 🔥 TDX数据源特殊处理：endpoint为空时设置为null，避免空字符串导致验证失败
if (isTdxDataSource.value && (!testPayload.endpoint || testPayload.endpoint.trim() === '')) {
  testPayload.endpoint = null
  console.log('🔍 [测试连接] TDX数据源：endpoint为空，设置为null')
}
```

**修改后**：
```typescript
// 🔥 TDX数据源特殊处理：endpoint、api_key、api_secret为空时设置为null，避免空字符串导致验证失败
if (isTdxDataSource.value) {
  if (!testPayload.endpoint || testPayload.endpoint.trim() === '') {
    testPayload.endpoint = null
  }
  if (!testPayload.api_key || testPayload.api_key.trim() === '') {
    testPayload.api_key = null
  }
  if (!testPayload.api_secret || testPayload.api_secret.trim() === '') {
    testPayload.api_secret = null
  }
  console.log('🔍 [测试连接] TDX数据源：endpoint、api_key、api_secret设置为null（TDX不需要这些配置）')
}
```

## TDX数据源配置说明

### 不需要的字段

- ❌ **API端点（endpoint）**：TDX直接连接到内置的服务器列表，无需配置端点
- ❌ **API Key**：TDX不需要API Key认证
- ❌ **API Secret**：TDX不需要API Secret

### 需要的字段

- ✅ **数据源类型（type）**：设置为 `tdx`
- ✅ **显示名称（display_name）**：例如"通达信"
- ✅ **优先级（priority）**：数字越大优先级越高
- ✅ **超时时间（timeout）**：连接超时时间（秒）
- ✅ **速率限制（rate_limit）**：请求速率限制

## 验证步骤

1. **刷新浏览器**（硬刷新：Ctrl+F5）
2. **打开配置管理页面**：`http://localhost:3000/settings/config`
3. **切换到"数据源配置"标签**
4. **编辑TDX数据源**：
   - ✅ API端点字段应显示为禁用状态，提示"通达信无需填写API端点（留空即可）"
   - ✅ API Key字段应显示为禁用状态，提示"通达信无需填写API Key（留空即可）"
   - ✅ API Secret字段应不显示（TDX不需要）
5. **保存配置**：应成功保存，不会保存endpoint、api_key、api_secret字段
6. **测试连接**：应成功测试，不会因为缺少API Key而失败

## 相关文件

- `frontend/src/views/Settings/components/DataSourceConfigDialog.vue` - 数据源配置对话框（已修复）
- `app/routers/config.py` - 后端配置API（已包含TDX endpoint处理）
- `app/services/config_service.py` - 配置服务（已包含TDX测试逻辑）

## 状态

✅ **已完成**：
- ✅ API Key字段对TDX数据源显示为禁用状态
- ✅ API Secret字段对TDX数据源不显示
- ✅ 保存时删除TDX不需要的字段
- ✅ 测试连接时正确处理TDX不需要的字段
- ✅ 前端镜像已重新构建
- ✅ 前端服务已重启

现在TDX数据源在配置验证界面应该正确显示，不会要求填写API地址和Key了！

