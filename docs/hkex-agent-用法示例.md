# HKEX Agent 用法示例

## 命令行界面使用

### 1. 启动 HKEX Agent

```bash
# 使用默认配置启动
hkex

# 指定特定的代理
hkex --agent my-research-agent

# 启用自动批准模式（工具执行无需确认）
hkex --auto-approve
```

### 2. 基本命令

```bash
# 查看帮助
hkex help

# 列出所有可用的代理
hkex list

# 重置代理到默认状态
hkex reset --agent my-agent

# 从另一个代理复制配置
hkex reset --agent new-agent --target existing-agent
```

## 交互式使用示例

### 示例 1：分析港交所公告

```
> 搜索腾讯控股的最新公告

> 下载公告 PDF 并分析内容

> 生成这份公告的摘要

> 分析公告中的财务数据

> 评估这份公告对股价的影响
```

### 示例 2：股票信息查询

```
> 查询腾讯控股(0700.HK)的基本信息

> 获取腾讯控股的最新公告列表

> 分析腾讯控股过去一个月的公告趋势

> 比较腾讯和阿里巴巴的最新财务数据
```

### 示例 3：PDF 文档处理

```
> 下载港交所公告编号为 HKEX-2024-12345 的 PDF

> 解析这个 PDF 文件的内容

> 提取 PDF 中的关键财务指标

> 生成结构化的数据摘要

> 将摘要保存为 Markdown 文件
```

## 高级功能

### 斜杠命令

在交互模式中，可以使用以下斜杠命令：

```bash
/help          # 显示帮助信息
/status        # 查看当前状态
/clear         # 清除屏幕
/memory        # 查看记忆存储
/tools         # 列出可用工具
/export        # 导出对话历史
```

### Bash 命令

使用感叹号 `!` 执行系统命令：

```bash
!ls -la        # 列出当前目录文件
!pwd           # 显示当前目录
!python script.py  # 运行Python脚本
```

### 快捷键

- `Enter`: 提交输入
- `Alt+Enter`: 插入新行
- `Ctrl+E`: 打开编辑器
- `Ctrl+T`: 切换自动批准模式
- `Ctrl+C`: 中断当前操作

## 编程接口使用

### 基础用法

```python
import asyncio
from src.cli.main import main
from src.cli.config import SessionState

# 创建会话状态
session_state = SessionState(auto_approve=False)

# 运行代理
asyncio.run(main("my-agent", session_state))
```

### 自定义工具集成

```python
from src.cli.agent import create_agent_with_config
from src.cli.config import create_model
from src.tools.hkex_tools import (
    search_hkex_announcements,
    get_latest_hkex_announcements,
    download_announcement_pdf
)

# 创建模型
model = create_model()

# 自定义工具列表
tools = [
    search_hkex_announcements,
    get_latest_hkex_announcements,
    download_announcement_pdf,
    # 添加更多自定义工具
]

# 创建代理
agent = create_agent_with_config(model, "my-agent", tools)

# 使用代理进行查询
result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "搜索腾讯控股的最新公告"
    }]
})
```

## 环境配置

### 必需的环境变量

```bash
# SiliconFlow API (推荐)
SILICONFLOW_API_KEY=your_api_key_here
SILICONFLOW_MODEL=deepseek-ai/DeepSeek-V3.1-Terminus

# 或者使用 OpenAI
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o

# 或者使用 Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_key_here
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

### 可选配置

```bash
# UI 配置
HKEX_ASCII_FONT=slant      # ASCII 横幅字体
HKEX_RAINBOW=true          # 启用彩虹效果

# 模型参数
SILICONFLOW_TEMPERATURE=0.7
SILICONFLOW_MAX_TOKENS=20000
```

## 使用场景示例

### 场景 1：投资研究

```bash
# 启动代理
hkex --agent investment-research

# 交互查询
> 搜索香港交易所所有金融股的最新公告
> 分析这些公告中关于分红政策的信息
> 生成一份关于金融股分红趋势的报告
> 重点关注股息率超过5%的公司
```

### 场景 2：合规监控

```bash
# 启动代理
hkex --agent compliance-monitor

# 交互查询
> 监控所有监管相关的公告
> 筛选出需要合规审查的重要公告
> 生成合规风险评估报告
> 标记需要人工审核的公告
```

### 场景 3：市场分析

```bash
# 启动代理
hkex --agent market-analysis

# 交互查询
> 分析科技股的最新业绩公告
> 比较不同公司的营收增长率
> 预测科技板块的短期趋势
> 生成市场分析报告
```

## 文件存储结构

HKEX Agent 的数据存储在以下位置：

```
~/.hkex-agent/
├── {agent_name}/          # 特定代理的数据
│   ├── memories/          # 对话记忆
│   │   └── agent.md       # 代理配置和记忆
│   └── pdf_cache/         # PDF 文件缓存
└── ...                    # 其他代理数据
```

## 故障排除

### 常见问题

1. **API 密钥错误**
   ```bash
   export SILICONFLOW_API_KEY=your_correct_api_key
   ```

2. **网络连接问题**
   - 检查网络连接
   - 确认 API 服务可用性

3. **PDF 解析失败**
   - 确认 PDF 文件可访问
   - 检查文件格式是否正确

4. **记忆存储问题**
   ```bash
   # 重置代理记忆
   hkex reset --agent problematic-agent
   ```

### 调试模式

```bash
# 启用详细日志
export HKEX_DEBUG=true
hkex --agent debug-agent
```

## 性能优化建议

1. **缓存管理**：定期清理 PDF 缓存以节省存储空间
2. **批量处理**：一次性处理多个公告以提高效率
3. **自动批准**：对于批量任务使用 `--auto-approve` 模式
4. **模型选择**：根据任务复杂度选择合适的模型

---

更多详细信息请参考项目 README.md 文档。