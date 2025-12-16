# TradingAgents 中文增强版

<div align="center">

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](#)
[![Version](https://img.shields.io/badge/Version-v1.0.0--preview-green.svg)](./VERSION)
[![Documentation](https://img.shields.io/badge/docs-中文文档-green.svg)](./docs/)

**基于多智能体与大模型的股票分析学习平台**

[快速开始](#-快速开始) • [功能特性](#-核心功能) • [部署指南](#-部署方式) • [文档中心](./docs/)

</div>

---

## 📖 项目简介

**TradingAgents-CN** 是一个面向中文用户的**多智能体与大模型股票分析学习平台**，基于 TradingAgents 项目进行中文化增强和功能扩展。

> ⚠️ **重要声明**: 本平台仅用于**学习与研究**目的，不提供实盘交易指令，不构成投资建议。投资有风险，决策需谨慎。

### 🎯 项目定位

- 🎓 **学习平台**: 系统化学习多智能体交易框架与 AI 大模型在金融领域的应用
- 🔬 **研究工具**: 合规的股票研究与策略实验环境
- 🌏 **中文优化**: 完整的中文本地化支持，适配 A股/港股/美股市场
- 🚀 **企业级架构**: FastAPI + Vue 3 现代化技术栈，支持生产环境部署

---

## ✨ 核心功能

### 🏗️ v1.0.0-preview 架构升级

#### 全新技术架构
- **后端**: FastAPI + Uvicorn，提供高性能 RESTful API
- **前端**: Vue 3 + TypeScript + Element Plus，现代化单页应用
- **数据库**: MongoDB + Redis 双数据库架构，性能提升 10 倍
- **部署**: Docker 多架构支持（amd64 + arm64），一键部署

#### 企业级功能模块

| 功能模块 | 描述 | 状态 |
|---------|------|------|
| 📊 **批量分析** | 多股票并发分析，智能队列管理，实时进度追踪 | ✅ |
| 🔍 **股票筛选** | 多维度筛选（财务/技术/行业），自定义策略 | ✅ |
| 📈 **个股详情** | 完整信息展示（基本面/技术面/资金面/新闻舆情） | ✅ |
| ⭐ **自选股管理** | 分组管理、标签系统、实时监控、智能提醒 | ✅ |
| 💰 **模拟交易** | 虚拟账户、交易记录、持仓分析、收益统计 | ✅ |

### 🤖 智能分析能力

#### 多智能体分析系统
- **市场分析师**: 技术指标分析（MA、MACD、RSI、BOLL等）
- **基本面分析师**: 财务数据分析（PE、PB、ROE、毛利率等）
- **新闻分析师**: 新闻舆情分析和情感评估
- **风险分析师**: 风险评估和投资建议

#### 多 LLM 提供商支持
- ✅ **OpenAI**: GPT-4、GPT-3.5 系列
- ✅ **Google AI**: Gemini 2.5 Pro/Flash、Gemini 2.0 Flash
- ✅ **DeepSeek**: DeepSeek Chat、DeepSeek Coder
- ✅ **通义千问**: Qwen 系列模型
- ✅ **自定义端点**: 支持任意 OpenAI 兼容 API

#### 多数据源集成
- 🆕 **TDX（通达信）**: 默认数据源，完全免费，实时行情
- ✅ **Tushare**: 专业金融数据，需 API Key
- ✅ **AKShare**: 免费开源数据源
- ✅ **BaoStock**: 备用数据源

### 🌍 多市场支持

| 市场 | 数据源 | 财务指标 | 技术指标 | 状态 |
|------|--------|---------|---------|------|
| 🇨🇳 **A股** | TDX/AKShare/Tushare | ✅ 完整 | ✅ 完整 | ✅ |
| 🇭🇰 **港股** | 新浪财经 | ✅ PE/PB/ROE | ✅ MA/MACD/RSI/BOLL | ✅ |
| 🇺🇸 **美股** | 统一接口 | ✅ 完整 | ✅ 完整 | ✅ |

### 📊 数据质量保障

- ✅ **毛利率字段修复**: 使用正确的 `grossprofit_margin` 字段
- ✅ **亏损股PE计算**: 3层降级策略，正确显示 N/A
- ✅ **技术指标统一**: RSI 标准化（支持国际标准和中国风格）
- ✅ **数据一致性**: 统一的数据获取流程和验证机制

---

## 🚀 快速开始

### 方式一：Docker 部署（推荐）⭐

```bash
# 克隆仓库
git clone <repository-url>
cd tradingagents_cn

# 启动服务（包含前端、后端、MongoDB、Redis）
docker-compose up -d

# 访问应用
# 前端: http://localhost:80
# 后端API: http://localhost:8000
```

📖 **详细文档**: [Docker 部署指南](./docs/deployment/)

### 方式二：Windows 安装程序

1. 下载最新版本的安装程序
2. 双击运行，按向导完成安装
3. 启动应用，开始使用

📖 **详细文档**: [打包可执行应用程序指南](./docs/打包可执行应用程序指南.md)

### 方式三：源码安装

```bash
# 1. 克隆仓库
git clone <repository-url>
cd tradingagents_cn

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置 MongoDB、Redis、LLM API Key 等

# 4. 启动后端
python -m app.main

# 5. 启动前端（新终端）
cd frontend
npm install
npm run dev
```

📖 **详细文档**: [源码安装手册](./docs/deployment/)

---

## 📥 部署方式对比

| 部署方式 | 适用场景 | 难度 | 文档链接 |
|---------|---------|------|---------|
| 🐳 **Docker版** | 生产环境、跨平台 | ⭐⭐ 中等 | [Docker 部署指南](./docs/deployment/) |
| 📦 **安装程序版** | Windows 用户、正式部署 | ⭐ 简单 | [打包指南](./docs/打包可执行应用程序指南.md) |
| 🟢 **绿色版** | Windows 用户、快速体验 | ⭐ 简单 | [部署文档](./docs/deployment/) |
| 💻 **源码版** | 开发者、定制需求 | ⭐⭐⭐ 较难 | [源码安装](./docs/deployment/) |

⚠️ **重要提醒**: 在分析股票之前，请按相关文档要求完成股票数据同步，否则分析结果可能出现数据错误。

---

## 📚 使用指南

### 文档中心

- 📘 [使用指南](./docs/usage/)
- 🐳 [Docker Compose 部署（完全版）](./docs/deployment/)
- 🔄 [从 Docker Hub 更新镜像](./docs/deployment/)
- 🟢 [安装和升级指南](./docs/deployment/)
- ⚙️ [端口配置说明](./docs/configuration/)

### 配置指南

- 🔑 [环境变量配置指南](./docs/configuration/环境变量配置指南.md)
- 🗄️ [MongoDB 配置说明](./docs/configuration/MongoDB配置说明.md)
- 📊 [数据源配置指南](./docs/guides/tdx_datasource_configuration.md)
- 🤖 [LLM 提供商配置](./docs/llm/)

---

## 🆚 相比原版的增强特性

### 中文优化
- ✅ 完整的中文界面和文档
- ✅ 中文股票市场深度支持（A股/港股）
- ✅ 国产 LLM 集成（通义千问、DeepSeek等）

### 功能增强
- ✅ **智能新闻分析**: 多层次新闻过滤和质量评估
- ✅ **多 LLM 提供商**: 支持 4+ 提供商，60+ 模型
- ✅ **模型选择持久化**: 记住用户偏好，快速切换
- ✅ **实时进度显示**: WebSocket 实时推送分析进度
- ✅ **专业报告导出**: Markdown/Word/PDF 多格式导出
- ✅ **Web 配置界面**: 可视化配置管理，无需编辑文件

### 技术架构
- ✅ **FastAPI + Vue 3**: 现代化前后端分离架构
- ✅ **MongoDB + Redis**: 双数据库架构，性能提升 10 倍
- ✅ **Docker 多架构**: 支持 x86_64 和 ARM64
- ✅ **统一配置管理**: pydantic-settings + 结构化日志

---

## 📈 版本历史

### v1.0.0-preview (2025-10-XX) - 当前版本 🚀

**重大更新**:
- 🏗️ FastAPI + Vue 3 全新架构
- 📊 批量分析、股票筛选、个股详情、自选股管理、模拟交易
- 🌍 多市场支持增强（港股数据完善）
- 📊 数据质量重大修复（毛利率字段、亏损股PE计算）
- 🔧 技术指标统一（RSI标准化）

### v0.1.13 (2025-08-02)

- 🤖 原生 OpenAI 端点支持
- 🧠 Google AI 生态系统全面集成
- 🔧 LLM 适配器架构优化

### v0.1.12 (2025-07-29)

- 🧠 智能新闻分析模块
- 📁 项目结构优化

### v0.1.11 (2025-07-27)

- 🤖 多 LLM 提供商集成
- 💾 模型选择持久化

📋 **完整更新日志**: [CHANGELOG.md](./docs/releases/CHANGELOG.md)

---

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 贡献类型

- 🐛 **Bug 修复**: 发现并修复问题
- ✨ **新功能**: 添加新的功能特性
- 📚 **文档改进**: 完善文档和教程
- 🌐 **本地化**: 翻译和本地化工作
- 🎨 **代码优化**: 性能优化和代码重构

### 贡献流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

📋 **查看贡献者**: [贡献者名单](CONTRIBUTORS.md)

---

## 📄 许可证

本项目采用**混合许可证**模式：

### 🔓 开源部分（Apache 2.0）

**适用范围**: 除 `app/` 和 `frontend/` 外的所有文件

- ✅ 商业使用
- ✅ 修改分发
- ✅ 私人使用
- ✅ 专利使用

**条件**: 保留版权声明 | 包含许可证副本

### 🔒 专有部分（需商业授权）

**适用范围**: `app/`（FastAPI后端）和 `frontend/`（Vue前端）目录

- ✅ **个人学习/研究**: 完全免费
- ✅ **源代码可见**: 公开可见
- ❌ **商业使用**: 需要单独许可协议
- 📧 **商业授权**: hsliup@163.com

📖 **详细说明**: [LICENSING.md](LICENSING.md)

---

## 🙏 致谢

### 🌟 向源项目致敬

感谢 [Tauric Research](https://github.com/TauricResearch) 团队创造的革命性多智能体交易框架 [TradingAgents](https://github.com/TauricResearch/TradingAgents)！

- 🎯 **愿景领导者**: AI金融领域的前瞻性思考和创新实践
- 💎 **珍贵源码**: 凝聚智慧的开源代码
- 🏗️ **架构大师**: 优雅、可扩展的多智能体框架
- 💡 **技术先驱**: 前沿AI技术与金融实务的完美结合

### 🤝 社区贡献者

感谢所有为 TradingAgents-CN 项目做出贡献的开发者和用户！

📋 **详细名单**: [贡献者名单](CONTRIBUTORS.md)

---

## ⚠️ 风险提示

**重要声明**: 本框架仅用于研究和教育目的，不构成投资建议。

- 📊 交易表现可能因多种因素而异
- 🤖 AI 模型的预测存在不确定性
- 💰 投资有风险，决策需谨慎
- 👨‍💼 建议咨询专业财务顾问

---

<div align="center">

**🌟 如果这个项目对您有帮助，请给我们一个 Star！**

[📖 Read the docs](./docs/)

Made with ❤️ by TradingAgents-CN Team

</div>
