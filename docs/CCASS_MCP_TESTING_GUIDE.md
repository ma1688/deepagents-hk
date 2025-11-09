# 🧪 CCASS MCP 集成测试指南

本文档提供 CCASS MCP Server 集成的完整测试流程和验证方法。

---

## 📋 测试前准备

### 1. 确认分支

```bash
# 确认当前在功能分支
cd /Users/ericp/PycharmProjects/deepagents-hk
git branch
# 应该显示: * feature/ccass-mcp-integration
```

### 2. 安装依赖

```bash
# 方式 1：使用 uv (推荐)
uv sync

# 方式 2：使用 pip
pip install langchain-mcp-adapters
```

### 3. 验证配置文件

```bash
# 检查 mcp_config.json 是否存在
cat mcp_config.json

# 预期输出：
# {
#   "mcpServers": {
#     "ccass": {
#       "type": "sse",
#       "url": "http://1.14.239.79:6008/mcp",
#       ...
#     }
#   }
# }
```

### 4. 测试 CCASS MCP Server 连接

```bash
# 测试 MCP Server 是否可访问
curl -I http://1.14.239.79:6008/mcp

# 预期输出：
# HTTP/1.1 200 OK
# Content-Type: text/event-stream
# ...
```

---

## 🧪 测试场景

### 场景 1：MCP 禁用模式（默认）

**目的**：验证向后兼容性，确保不影响现有功能

**步骤**：

1. **不设置 ENABLE_MCP 环境变量**（默认 false）

```bash
# 确保 ENABLE_MCP 未设置或为 false
unset ENABLE_MCP
# 或
export ENABLE_MCP=false
```

2. **启动 Agent**

```bash
hkex
```

3. **预期输出**

