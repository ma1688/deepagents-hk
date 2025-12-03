"""
配置数据模型 - Chainlit Settings Panel

定义用户配置的数据结构、API Provider 枚举和场景模式。
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


# ============== 场景模式 ==============
# 每个场景 = 参数 + 提示词 = 完整配置

# 默认系统提示词
from src.prompts.prompts import get_main_system_prompt
try:
    DEFAULT_SYSTEM_PROMPT = get_main_system_prompt()
except FileNotFoundError:
    DEFAULT_SYSTEM_PROMPT = "你是港股智能分析系统 HKEX Agent。"


# 内置场景（不可删除）
BUILTIN_SCENES: Dict[str, Dict[str, Any]] = {
    "default": {
        "name": "🎯 通用模式",
        "description": "平衡配置，适合日常分析",
        "temperature": 0.7,
        "max_tokens": 8000,
        "top_p": 0.9,
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "builtin": True,
    },
    "analysis": {
        "name": "🔍 深度分析",
        "description": "详细分析港股公告",
        "temperature": 0.3,
        "max_tokens": 16000,
        "top_p": 0.95,
        "system_prompt": """你是港股深度分析专家。请对公告进行详尽分析。

## 分析框架
1. **核心要点** - 关键数据、日期、金额
2. **交易结构** - 配售/供股/收购的具体条款
3. **财务影响** - 对公司财务状况的影响
4. **风险因素** - 潜在风险和不确定性
5. **投资建议** - 基于分析的客观评价

## 输出要求
- 使用表格呈现关键数据
- 计算折让率、摊薄比例等关键指标
- 对比行业平均水平
- 提供详细的数据支撑

""" + DEFAULT_SYSTEM_PROMPT,
        "builtin": True,
    },
    "summary": {
        "name": "⚡ 快速摘要",
        "description": "简洁输出，节省时间",
        "temperature": 0.5,
        "max_tokens": 4000,
        "top_p": 0.85,
        "system_prompt": """你是港股公告摘要专家。用最简洁的方式总结要点。

## 输出格式
📌 **一句话总结**: [核心内容]

📊 **关键数据**:
| 项目 | 内容 |
|------|------|
| 股票代码 | |
| 涉及金额 | |
| 关键日期 | |

⚠️ **注意事项**: [如有]

**限制**: 回复控制在 500 字以内。

""" + DEFAULT_SYSTEM_PROMPT,
        "builtin": True,
    },
    "creative": {
        "name": "✨ 创意报告",
        "description": "生动有趣的分析风格",
        "temperature": 0.9,
        "max_tokens": 12000,
        "top_p": 0.95,
        "system_prompt": """你是一位富有洞察力的港股分析师，擅长用生动的语言解读公告。

## 风格要求
- 使用生动形象的比喻解释复杂概念
- 加入市场背景和行业趋势分析
- 提供独到的投资视角
- 适当使用 emoji 增强可读性

## 报告结构
🎯 **开篇亮点** - 最吸引眼球的发现
📖 **故事背景** - 公司和市场情况
🔍 **深度解读** - 核心内容分析
💡 **独家观点** - 你的专业判断
🎬 **后续展望** - 可能的发展方向

