# 上游改进选择性移植执行方案

**生成时间**: 2025-11-11  
**目标**: 安全移植上游3个有益改进，保留所有 HKEX 功能  
**预计总耗时**: 4-6小时  
**风险等级**: 🟡 中等（可控）

---

## 📋 移植清单

| # | 特性 | Commit | 优先级 | 预计耗时 | 风险 |
|---|------|--------|--------|---------|------|
| 1 | 子代理错误处理优化 | 766c41c | 🔴 高 | 1-2h | 🟢 低 |
| 2 | HITL 并发修复 | 1d9fa2f | 🟡 中 | 2-3h | 🟡 中 |
| 3 | fetch_url 工具 | e63487e | 🟢 低 | 1h | 🟢 低 |

---

## 🎯 移植 1: 子代理错误处理优化

### 背景
**问题**: 当前子代理不存在时抛出 `ValueError`，导致 Agent 崩溃  
**改进**: 改为返回友好错误消息，让 Agent 自行处理  
**影响文件**: `libs/deepagents/middleware/subagents.py`

### 执行步骤

#### 第1步：创建备份

```bash
# 切换到项目根目录
cd /Users/ericp/PycharmProjects/deepagents-hk

# 创建备份分支
git checkout -b backup/before-upstream-merge-2025-11-11
git push origin backup/before-upstream-merge-2025-11-11

# 确认备份成功
git branch -a | grep backup
```

**预期输出**:
```
* backup/before-upstream-merge-2025-11-11
  master
```

#### 第2步：创建特性分支

```bash
# 回到主分支
git checkout master

# 创建特性分支
git checkout -b feature/upstream-subagent-error-handling

# 确认分支
git branch
```

#### 第3步：查看目标改动

```bash
# 查看上游具体改动
git show upstream/master:libs/deepagents/middleware/subagents.py > /tmp/upstream_subagents.py
git show master:libs/deepagents/middleware/subagents.py > /tmp/current_subagents.py

# 对比差异
diff -u /tmp/current_subagents.py /tmp/upstream_subagents.py | grep -A 10 -B 10 "validate_and_prepare_state\|subagent_type not in"
```

**关键差异**:
```diff
# 旧版本（抛出异常）
def _validate_and_prepare_state(...):
-   if subagent_type not in subagent_graphs:
-       msg = f"Error: invoked agent of type {subagent_type}..."
-       raise ValueError(msg)

# 新版本（返回错误消息）
def task(...):
+   if subagent_type not in subagent_graphs:
+       allowed_types = ", ".join([f"`{k}`" for k in subagent_graphs])
+       return f"We cannot invoke subagent {subagent_type}..."
```

#### 第4步：应用改动

```bash
# 尝试 cherry-pick（可能失败）
git cherry-pick 766c41c
```

**预期结果**:
- ✅ **成功**: 无冲突，直接进入第5步
- ⚠️ **冲突**: 需要手动合并，继续下面步骤

#### 第5步：手动合并（如果 cherry-pick 冲突）

打开 `libs/deepagents/middleware/subagents.py`，找到以下函数并修改：

**位置1**: `_validate_and_prepare_state` 函数（约第325行）

```python
# 修改前
def _validate_and_prepare_state(subagent_type: str, description: str, runtime: ToolRuntime) -> tuple[Runnable, dict]:
    """Validate subagent type and prepare state for invocation."""
    if subagent_type not in subagent_graphs:
        msg = f"Error: invoked agent of type {subagent_type}, the only allowed types are {[f'`{k}`' for k in subagent_graphs]}"
        raise ValueError(msg)  # ← 删除这个检查
    subagent = subagent_graphs[subagent_type]
    # ... 其余代码保持不变
```

```python
# 修改后
def _validate_and_prepare_state(subagent_type: str, description: str, runtime: ToolRuntime) -> tuple[Runnable, dict]:
    """Prepare state for invocation."""  # ← 移除 "Validate" 描述
    # ← 删除了 if 检查
    subagent = subagent_graphs[subagent_type]
    # ... 其余代码保持不变
```

**位置2**: `task` 函数（约第344行）

```python
# 在函数开头添加检查
def task(
    description: str,
    subagent_type: str,
    runtime: ToolRuntime,
) -> str | Command:
    # ← 在这里添加新检查
    if subagent_type not in subagent_graphs:
        allowed_types = ", ".join([f"`{k}`" for k in subagent_graphs])
        return f"We cannot invoke subagent {subagent_type} because it does not exist, the only allowed types are {allowed_types}"
    
    # 原有代码
    subagent, subagent_state = _validate_and_prepare_state(subagent_type, description, runtime)
    # ...
```

