# API 速率限制处理方案

## 问题描述

当遇到以下错误时：

```
❌ Error: Error code: 429 - {'message': 'Request was rejected due to rate limiting. Details: TPM limit reached.'}
```

这表示 API 调用超过了服务提供商的速率限制（TPM = Tokens Per Minute，每分钟令牌数）。

## 解决方案概述

项目已集成**自动重试机制 + 速率限制器**，无需手动干预即可处理 429 错误。

### 核心功能

1. **指数退避重试** - 自动重试失败的请求，延迟时间指数增长
2. **令牌桶速率限制** - 主动控制请求频率，预防超限
3. **智能错误识别** - 自动识别可重试的错误（429, 5xx）
4. **并发控制** - 限制同时进行的请求数量

## 架构实现

### 1. 速率限制器 (`rate_limiter.py`)

```python
# 令牌桶算法 - 控制请求频率
class TokenBucketRateLimiter:
    - tokens_per_minute: 每分钟允许的令牌数
    - burst_size: 允许的突发请求量
    - acquire(tokens): 获取令牌（不足时等待）
```

### 2. 指数退避重试 (`rate_limiter.py`)

```python
# 重试策略
@async_retry_with_backoff(
    max_retries=5,        # 最多重试 5 次
    base_delay=1.0,       # 基础延迟 1 秒
    max_delay=60.0,       # 最大延迟 60 秒
    exponential_base=2.0, # 指数基数 2
    jitter=True           # 添加随机抖动
)
```

**延迟计算公式**：
```
delay = min(max_delay, base_delay * (exponential_base ^ retry_count))
```

示例延迟序列：1s → 2s → 4s → 8s → 16s

### 3. 弹性模型包装器 (`resilient_model.py`)

```python
# 为 LangChain 模型添加弹性功能
ResilientChatModel:
    - 自动处理 429 错误
    - 自动处理 5xx 服务器错误
    - 透明代理底层模型的所有功能
```

### 4. 配置集成 (`config.py`)

```python
def create_model(enable_resilience=True):
    # 创建基础模型
    base_model = ChatOpenAI(...)
    
    # 包装为弹性模型（默认启用）
    return wrap_model_with_resilience(base_model, ...)
```

## 环境变量配置

### 速率限制配置

```bash
# .env 文件或环境变量

# 是否启用弹性功能（默认: true）
ENABLE_MODEL_RESILIENCE=true

# 每分钟令牌限制（默认: 50000）
API_TOKENS_PER_MINUTE=50000

# 突发请求令牌数（默认: 10000）
API_BURST_SIZE=10000

# 最大重试次数（默认: 5）
API_MAX_RETRIES=5

# 基础延迟时间/秒（默认: 1.0）
API_BASE_DELAY=1.0

# 最大延迟时间/秒（默认: 60.0）
API_MAX_DELAY=60.0

# 最大并发请求数（默认: 5）
API_MAX_CONCURRENT=5
```

### 根据不同 API 提供商调整

#### SiliconFlow (DeepSeek)

```bash
# 免费套餐示例配置
API_TOKENS_PER_MINUTE=20000
API_BURST_SIZE=5000
API_MAX_CONCURRENT=3
```

#### OpenAI

```bash
# GPT-4 标准套餐
API_TOKENS_PER_MINUTE=90000
API_BURST_SIZE=15000
API_MAX_CONCURRENT=10
```

#### Anthropic (Claude)

```bash
# Claude 标准套餐
API_TOKENS_PER_MINUTE=40000
API_BURST_SIZE=8000
API_MAX_CONCURRENT=5
```

## 使用示例

### 自动模式（推荐）

系统已默认启用，无需额外配置：

```bash
# 直接使用，遇到 429 错误会自动重试
python -m src.cli.main
```

**终端输出示例**：

```
Using SiliconFlow model: deepseek-chat
  temperature=0.1, max_tokens=8192
  🛡️  弹性功能已启用: max_retries=5, TPM=50000

⚠️  速率限制: Error code: 429 - TPM limit reached
🔄 第 1/5 次重试，等待 1.2秒...
✅ 重试成功
```

### 手动配置模式

如果需要自定义配置：

```python
from src.cli.config import create_model
from src.cli.rate_limiter import TokenBucketRateLimiter
from src.cli.resilient_model import wrap_model_with_resilience

# 创建基础模型
base_model = create_model(enable_resilience=False)

# 自定义速率限制器
custom_limiter = TokenBucketRateLimiter(
    tokens_per_minute=30000,  # 自定义限制
    burst_size=6000
)

# 应用弹性功能
resilient_model = wrap_model_with_resilience(
    model=base_model,
    max_retries=3,
    base_delay=2.0,
    rate_limiter=custom_limiter
)
```

### 禁用弹性功能

```bash
# 如果需要禁用（不推荐）
export ENABLE_MODEL_RESILIENCE=false
```

或在代码中：

```python
model = create_model(enable_resilience=False)
```

## 监控和调试

### 查看速率限制状态

系统会在终端输出实时状态：

```
⏳ 速率限制: 等待 3.5秒 (需要 2500 个令牌)
```

