# AI PCB 设计助手

基于大模型与知识图谱驱动的 PCB 设计 + 仿真一体化自动化插件。

## 功能特性

- 🤖 **AI 智能对话**：基于大模型（智谱 GLM/OpenAI），支持多轮对话
- 🎯 **AI 自动布局**：根据元器件连接关系自动优化 PCB 布局
- 📊 **电路仿真**：支持 DC / AC / 瞬态仿真
- 🔍 **电路分析**：智能分析原理图连接关系，提供设计建议
- 💾 **会话保存**：聊天记录本地持久化

## 环境要求

- 嘉立创 EDA 专业版 v2.3.0+
- Node.js 20.5.0+
- Python 3.11+（用于后端服务）

##工程结构：

ai-pcb-agent/

├── eda-plugin/          # 嘉立创EDA插件（TS/JS）

│   ├── extension.json   # 官方必填配置（UUID/版本/入口）

│   ├── src/

│   │   ├── index.ts     # 插件入口（注册面板/API）

│   │   ├── panel.html   # UI面板

│   │   ├── eda-api.ts  # 封装嘉立创pro-api

│   │   └── agent-client.ts # 调用后端Agent

│   └── package.json

├── agent-backend/       # Python后端（FastAPI）

│   ├── main.py

│   ├── llm/             # 大模型调用

│   ├── kg/              # 硬件知识图谱

│   ├── multisim/        # Multisim COM自动化

│   └── netlist/         # 网表转换

└── docs/                # PRD/API文档

## 安装步骤

### 1. 安装前端依赖

```bash
cd eda-plugin
npm install
```

### 2. 编译插件

```bash
npm run compile
```

### 3. 安装插件

在嘉立创 EDA 专业版中：
1. 点击菜单「扩展」→「加载扩展」
2. 选择编译生成的 `build/dist/*.eext` 文件

### 4. 启动后端服务

```bash
cd agent-backend
pip install -r requirements.txt
python main.py
```

### 5. 配置大模型 API

在 `agent-backend/.env` 文件中配置智谱 API：

```
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
OPENAI_API_KEY=your-api-key
LLM_MODEL=select-model
```

## 使用方法

1. 打开嘉立创 EDA 专业版
2. 点击菜单「AI PCB助手」→「打开 AI 助手面板」
3. 在右侧面板中：
   - **智能对话**：输入问题，获取 PCB 设计建议
   - **PCB 布局**：点击「开始 AI 自动布局」
   - **电路仿真**：配置仿真参数并运行

## 菜单功能

- 打开 AI 助手面板
- AI 自动布局（在 PCB 文档中）
- 运行仿真（在原理图文档中）

## 技术架构

- 前端：TypeScript + 嘉立创 Pro API SDK
- 后端：Python Flask + 智谱 GLM 大模型
- 通信：HTTP REST API

## 开源许可

Apache License 2.0
