# 打包可执行应用程序 - 快速说明

## 🚀 一键打包

```powershell
# 在项目根目录执行
powershell -ExecutionPolicy Bypass -File scripts\build_executable.ps1
```

## 📦 输出文件

打包完成后，文件位于 `release/packages/` 目录：

- **便携版**: `TradingAgentsCN-Portable-v1.0.0-preview-*.zip`
- **安装程序**: `TradingAgentsCNSetup-v1.0.0-preview.exe`

## ⚙️ 常用选项

```powershell
# 只创建便携版（不创建安装程序）
.\scripts\build_executable.ps1 -SkipInstaller

# 只创建安装程序（需要先有便携版）
.\scripts\build_executable.ps1 -SkipFrontend -SkipPortable

# 指定版本号
.\scripts\build_executable.ps1 -Version "1.0.1"
```

## 📋 前置要求

1. ✅ Python 3.10+
2. ✅ Node.js 18+ 和 Yarn
3. ✅ PowerShell 5.1+（Windows自带）
4. ⚠️ NSIS（仅用于创建安装程序，可选）

## 📚 详细文档

查看完整指南: [打包可执行应用程序指南.md](../docs/打包可执行应用程序指南.md)