**位置3**: `async def task` 函数（约第356行）

```python
# 在异步函数开头添加相同检查
async def task(
    description: str,
    subagent_type: str,
    runtime: ToolRuntime,
) -> str | Command:
    # ← 在这里添加新检查
    if subagent_type not in subagent_graphs:
        allowed_types = ", ".join([f"`{k}`" for k in subagent_graphs])
        return f"We cannot invoke subagent {subagent_type} because it does not exist, the only allowed types are {allowed_types}"
    
    # 原有代码
    subagent, subagent_state = _validate_and_prepare_state(subagent_type, description, runtime)
    # ...
```

#### 第6步：解决冲突标记（如果有）

```bash
# 查看冲突文件
git status

# 标记已解决
git add libs/deepagents/middleware/subagents.py

# 完成 cherry-pick
git cherry-pick --continue
```

#### 第7步：测试改动

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行相关测试
pytest libs/deepagents/tests/unit_tests/test_middleware.py -v -k "subagent"

# 运行完整测试套件
pytest libs/deepagents/tests/ -v
```

**预期测试结果**:
```
libs/deepagents/tests/unit_tests/test_middleware.py::test_subagent_error_handling PASSED
libs/deepagents/tests/unit_tests/test_middleware.py::test_subagent_invalid_type PASSED
================================ X passed in X.XXs ================================
```

#### 第8步：功能验证

创建测试脚本 `test_subagent_error.py`:

```python
#!/usr/bin/env python3
"""测试子代理错误处理"""
import asyncio
from src.agents.main_agent import create_hkex_agent
from src.cli.config import create_model

async def test_invalid_subagent():
    """测试调用不存在的子代理"""
    model = create_model()
    agent = await create_hkex_agent(model=model, assistant_id="test")
    
    # 模拟调用不存在的子代理
    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "请使用 invalid-subagent 子代理分析数据"
        }]
    })
    
    # 检查是否友好处理错误
    last_message = result["messages"][-1].content
    print("Agent 响应:", last_message)
    
    # 应该包含错误提示而不是崩溃
    assert "cannot invoke subagent" in last_message.lower() or "不存在" in last_message

if __name__ == "__main__":
    asyncio.run(test_invalid_subagent())
    print("✅ 测试通过：子代理错误处理正常")
```

运行测试:
```bash
python test_subagent_error.py
```

#### 第9步：提交改动

```bash
# 查看改动
git diff HEAD

# 提交
git add libs/deepagents/middleware/subagents.py
git commit -m "feat: improve subagent error handling (from upstream 766c41c)

- Don't raise ValueError when subagent doesn't exist
- Return friendly error message instead
- Allow agent to handle the error gracefully

Cherry-picked from: https://github.com/langchain-ai/deepagents/commit/766c41c"

# 推送到远程
git push origin feature/upstream-subagent-error-handling
```

#### 第10步：合并到主分支

```bash
# 切换到主分支
git checkout master

# 合并特性分支
git merge feature/upstream-subagent-error-handling --no-ff

# 推送到远程
git push origin master

# 删除特性分支（可选）
# git branch -d feature/upstream-subagent-error-handling
```

---

## 🎯 移植 2: HITL 并发修复

### 背景
**问题**: 多个子代理并发请求人工批准时抛出 `RuntimeError`  
**改进**: 正确处理多个待处理中断，按中断ID映射响应  
**影响文件**: `libs/deepagents-cli/deepagents_cli/execution.py`

### ⚠️ 复杂度分析

**冲突风险**: 🟡 **中等偏高**

原因:
1. 您的 `src/cli/execution.py` 是高度定制的 HKEX 实现（670行）
2. 上游修改的是 `libs/deepagents-cli/deepagents_cli/execution.py`
3. 两个文件功能相似但实现不同

### 决策点

**选项A**: 仅修改 `libs/deepagents-cli/`（如果您不使用它）
- ✅ 零冲突
- ⚠️ 您的 HKEX CLI 不受益

**选项B**: 同时修改 `src/cli/execution.py`（手动移植逻辑）
- ✅ HKEX CLI 受益
- ⚠️ 需要理解并适配代码逻辑
- ⏱️ 耗时 2-3 小时

### 执行步骤

#### 第1步：评估是否需要

```bash
# 检查 src/cli/execution.py 是否有多子代理并发场景
grep -n "pending_interrupts\|multiple.*interrupt" src/cli/execution.py