```
 _   _ _  ________ __  __            _                 _   
| | | | |/ /  ____\ \/ /           / \   __ _  ___ _ __ | |_ 
| |_| | ' /| |__   \  /   _____   / _ \ / _` |/ _ \ '_ \| __|
|  _  | . \|  __|  /  \  |_____| / ___ \ (_| |  __/ | | | |_ 
|_| |_|_|\_\_____| /_/\_\        /_/   \_\__, |\___|_| |_|\__|
                                         |___/                

🤖 HKEX Agent v1.0.0
📊 模型: deepseek-ai/DeepSeek-V3.1-Terminus
🎨 字体: slant | 🌈 彩虹模式: 启用

HKEX Agent> _
```

**验证点**：
- ✅ Agent 正常启动
- ✅ **没有** "已加载 X 个 MCP 工具" 的提示
- ✅ 只有 HKEX 工具可用

4. **测试现有功能**

```bash
HKEX Agent> 00700 最新中期报告的摘要
```

**预期结果**：
- ✅ 正常查询港交所公告
- ✅ 正常下载 PDF
- ✅ 正常提取内容
- ✅ 正常生成摘要

5. **退出 Agent**

```bash
HKEX Agent> 退出
```

**测试结果**：
- [ ] ✅ 通过
- [ ] ❌ 失败（请记录错误信息）

---

### 场景 2：MCP 启用模式（CCASS 工具加载）

**目的**：验证 CCASS MCP Server 集成，确保工具正确加载

**步骤**：

1. **设置 ENABLE_MCP 环境变量**

```bash
export ENABLE_MCP=true
```

2. **启动 Agent**

```bash
hkex
```

3. **预期输出**

```
 _   _ _  ________ __  __            _                 _   
| | | | |/ /  ____\ \/ /           / \   __ _  ___ _ __ | |_ 
| |_| | ' /| |__   \  /   _____   / _ \ / _` |/ _ \ '_ \| __|
|  _  | . \|  __|  /  \  |_____| / ___ \ (_| |  __/ | | | |_ 
|_| |_|_|\_\_____| /_/\_\        /_/   \_\__, |\___|_| |_|\__|
                                         |___/                

🤖 HKEX Agent v1.0.0
📊 模型: deepseek-ai/DeepSeek-V3.1-Terminus
🎨 字体: slant | 🌈 彩虹模式: 启用

✅ 已加载 5 个 MCP 工具
   - get_broker_holdings: 获取指定股票的券商持仓数据
   - get_ownership_concentration: 获取股权集中度分析
   - get_trend_analysis: 获取持仓趋势分析
   - get_top_brokers: 获取持仓最多的券商列表
   - get_broker_changes: 获取券商持仓变化

HKEX Agent> _
```

**验证点**：
- ✅ Agent 正常启动
- ✅ **显示** "已加载 5 个 MCP 工具" 的提示
- ✅ 列出所有 CCASS MCP 工具名称和描述
- ✅ HKEX 工具 + CCASS 工具都可用

4. **测试 CCASS MCP 工具**

**测试 1：查询券商持仓**

```bash
HKEX Agent> 00700 的券商持仓数据
```

**预期结果**：
- ✅ Agent 识别到需要使用 `get_broker_holdings` 工具
- ✅ 调用 CCASS MCP Server
- ✅ 返回券商持仓数据（表格格式）
- ✅ 包含券商代码、名称、持仓股数、持仓比例等信息

**测试 2：股权集中度分析**

```bash
HKEX Agent> 分析 00700 的股权集中度
```

**预期结果**：
- ✅ Agent 识别到需要使用 `get_ownership_concentration` 工具
- ✅ 调用 CCASS MCP Server
- ✅ 返回股权集中度数据
- ✅ 包含前 10/20/50 大券商持仓占比、赫芬达尔指数等

**测试 3：综合分析（HKEX + CCASS）**

```bash
HKEX Agent> 00700 最新中期报告的摘要，并分析券商持仓变化
```

**预期结果**：
- ✅ Agent 调用 HKEX 工具（查询公告、下载 PDF、提取内容）
- ✅ Agent 调用 CCASS MCP 工具（查询券商持仓变化）
- ✅ 生成综合分析报告（财务 + 持仓）

5. **退出 Agent**

```bash
HKEX Agent> 退出
```

**测试结果**：
- [ ] ✅ 通过
- [ ] ❌ 失败（请记录错误信息）

---

### 场景 3：MCP Server 不可用（错误处理）

**目的**：验证 MCP Server 不可用时的降级处理

**步骤**：

1. **修改 mcp_config.json 使用错误的 URL**

```bash
# 备份原配置
cp mcp_config.json mcp_config.json.bak

# 修改为错误的 URL
cat > mcp_config.json << 'EOF'
{
  "mcpServers": {
    "ccass": {
      "type": "sse",
      "url": "http://invalid-url:9999/mcp",
      "description": "CCASS数据分析MCP服务器",
      "name": "ccass-mcp-server",
      "baseUrl": "http://invalid-url:9999/mcp",
      "isActive": true
    }
  }
}
EOF
```

2. **设置 ENABLE_MCP=true 并启动 Agent**

```bash
export ENABLE_MCP=true
hkex
```

3. **预期输出**

```
🤖 HKEX Agent v1.0.0
📊 模型: deepseek-ai/DeepSeek-V3.1-Terminus
🎨 字体: slant | 🌈 彩虹模式: 启用

⚠️  MCP 工具加载失败: [Errno 61] Connection refused
Traceback (most recent call last):
  ...
  ConnectionRefusedError: [Errno 61] Connection refused

HKEX Agent> _
```

**验证点**：
- ✅ Agent 仍然正常启动（降级处理）
- ✅ 显示 MCP 工具加载失败的警告
- ✅ 打印详细错误信息（traceback）
- ✅ HKEX 工具仍然可用

4. **测试现有功能**

```bash
HKEX Agent> 00700 最新中期报告的摘要
```

**预期结果**：
- ✅ HKEX 工具正常工作
- ✅ 不影响基本功能

5. **恢复原配置**

```bash
mv mcp_config.json.bak mcp_config.json
```

**测试结果**：
- [ ] ✅ 通过
- [ ] ❌ 失败（请记录错误信息）

---

## 📊 测试结果记录

### 测试环境

- **操作系统**：macOS 25.1.0
- **Python 版本**：3.13
- **分支**：feature/ccass-mcp-integration
- **Commit**：345d6a2

### 测试结果汇总

| 场景 | 测试项 | 结果 | 备注 |
|------|--------|------|------|
| 场景 1 | Agent 启动 | [ ] | |
| 场景 1 | 无 MCP 工具提示 | [ ] | |
| 场景 1 | HKEX 工具正常 | [ ] | |
| 场景 2 | Agent 启动 | [ ] | |
| 场景 2 | MCP 工具加载 | [ ] | |
| 场景 2 | 券商持仓查询 | [ ] | |
| 场景 2 | 股权集中度分析 | [ ] | |
| 场景 2 | 综合分析 | [ ] | |
| 场景 3 | 错误处理 | [ ] | |
| 场景 3 | 降级处理 | [ ] | |

### 问题记录

**问题 1**：
- **场景**：
- **现象**：
- **错误信息**：
- **解决方案**：

**问题 2**：
- **场景**：
- **现象**：
- **错误信息**：
- **解决方案**：

---

## 🐛 常见问题

### 问题 1：`ModuleNotFoundError: No module named 'langchain_mcp_adapters'`

**原因**：未安装 `langchain-mcp-adapters` 依赖

**解决方案**：
```bash
uv sync
# 或
pip install langchain-mcp-adapters
```

### 问题 2：`Connection refused` 错误

**原因**：CCASS MCP Server 不可访问

**排查步骤**：
1. 测试 MCP Server 连接：
   ```bash
   curl -I http://1.14.239.79:6008/mcp
   ```
2. 检查网络连接
3. 确认 MCP Server 是否运行

### 问题 3：Agent 启动慢

**原因**：MCP 客户端初始化需要时间

**正常行为**：
- MCP 禁用：启动快（< 2 秒）
- MCP 启用：启动慢（5-10 秒，需要连接 MCP Server）

### 问题 4：MCP 工具未加载

**排查步骤**：
1. 确认 `ENABLE_MCP=true`
2. 检查 `mcp_config.json` 配置
3. 查看错误日志（traceback）

---

## ✅ 测试通过标准

### 场景 1（MCP 禁用）

- [ ] Agent 正常启动
- [ ] 无 MCP 工具加载提示
- [ ] HKEX 工具正常工作
- [ ] 查询公告功能正常
- [ ] PDF 下载和提取正常
- [ ] 摘要生成正常

### 场景 2（MCP 启用）

- [ ] Agent 正常启动
- [ ] 显示 MCP 工具加载提示
- [ ] 列出所有 CCASS MCP 工具
- [ ] 券商持仓查询成功
- [ ] 股权集中度分析成功
- [ ] 综合分析成功（HKEX + CCASS）

### 场景 3（错误处理）

- [ ] Agent 正常启动（降级）
- [ ] 显示 MCP 加载失败警告
- [ ] 打印详细错误信息
- [ ] HKEX 工具仍然可用

---

## 📝 测试完成后

### 1. 填写测试结果

在 "测试结果汇总" 表格中填写测试结果（✅ 或 ❌）

### 2. 记录问题

在 "问题记录" 部分记录遇到的问题和解决方案

### 3. 反馈测试结果

将测试结果反馈给开发者：
- 所有测试通过：继续 Phase 4（文档更新）
- 部分测试失败：修复问题后重新测试

---

## 📞 联系方式

如有问题，请反馈：
- **GitHub Issues**: [https://github.com/HK-CCASS/deepagents-hk/issues](https://github.com/HK-CCASS/deepagents-hk/issues)
- **Email**: your-email@example.com

---

**🎉 祝测试顺利！**