### 查看重试过程

```
⚠️  速率限制: Error code: 429 - ...
🔄 第 2/5 次重试，等待 2.1秒...
```

### 调试模式

增加环境变量输出：

```bash
export PYTHONUNBUFFERED=1
export API_MAX_RETRIES=10  # 增加重试次数以便观察
```

## 最佳实践

### 1. 根据套餐配置限制

查看你的 API 套餐限制：

- **SiliconFlow**: [价格页面](https://siliconflow.cn/pricing)
- **OpenAI**: [Rate Limits](https://platform.openai.com/docs/guides/rate-limits)
- **Anthropic**: [Rate Limits](https://docs.anthropic.com/claude/reference/rate-limits)

设置 `API_TOKENS_PER_MINUTE` 为实际限制的 **80%**，留出安全余量。

### 2. 优化请求策略

```python
# ❌ 避免短时间内大量请求
for item in large_list:
    response = agent.analyze(item)  # 可能触发速率限制

# ✅ 使用批处理或增加间隔
import asyncio

async def process_batch(items):
    tasks = [agent.analyze_async(item) for item in items]
    return await asyncio.gather(*tasks)  # 自动速率控制
```

### 3. 监控 Token 使用

```python
from src.cli.token_utils import TokenTracker

tracker = TokenTracker(model_name="deepseek-chat")
# 使用后查看统计
print(f"Total tokens: {tracker.total_tokens}")
print(f"Cost: ${tracker.total_cost:.4f}")
```

### 4. 应对突发流量

```bash
# 临时增加突发容量
export API_BURST_SIZE=15000

# 或减少并发
export API_MAX_CONCURRENT=2
```

## 错误处理矩阵

| 错误类型 | 状态码 | 自动重试 | 建议操作 |
|---------|--------|---------|---------|
| 速率限制 | 429 | ✅ 是 | 降低 `API_TOKENS_PER_MINUTE` |
| 服务器错误 | 500-504 | ✅ 是 | 等待服务恢复 |
| 超时 | Timeout | ✅ 是 | 增加 `API_MAX_DELAY` |
| 配额耗尽 | 429 | ✅ 是 | 升级套餐或等待重置 |
| 认证错误 | 401 | ❌ 否 | 检查 API Key |
| 参数错误 | 400 | ❌ 否 | 修正请求参数 |

## 故障排查

### 问题 1: 仍然遇到 429 错误

**原因**: 速率限制设置过高

**解决**:

```bash
# 降低限制到实际配额的 50%
export API_TOKENS_PER_MINUTE=25000
export API_BURST_SIZE=5000
```

### 问题 2: 请求太慢

**原因**: 速率限制过于保守

**解决**:

```bash
# 增加限制（确保不超过实际配额）
export API_TOKENS_PER_MINUTE=80000
export API_MAX_CONCURRENT=10
```

### 问题 3: 重试次数耗尽

**原因**: 基础延迟或最大延迟设置不当

**解决**:

```bash
# 增加最大重试次数和延迟
export API_MAX_RETRIES=10
export API_MAX_DELAY=120
```

### 问题 4: 导入错误

**原因**: 模块未正确安装

**解决**:

```bash
# 重新安装依赖
pip install -e .
# 或
uv pip install -e .
```

## 升级建议

### 如果频繁遇到速率限制

1. **升级 API 套餐**
   - 增加 TPM 配额
   - 减少等待时间

2. **优化 Token 使用**
   - 简化 Prompt
   - 使用更小的模型
   - 启用响应缓存

3. **使用多个 API Key**
   ```python
   # 实现简单的负载均衡
   keys = [key1, key2, key3]
   current_key = keys[request_count % len(keys)]
   ```

## 技术细节

### 令牌估算算法

```python
# 简化估算：1 token ≈ 4 字符（英文）
estimated_tokens = len(text) // 4

# 保守估算
estimated_tokens = max(estimated_tokens, 500)  # 最小 500
```

### 重试判断逻辑

```python
def is_retryable_error(error: Exception) -> bool:
    error_str = str(error).lower()
    return any([
        "429" in error_str,
        "rate limit" in error_str,
        "tpm limit" in error_str,
        "quota" in error_str,
        "500" in error_str,
        "502" in error_str,
        "503" in error_str,
        "timeout" in error_str,
    ])
```

## 参考资料

- [LangChain 错误处理](https://python.langchain.com/docs/guides/safety/error_handling)
- [令牌桶算法](https://en.wikipedia.org/wiki/Token_bucket)
- [指数退避策略](https://en.wikipedia.org/wiki/Exponential_backoff)
- [OpenAI Rate Limits Best Practices](https://platform.openai.com/docs/guides/rate-limits/rate-limits-best-practices)

## 更新日志

- **2025-11-09**: 初始版本 - 添加完整速率限制和重试机制
  - 实现 `TokenBucketRateLimiter`
  - 实现 `ExponentialBackoff`
  - 实现 `ResilientChatModel`
  - 集成到 `create_model()`

---

**维护者**: DeepAgents-HK Team  
**最后更新**: 2025-11-09

