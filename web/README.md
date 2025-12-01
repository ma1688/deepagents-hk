# HKEX Agent Web Frontend

港股智能分析系统 Web 界面 - 现代化的毛玻璃风格设计。

## 技术栈

### 后端
- **FastAPI** - 异步 Web 框架
- **PostgreSQL** - 数据库
- **SQLAlchemy 2.0** - 异步 ORM
- **Alembic** - 数据库迁移
- **WebSocket** - 流式响应

### 前端
- **React 18** + **TypeScript**
- **Vite** - 构建工具
- **Zustand** - 状态管理
- **Lucide React** - 图标库
- **React Markdown** - Markdown 渲染

## 快速开始

### 1. 启动 PostgreSQL

```bash
cd web
docker-compose up -d
```

### 2. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 3. 初始化数据库

```bash
cd web
alembic upgrade head
```

### 4. 启动后端服务

```bash
cd web
uvicorn backend.main:app --reload --port 8000
```

### 5. 安装前端依赖

```bash
cd web/frontend
npm install
```

### 6. 启动前端开发服务器

```bash
cd web/frontend
npm run dev
```

访问 http://localhost:5173

## 环境变量

创建 `.env` 文件在项目根目录：

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://hkex:hkex_secret_2024@localhost:5432/hkex_agent

# API 密钥加密
ENCRYPTION_KEY=your-secret-encryption-key

# CORS 配置
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# 模型配置（可选，用户也可在界面中配置）
SILICONFLOW_API_KEY=your-api-key
```

## 功能特性

### 对话交互
- WebSocket 流式输出
- Markdown 渲染 + 代码高亮
- 自动保存对话历史

### 模型配置
- 支持 SiliconFlow / OpenAI / Anthropic
- 多模型切换
- Temperature / MaxTokens 调节
- API 密钥加密存储

### 对话历史
- 会话管理（新建/删除/重命名）
- 完整消息恢复
- PostgreSQL 持久化

### Token 监控
- 实时使用量统计
- 每日/每月统计图表
- 费用估算

### 公告搜索
- 股票代码搜索
- 日期范围筛选
- 结果缓存（24小时）

## API 文档

启动后端后访问：http://localhost:8000/docs

## 项目结构

```
web/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── routes/
│   │   ├── chat.py          # 对话 API
│   │   ├── config.py        # 配置 API
│   │   ├── history.py       # 历史 API
│   │   └── search.py        # 搜索 API
│   ├── db/
│   │   ├── database.py      # 数据库连接
│   │   ├── models.py        # ORM 模型
│   │   └── crud.py          # CRUD 操作
│   ├── models/
│   │   └── schemas.py       # Pydantic 模型
│   └── services/
│       └── agent_service.py # Agent 服务封装
├── frontend/
│   ├── src/
│   │   ├── components/      # React 组件
│   │   ├── stores/          # Zustand 状态
│   │   ├── hooks/           # 自定义 Hooks
│   │   ├── api/             # API 客户端
│   │   ├── types/           # TypeScript 类型
│   │   └── styles/          # 全局样式
│   └── package.json
├── alembic/                  # 数据库迁移
├── docker-compose.yml        # PostgreSQL 容器
└── requirements.txt          # 后端依赖
```

## 设计风格

毛玻璃现代风格 (Glass Morphism):
- 深色渐变背景 (`#0f0f23` → `#1a1a3e`)
- 毛玻璃效果 (`backdrop-filter: blur(20px)`)
- 蓝紫渐变主色 (`#6366f1` → `#8b5cf6`)
- 边框发光效果
- 平滑过渡动画