# 检查是否使用 libs/deepagents-cli
grep -n "from deepagents_cli" src/cli/*.py
```

**决策**:
- 如果 **没有** 多子代理并发场景 → **跳过此移植**
- 如果 **有** 并发场景 → 继续下面步骤

#### 第2步：创建特性分支

```bash
git checkout master
git checkout -b feature/upstream-hitl-concurrent-fix
```

#### 第3步：分析上游改动

```bash
# 查看上游详细改动
git show 1d9fa2f
```

**核心改动**:
```python
# 旧版本（单个中断）
pending_hitl_request = state.get("pending_hitl_request")
if pending_hitl_request:
    # 处理单个中断
    response = handle_interrupt(pending_hitl_request)
    agent.update_state(config, {"decisions": [response]})

# 新版本（多个中断）
pending_interrupts = {}
for interrupt_id, interrupt_value in state.get("pending_interrupts", {}).items():
    pending_interrupts[interrupt_id] = interrupt_value

if pending_interrupts:
    responses = {}
    for interrupt_id, interrupt_value in pending_interrupts.items():
        response = handle_interrupt(interrupt_value)
        responses[interrupt_id] = {"decisions": [response]}
    
    # 区分单个和多个中断
    if len(responses) == 1:
        agent.update_state(config, list(responses.values())[0])
    else:
        agent.update_state(config, responses)
```

#### 第4步：决定移植范围

**选项2A**: 只移植到 `libs/deepagents-cli/` (简单)

```bash
# 直接 cherry-pick
git cherry-pick 1d9fa2f

# 测试
cd libs/deepagents-cli
uv sync
uv run pytest tests/ -v
```

**选项2B**: 移植到 `src/cli/execution.py` (复杂)

需要手动分析和适配：

1. 打开 `src/cli/execution.py`
2. 找到 HITL 中断处理逻辑（约第400-500行）
3. 找到类似以下代码:

```python
# 查找类似模式
def handle_tool_approval(self, state):
    """处理工具批准请求"""
    # 当前可能是单中断处理
    pending_request = state.get("pending_request")
    if pending_request:
        # 处理逻辑...
```

4. 参考上游改动，修改为多中断处理:

```python
def handle_tool_approval(self, state):
    """处理工具批准请求（支持并发）"""
    # 收集所有待处理中断
    pending_interrupts = {}
    
    # 根据您的状态结构调整
    for interrupt_id, interrupt_value in state.get("pending_interrupts", {}).items():
        pending_interrupts[interrupt_id] = interrupt_value
    
    if not pending_interrupts:
        return None
    
    # 处理每个中断
    responses = {}
    for interrupt_id, interrupt_value in pending_interrupts.items():
        # 自动批准或手动批准
        if self.auto_approve:
            response = self._auto_approve(interrupt_value)
        else:
            response = self._prompt_user(interrupt_value)
        
        responses[interrupt_id] = {"decisions": [response]}
    
    # 返回响应
    if len(responses) == 1:
        return list(responses.values())[0]
    else:
        return responses
```

#### 第5步：测试（重要！）

创建并发测试脚本 `test_concurrent_hitl.py`:

```python
#!/usr/bin/env python3
"""测试并发 HITL 场景"""
import asyncio
from src.agents.main_agent import create_hkex_agent
from src.cli.config import create_model

async def test_concurrent_subagents():
    """测试多个子代理并发请求批准"""
    model = create_model()
    agent = await create_hkex_agent(model=model, assistant_id="test")
    
    # 模拟3个子代理并发请求
    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "同时分析 00700、00875、03800 三只股票的最新公告"
        }]
    })
    
    print("✅ 并发测试通过：无 RuntimeError")

if __name__ == "__main__":
    asyncio.run(test_concurrent_subagents())
```

```bash
python test_concurrent_hitl.py
```

#### 第6步：提交

```bash
git add src/cli/execution.py  # 或 libs/deepagents-cli/deepagents_cli/execution.py
git commit -m "feat: support concurrent HITL interrupts (from upstream 1d9fa2f)

- Handle multiple pending interrupts correctly
- Map responses by interrupt ID
- Fix RuntimeError when parallel subagents request approval

Cherry-picked from: https://github.com/langchain-ai/deepagents/commit/1d9fa2f"

git push origin feature/upstream-hitl-concurrent-fix
```

#### 第7步：合并

```bash
git checkout master
git merge feature/upstream-hitl-concurrent-fix --no-ff
git push origin master
```

---

## 🎯 移植 3: fetch_url 工具

### 背景
**功能**: 获取网页内容并转换为 markdown  
**用途**: 类似 Claude Code 的 web-fetch 工具  
**影响文件**: 
- `libs/deepagents-cli/deepagents_cli/tools.py`
- `libs/deepagents-cli/pyproject.toml`

### 价值评估

**对 HKEX Agent 的价值**: 🟡 中等

可能的应用场景:
- ✅ 获取港交所网页数据
- ✅ 获取财经新闻分析
- ✅ 补充现有 `web_search` 工具（Tavily只返回片段）

**决策**: 
- 如果需要深度网页内容提取 → 移植
- 如果只需搜索结果片段 → 跳过

### 执行步骤

#### 第1步：创建特性分支

```bash
git checkout master
git checkout -b feature/upstream-fetch-url
```

#### 第2步：应用改动

```bash
# Cherry-pick
git cherry-pick e63487e

# 如果冲突，查看冲突文件
git status
```

#### 第3步：更新依赖

编辑 `pyproject.toml`（根目录）:

```toml
dependencies = [
    # ... 现有依赖
    "markdownify>=0.13.0",  # ← 添加这行
]
```

编辑 `libs/deepagents-cli/pyproject.toml`:

```toml
dependencies = [
    # ... 现有依赖
    "markdownify>=0.13.0",  # ← 已通过 cherry-pick 自动添加
]

[dependency-groups]
test = [
    # ... 现有依赖
    "responses>=0.25.0",  # ← 已通过 cherry-pick 自动添加
]
```

#### 第4步：安装依赖

```bash
# 重新同步依赖
uv sync

# 验证安装
python -c "import markdownify; print('✅ markdownify installed')"
```

#### 第5步：集成到 HKEX Agent

**选项3A**: 作为独立工具（推荐）

在 `src/cli/config.py` 或 `src/agents/main_agent.py` 中添加:

```python
from libs.deepagents-cli.deepagents_cli.tools import fetch_url

# 在创建 Agent 时添加工具
tools = [
    # ... 现有工具
    fetch_url,  # ← 新增
]

agent = create_deep_agent(
    model=model,
    tools=tools,
    # ...
)
```

**选项3B**: 集成到现有工具（可选）

在 `src/tools/hkex_tools.py` 中封装:

```python
from deepagents_cli.tools import fetch_url as _fetch_url

def fetch_hkex_page(url: str) -> dict:
    """获取港交所网页内容（专用）"""
    if "hkexnews.hk" not in url and "hkex.com.hk" not in url:
        return {"error": "仅支持港交所网址"}
    
    return _fetch_url(url, timeout=60)
```

#### 第6步：测试

创建测试脚本 `test_fetch_url.py`:

```python
#!/usr/bin/env python3
"""测试 fetch_url 工具"""
from deepagents_cli.tools import fetch_url

def test_fetch_langchain_docs():
    """测试获取 LangChain 文档"""
    result = fetch_url(
        url="https://docs.langchain.com/oss/python/deepagents/overview",
        timeout=30
    )
    
    assert "error" not in result
    assert "markdown_content" in result
    assert len(result["markdown_content"]) > 0
    print(f"✅ 获取成功：{result['content_length']} 字符")
    print(f"状态码：{result['status_code']}")
    print(f"内容预览：{result['markdown_content'][:200]}...")

def test_fetch_hkex():
    """测试获取港交所页面"""
    result = fetch_url(
        url="https://www.hkex.com.hk/",
        timeout=30
    )
    
    if "error" in result:
        print(f"⚠️  错误：{result['error']}")
    else:
        print(f"✅ 获取成功：{result['content_length']} 字符")

if __name__ == "__main__":
    print("测试 1: LangChain 文档")
    test_fetch_langchain_docs()
    
    print("\n测试 2: 港交所首页")
    test_fetch_hkex()
```

```bash
python test_fetch_url.py
```

#### 第7步：运行单元测试

```bash
cd libs/deepagents-cli
uv run pytest tests/tools/test_fetch_url.py -v
```

#### 第8步：提交

```bash
git add .
git commit -m "feat: add fetch_url tool for web content (from upstream e63487e)

- Fetch web page content and convert to markdown
- Add markdownify dependency
- Add responses for testing

Potential use cases:
- Fetch HKEX web pages
- Get financial news content
- Complement existing web_search tool

Cherry-picked from: https://github.com/langchain-ai/deepagents/commit/e63487e"

git push origin feature/upstream-fetch-url
```

#### 第9步：合并

```bash
git checkout master
git merge feature/upstream-fetch-url --no-ff
git push origin master
```

---

## 📊 移植进度跟踪

### 完成检查清单

#### 移植 1: 子代理错误处理
- [ ] 创建备份分支
- [ ] 创建特性分支 `feature/upstream-subagent-error-handling`
- [ ] Cherry-pick 或手动应用改动
- [ ] 运行单元测试
- [ ] 功能验证测试
- [ ] 提交改动
- [ ] 合并到 master
- [ ] 推送到远程

#### 移植 2: HITL 并发修复
- [ ] 评估是否需要（检查并发场景）
- [ ] 创建特性分支 `feature/upstream-hitl-concurrent-fix`
- [ ] 决定移植范围（仅 libs/ 或也包括 src/）
- [ ] 应用改动
- [ ] 创建并发测试
- [ ] 运行测试
- [ ] 提交改动
- [ ] 合并到 master
- [ ] 推送到远程

#### 移植 3: fetch_url 工具
- [ ] 评估价值（是否需要网页抓取）
- [ ] 创建特性分支 `feature/upstream-fetch-url`
- [ ] Cherry-pick 改动
- [ ] 更新依赖（pyproject.toml）
- [ ] 安装依赖（uv sync）
- [ ] 集成到 HKEX Agent
- [ ] 运行测试
- [ ] 提交改动
- [ ] 合并到 master
- [ ] 推送到远程

---

## 🔧 故障排查

### 问题1: Cherry-pick 冲突

**症状**:
```
error: could not apply 766c41c... fix: Don't error when "subagent" does not exist
hint: after resolving the conflicts, mark the corrected paths
```

**解决**:
```bash
# 查看冲突文件
git status

# 手动编辑冲突文件
# 查找 <<<<<<< HEAD 标记

# 标记已解决
git add <冲突文件>

# 继续 cherry-pick
git cherry-pick --continue
```

### 问题2: 测试失败

**症状**:
```
FAILED libs/deepagents/tests/unit_tests/test_middleware.py::test_subagent_error
```

**解决**:
```bash
# 查看详细错误
pytest libs/deepagents/tests/unit_tests/test_middleware.py -v -s

# 检查代码是否正确应用
git diff master libs/deepagents/middleware/subagents.py

# 对比上游版本
git show upstream/master:libs/deepagents/middleware/subagents.py > /tmp/upstream.py
diff libs/deepagents/middleware/subagents.py /tmp/upstream.py
```

### 问题3: 依赖安装失败

**症状**:
```
ERROR: Could not find a version that satisfies the requirement markdownify>=0.13.0
```

**解决**:
```bash
# 清理缓存
uv cache clean

# 重新同步
uv sync --refresh

# 或手动安装
pip install markdownify>=0.13.0
```

### 问题4: HKEX Agent 不兼容

**症状**:
移植后 `hkex` 命令无法运行

**解决**:
```bash
# 检查导入
python -c "from src.cli.main import cli_main; print('OK')"

# 检查配置
python -c "from src.cli.config import create_model; print(create_model())"

# 回滚到备份分支
git checkout backup/before-upstream-merge-2025-11-11
```

---

## 📈 验收标准

### 移植 1 成功标准
- ✅ 单元测试全部通过
- ✅ 调用不存在的子代理返回友好错误（不崩溃）
- ✅ HKEX Agent 正常工作
- ✅ 没有新增 linter 错误

### 移植 2 成功标准
- ✅ 多子代理并发场景不抛出 RuntimeError
- ✅ HITL 批准流程正常
- ✅ 自动批准模式正常
- ✅ HKEX Agent 正常工作

### 移植 3 成功标准
- ✅ `fetch_url` 工具可用
- ✅ 能够获取并转换网页为 markdown
- ✅ 错误处理正常（超时、404等）
- ✅ 与现有工具无冲突

---

## 🎯 下一步行动

### 立即执行（建议顺序）

1. **先执行移植 1**（最简单，风险最低）
   ```bash
   cd /Users/ericp/PycharmProjects/deepagents-hk
   git checkout -b backup/before-upstream-merge-2025-11-11
   git push origin backup/before-upstream-merge-2025-11-11
   git checkout master
   git checkout -b feature/upstream-subagent-error-handling
   # 按照上面步骤执行...
   ```

2. **评估移植 2 是否需要**
   - 检查是否有多子代理并发场景
   - 如果没有，跳过
   - 如果有，执行移植

3. **评估移植 3 价值**
   - 是否需要深度网页内容提取？
   - 现有 `web_search` 是否足够？
   - 如果需要，执行移植

### 需要帮助？

如需协助，请告知：
- 🐛 遇到的具体错误信息
- 📄 冲突的文件内容
- ❓ 不确定的决策点

---

**生成工具**: Claude Sonnet 4.5 + Cursor IDE  
**方案置信度**: 高  
**预计成功率**: 85%+（前提是按步骤执行）

