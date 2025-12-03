"""
配置数据模型 - Chainlit Settings Panel

定义用户配置的数据结构、API Provider 枚举和模型预设。
"""

import os
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, Dict, Any, List
import json

import dotenv
dotenv.load_dotenv()


class APIProvider(str, Enum):
    """支持的 API Provider 枚举."""
    SILICONFLOW = "siliconflow"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    
    @classmethod
    def choices(cls) -> List[str]:
        """返回所有可选值列表."""
        return [p.value for p in cls]
    
    @classmethod
    def display_names(cls) -> Dict[str, str]:
        """返回显示名称映射."""
        return {
            cls.SILICONFLOW.value: "SiliconFlow (硅基流动)",
            cls.OPENAI.value: "OpenAI",
            cls.ANTHROPIC.value: "Anthropic (Claude)",
        }


# 按 Provider 分组的模型列表
MODEL_PRESETS: Dict[str, List[Dict[str, str]]] = {
    APIProvider.SILICONFLOW.value: [
        {"id": "deepseek-chat", "name": "DeepSeek-V3 (推荐)", "context": "128K"},
        {"id": "deepseek-ai/DeepSeek-V3.1-Terminus", "name": "DeepSeek-V3.1 Terminus", "context": "128K"},
        {"id": "deepseek-reasoner", "name": "DeepSeek-R1 (推理)", "context": "128K"},
        {"id": "Qwen/Qwen2.5-72B-Instruct", "name": "Qwen2.5-72B", "context": "128K"},
        {"id": "Qwen/Qwen2.5-32B-Instruct", "name": "Qwen2.5-32B", "context": "128K"},
        {"id": "Qwen/Qwen2.5-7B-Instruct", "name": "Qwen2.5-7B (轻量)", "context": "32K"},
        {"id": "MiniMaxAI/MiniMax-M2", "name": "MiniMax-M2", "context": "186K"},
        {"id": "internlm/internlm2_5-7b-chat", "name": "InternLM2.5-7B", "context": "32K"},
    ],
    APIProvider.OPENAI.value: [
        {"id": "gpt-4o", "name": "GPT-4o (推荐)", "context": "128K"},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context": "128K"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini (轻量)", "context": "128K"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context": "16K"},
    ],
    APIProvider.ANTHROPIC.value: [
        {"id": "claude-sonnet-4-5-20250929", "name": "Claude Sonnet 4.5 (推荐)", "context": "200K"},
        {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "context": "200K"},
        {"id": "claude-opus-4", "name": "Claude Opus 4", "context": "200K"},
        {"id": "claude-haiku-4", "name": "Claude Haiku 4 (轻量)", "context": "200K"},
    ],
}


# 配置预设模板
CONFIG_PRESETS: Dict[str, Dict[str, Any]] = {
    "default": {
        "name": "默认配置",
        "description": "平衡的默认配置，适合日常使用",
        "temperature": 0.7,
        "max_tokens": 8000,
        "top_p": 0.9,
    },
    "analysis": {
        "name": "深度分析",
        "description": "适合深入分析港股公告，输出更详细",
        "temperature": 0.3,
        "max_tokens": 16000,
        "top_p": 0.95,
    },
    "summary": {
        "name": "快速摘要",
        "description": "快速生成简洁摘要，节省 Token",
        "temperature": 0.5,
        "max_tokens": 4000,
        "top_p": 0.85,
    },
    "creative": {
        "name": "创意报告",
        "description": "生成更有创意的分析报告",
        "temperature": 0.9,
        "max_tokens": 12000,
        "top_p": 0.95,
    },
}


# 默认系统提示词 - 使用与 CLI 相同的完整提示词
from src.prompts.prompts import get_main_system_prompt

try:
    DEFAULT_SYSTEM_PROMPT = get_main_system_prompt()
except FileNotFoundError:
    # 回退到简化版本
    DEFAULT_SYSTEM_PROMPT = """你是港股智能分析系统 HKEX Agent，专门处理港交所公告分析。

核心能力：
- 搜索和分析港交所公告
- 解析 PDF 文档（支持繁体中文）
- 生成结构化分析报告
- 查询股票基本信息
- 使用 shell 工具执行系统命令（如 date 获取时间）

分析原则：
- 保持客观中立，基于事实分析
- 对配售、供股等重大事项重点关注折让率
- 输出使用简洁专业的语言
- 数据呈现优先使用表格格式

时间获取：
- 使用 shell 工具执行 `date` 命令获取当前系统时间
- date 命令是安全的只读命令，无需用户审批
"""


