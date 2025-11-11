# SqliteSaver 功能测试指南

## 测试环境

- **分支**：`feature/sqlite-checkpointer`
- **Python版本**：3.11+
- **依赖**：已安装 `langgraph-checkpoint-sqlite==3.0.0`

## 快速测试

### 1. 基础功能测试

#### 测试 1.1：首次启动（无历史）

```bash
# 启动程序
source .venv/bin/activate
hkex

# 预期结果：
- 程序正常启动
- 显示欢迎界面
- 无历史对话加载
```

#### 测试 1.2：对话持久化

```bash
# 在 hkex CLI 中：
用户> 查询00700的最新公告

# 等待 Agent 回复后，关闭程序
用户> /quit

# 检查数据库文件是否创建
ls -lh ~/.hkex-agent/default/checkpoints.db

# 预期结果：
- 数据库文件存在
- 文件大小 > 0 KB
```

#### 测试 1.3：自动继续对话

```bash
# 重新启动程序
hkex

# 输入新消息（无需重复上下文）
用户> 继续分析

# 预期结果：
- Agent 记得之前的 00700 查询
- 能够基于上次对话继续分析
- 无需重新说明背景
```

### 2. /clear 命令测试

#### 测试 2.1：创建新对话

```bash
# 在 hkex CLI 中：
用户> /clear

# 预期结果：
- 屏幕清空
- 显示 "Fresh start! New conversation started."
- 显示提示：使用 /history 查看历史
```

#### 测试 2.2：新对话独立性

```bash
# /clear 后
用户> 你好

# 预期结果：
- Agent 不记得之前的对话
- 开始新的对话线程
```

#### 测试 2.3：历史数据保留

```bash
# 检查数据库
ls -lh ~/.hkex-agent/default/checkpoints.db

# 预期结果：
- 数据库文件仍然存在
- 文件大小增加（包含多个 thread）
```

### 3. /history 命令测试

#### 测试 3.1：查看历史状态

```bash
# 在 hkex CLI 中：
用户> /history

# 预期结果：
- 显示 "Conversation History"
- 显示数据库路径
- 显示提示：完整查看功能待实现
```

### 4. 上下文恢复测试

#### 测试 4.1：长对话恢复

```bash
# 第一次会话
用户> 分析00700
用户> 查看财务数据
用户> 对比去年
[关闭程序]

# 重新启动
hkex
用户> 总结一下

# 预期结果：
- Agent 能够总结之前的所有分析
- 上下文完整保留
```

#### 测试 4.2：跨多次重启

```bash
# Day 1
用户> 查询00700
[关闭]

# Day 2
用户> 继续分析
[关闭]

# Day 3
用户> 生成报告

# 预期结果：
- 所有历史对话保留
- 能够基于多天的对话生成报告
```

## 高级测试

### 5. 性能测试

#### 测试 5.1：启动加载时间

```bash
# 使用 time 命令测试
time (echo "测试" | hkex)

# 预期结果：
- 启动时间 < 5 秒
- 加载历史延迟 < 100ms
```

#### 测试 5.2：大量对话

```bash
# 进行 50+ 轮对话
for i in {1..50}; do
    echo "消息 $i"
done

# 关闭并重启
# 检查性能

# 预期结果：
- 启动时间仍然 < 5 秒
- 对话响应正常
```

### 6. 边界情况测试

#### 测试 6.1：数据库不存在

```bash
# 删除数据库
rm ~/.hkex-agent/default/checkpoints.db

# 启动程序
hkex

# 预期结果：
- 程序正常启动
- 自动创建新数据库
- 无错误信息
```

#### 测试 6.2：数据库损坏

```bash
# 备份数据库
cp ~/.hkex-agent/default/checkpoints.db ~/.hkex-agent/default/checkpoints.db.bak

# 损坏数据库（写入随机数据）
echo "corrupted" > ~/.hkex-agent/default/checkpoints.db

# 启动程序
hkex

# 预期结果：
- 程序能够处理错误
- 显示友好的错误消息
- 或自动创建新数据库
```

#### 测试 6.3：多次快速 /clear

```bash
# 在 hkex CLI 中：
用户> /clear
用户> /clear
用户> /clear

# 预期结果：
- 每次创建新 thread_id
- 无错误信息
- 数据库正常工作
```

### 7. 集成测试

#### 测试 7.1：完整工作流

```bash
# 场景：分析股票公告
1. 启动 hkex
2. 查询00700公告
3. 下载PDF
4. 分析内容
5. /clear
6. 查询另一只股票
7. /quit
8. 重启
9. /history 查看历史
10. 继续上次对话

# 预期结果：
- 所有步骤正常工作
- 数据正确保存和恢复
```

## 测试检查清单

### 基本功能
- [ ] 首次启动无历史
- [ ] 对话自动保存
- [ ] 重启自动恢复
- [ ] /clear 创建新对话
- [ ] /history 显示状态
- [ ] 数据库文件创建

### 对话管理
- [ ] 多轮对话保留
- [ ] 上下文正确恢复
- [ ] 新对话独立
- [ ] 历史数据保留

### 性能指标
- [ ] 启动时间 < 5s
- [ ] 加载延迟 < 100ms
- [ ] 对话响应正常
- [ ] 大量数据无问题

### 边界情况
- [ ] 无数据库处理
- [ ] 损坏数据库处理
- [ ] 多次 /clear 正常
- [ ] 并发访问正常

## 问题报告

如发现问题，请记录：

### 问题模板

```markdown
## 问题描述
[简要描述问题]

## 复现步骤
1. 启动程序
2. 执行操作 X
3. 观察到问题 Y

## 预期行为
[描述预期的正确行为]

## 实际行为
[描述实际观察到的行为]

## 环境信息
- Python 版本：
- OS：
- 分支：feature/sqlite-checkpointer
- 数据库位置：~/.hkex-agent/default/checkpoints.db

## 错误日志
[粘贴相关错误信息]
```

## 性能基准

### 预期性能指标

| 指标 | 目标值 | 实际值 | 状态 |
|------|--------|--------|------|
| 首次启动 | < 3s | | 待测 |
| 加载历史 | < 100ms | | 待测 |
| 对话延迟 | < 50ms | | 待测 |
| 数据库大小（10轮） | ~50KB | | 待测 |
| 数据库大小（100轮） | ~500KB | | 待测 |

## 数据库检查

### 检查数据库内容

```bash
# 使用 sqlite3 查看数据库
sqlite3 ~/.hkex-agent/default/checkpoints.db

# SQL 命令：
.tables              # 查看表
.schema checkpoints  # 查看表结构
SELECT COUNT(*) FROM checkpoints;  # 查看记录数
SELECT thread_id, COUNT(*) FROM checkpoints GROUP BY thread_id;  # 按 thread 统计
```

### 数据库路径

```
位置：~/.hkex-agent/{agent_id}/checkpoints.db

默认：~/.hkex-agent/default/checkpoints.db
```

## 测试完成标准

✅ 所有基本功能测试通过
✅ 所有对话管理测试通过
✅ 性能指标达到预期
✅ 边界情况处理正常
✅ 无严重 bug 或错误

## 下一步

测试通过后：
1. 合并到主分支
2. 更新版本号
3. 发布变更日志
4. 通知用户新功能

测试未通过：
1. 记录问题
2. 修复 bug
3. 重新测试
4. 更新文档