""" + DEFAULT_SYSTEM_PROMPT,
        "builtin": True,
    },
}

# 兼容旧代码
CONFIG_PRESETS = BUILTIN_SCENES
BUILTIN_PRESETS = BUILTIN_SCENES


@dataclass
class UserScene:
    """用户自定义场景数据类."""
    
    id: str  # 场景 ID (唯一标识)
    name: str  # 显示名称
    description: str = ""  # 描述
    temperature: float = 0.7
    max_tokens: int = 8000
    top_p: float = 0.9
    system_prompt: str = ""  # 系统提示词
    user_id: str = ""  # 所属用户
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return asdict(self)
    
    def to_json(self) -> str:
        """序列化为 JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserScene":
        """从字典创建."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
    
    def to_scene_dict(self) -> Dict[str, Any]:
        """转换为场景格式."""
        return {
            "name": f"⭐ {self.name}",
            "description": self.description,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "system_prompt": self.system_prompt,
            "builtin": False,
            "user_scene_id": self.id,
        }


# 兼容旧代码 - 别名
UserPreset = UserScene


@dataclass
class UserConfig:
    """用户配置数据类.
    
    包含所有可配置项，支持序列化到 JSON 存储。
    """
    
    # API 设置
    provider: str = APIProvider.SILICONFLOW.value
    model: str = "deepseek-chat"
    custom_model: Optional[str] = None
    api_key_override: Optional[str] = None
    
    # 模型参数
    temperature: float = 0.7
    max_tokens: int = 8000
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
    # 系统设置
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    enable_mcp: bool = False
    auto_approve: bool = True
    show_download_links: bool = True
    
    # 当前场景
    scene: str = "default"
    
    # 兼容旧代码
    @property
    def preset(self) -> str:
        return self.scene
    
    @preset.setter
    def preset(self, value: str):
        self.scene = value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        d = asdict(self)
        d["preset"] = self.scene  # 兼容
        return d
    
    def to_json(self) -> str:
        """序列化为 JSON 字符串."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserConfig":
        """从字典创建实例."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        # 兼容旧的 preset 字段
        if "preset" in data and "scene" not in filtered_data:
            filtered_data["scene"] = data["preset"]
        return cls(**filtered_data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "UserConfig":
        """从 JSON 字符串创建实例."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def apply_scene(self, scene_id: str, all_scenes: Dict[str, Any] = None) -> bool:
        """应用场景配置.
        
        Args:
            scene_id: 场景 ID
            all_scenes: 所有可用场景（内置+自定义）
            
        Returns:
            是否成功应用
        """
        scenes = all_scenes or BUILTIN_SCENES
        if scene_id not in scenes:
            return False
        
        scene = scenes[scene_id]
        self.temperature = scene.get("temperature", self.temperature)
        self.max_tokens = scene.get("max_tokens", self.max_tokens)
        self.top_p = scene.get("top_p", self.top_p)
        self.system_prompt = scene.get("system_prompt", self.system_prompt)
        self.scene = scene_id
        return True
    
    def validate(self) -> List[str]:
        """验证配置有效性."""
        errors = []
        if self.provider not in APIProvider.choices():
            errors.append(f"无效的 API Provider: {self.provider}")
        if not 0.0 <= self.temperature <= 2.0:
            errors.append(f"Temperature 必须在 0.0-2.0 之间")
        if self.max_tokens < 100 or self.max_tokens > 1000000:
            errors.append(f"Max Tokens 必须在 100-1000000 之间")
        if not 0.0 <= self.top_p <= 1.0:
            errors.append(f"Top P 必须在 0.0-1.0 之间")
        return errors
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """获取当前 Provider 的可用模型列表."""
        return MODEL_PRESETS.get(self.provider, [])
    
    def get_model_display_name(self) -> str:
        """获取当前模型的显示名称."""
        if self.custom_model:
            return f"{self.custom_model} (自定义)"
        models = self.get_available_models()
        for m in models:
            if m["id"] == self.model:
                return f"{m['name']} ({m['context']})"
        return self.model
    
    def get_effective_model(self) -> str:
        """获取实际使用的模型名称."""
        return self.custom_model if self.custom_model else self.model


def get_default_config() -> UserConfig:
    """获取默认配置实例."""
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
    """获取指定 Provider 的模型列表."""
    return MODEL_PRESETS.get(provider, [])


def get_preset_options() -> List[Dict[str, str]]:
    """获取场景选项列表（兼容旧API）."""
    return [
        {"id": k, "name": v["name"], "description": v["description"]}
        for k, v in BUILTIN_SCENES.items()
    ]


def get_preset_display_name(preset_id: str, preset_data: Dict[str, Any]) -> str:
    """生成预设的显示名称（兼容旧API）."""
    return preset_data.get("name", preset_id)