@dataclass
class UserConfig:
    """用户配置数据类.
    
    包含所有可配置项，支持序列化到 JSON 存储。
    """
    
    # API 设置
    provider: str = APIProvider.SILICONFLOW.value
    model: str = "deepseek-chat"
    custom_model: Optional[str] = None  # 自定义模型名称（优先于 model）
    api_key_override: Optional[str] = None  # 可选覆盖环境变量
    
    # 模型参数
    temperature: float = 0.7
    max_tokens: int = 8000
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
    # 系统设置
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    enable_mcp: bool = False
    auto_approve: bool = True  # 自动审批工具调用（Chainlit 默认开启）
    show_download_links: bool = True  # 显示生成文件的下载链接
    
    # 预设 (用于快速切换)
    preset: str = "default"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return asdict(self)
    
    def to_json(self) -> str:
        """序列化为 JSON 字符串."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserConfig":
        """从字典创建实例."""
        # 过滤掉不存在的字段
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "UserConfig":
        """从 JSON 字符串创建实例."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def apply_preset(self, preset_name: str) -> None:
        """应用配置预设.
        
        Args:
            preset_name: 预设名称
        """
        if preset_name not in CONFIG_PRESETS:
            return
        
        preset = CONFIG_PRESETS[preset_name]
        self.temperature = preset.get("temperature", self.temperature)
        self.max_tokens = preset.get("max_tokens", self.max_tokens)
        self.top_p = preset.get("top_p", self.top_p)
        self.preset = preset_name
    
    def validate(self) -> List[str]:
        """验证配置有效性.
        
        Returns:
            错误消息列表，空列表表示配置有效
        """
        errors = []
        
        # 验证 provider
        if self.provider not in APIProvider.choices():
            errors.append(f"无效的 API Provider: {self.provider}")
        
        # 验证 temperature
        if not 0.0 <= self.temperature <= 2.0:
            errors.append(f"Temperature 必须在 0.0-2.0 之间: {self.temperature}")
        
        # 验证 max_tokens（放宽上限以支持不同模型）
        if self.max_tokens < 100:
            errors.append(f"Max Tokens 不能小于 100: {self.max_tokens}")
        elif self.max_tokens > 1000000:
            errors.append(f"Max Tokens 不能超过 1000000: {self.max_tokens}")
        
        # 验证 top_p
        if not 0.0 <= self.top_p <= 1.0:
            errors.append(f"Top P 必须在 0.0-1.0 之间: {self.top_p}")
        
        return errors
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """获取当前 Provider 的可用模型列表."""
        return MODEL_PRESETS.get(self.provider, [])
    
    def get_model_display_name(self) -> str:
        """获取当前模型的显示名称."""
        # 优先使用自定义模型
        if self.custom_model:
            return f"{self.custom_model} (自定义)"
        
        models = self.get_available_models()
        for m in models:
            if m["id"] == self.model:
                return f"{m['name']} ({m['context']})"
        return self.model
    
    def get_effective_model(self) -> str:
        """获取实际使用的模型名称（自定义优先）."""
        return self.custom_model if self.custom_model else self.model


def get_default_config() -> UserConfig:
    """获取默认配置实例.
    
    从环境变量读取默认值，如果未设置则使用硬编码默认值。
    """
    # 从环境变量读取默认值
    model = os.getenv("SILICONFLOW_MODEL", "deepseek-chat")
    temperature = float(os.getenv("SILICONFLOW_TEMPERATURE", "0.7"))
    max_tokens = int(os.getenv("SILICONFLOW_MAX_TOKENS", "8000"))
    enable_mcp = os.getenv("ENABLE_MCP", "false").lower() == "true"
    
    return UserConfig(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        enable_mcp=enable_mcp,
    )


def get_models_for_provider(provider: str) -> List[Dict[str, str]]:
    """获取指定 Provider 的模型列表.
    
    Args:
        provider: API Provider 值
        
    Returns:
        模型列表，每个模型包含 id, name, context
    """
    return MODEL_PRESETS.get(provider, [])


def get_preset_options() -> List[Dict[str, str]]:
    """获取配置预设选项列表.
    
    Returns:
        预设选项列表，每个选项包含 id, name, description
    """
    return [
        {"id": k, "name": v["name"], "description": v["description"]}
        for k, v in CONFIG_PRESETS.items()
    ]

