"""Configuration, constants, and model creation for the CLI."""

import os
import sys
from pathlib import Path
from typing import Union

import dotenv
from rich.console import Console
from rich.text import Text

dotenv.load_dotenv()

# Color scheme
COLORS = {
    "primary": "#10b981",
    "dim": "#6b7280",
    "user": "#ffffff",
    "agent": "#10b981",
    "thinking": "#34d399",
    "tool": "#fbbf24",
}

# 彩虹渐变色 - 用于ASCII横幅
RAINBOW_COLORS = [
    "#ff0000",  # 红
    "#ff7f00",  # 橙
    "#ffff00",  # 黄
    "#00ff00",  # 绿
    "#00ffff",  # 青
    "#0000ff",  # 蓝
    "#8b00ff",  # 紫
]

def get_hkex_banner(font: str = "slant", rainbow: bool = True) -> Union[Text, str]:
    """动态生成HKEX Agent横幅，支持彩虹渐变效果.
    
    Args:
        font: 字体风格 (slant, standard, banner, digital等)
            可通过环境变量 HKEX_ASCII_FONT 配置
        rainbow: 是否启用彩虹渐变效果
            可通过环境变量 HKEX_RAINBOW=true/false 配置
    
    Returns:
        Rich Text对象(彩虹模式) 或 字符串(普通模式)
    """
    # 从环境变量读取配置
    font = os.getenv("HKEX_ASCII_FONT", font)
    rainbow = os.getenv("HKEX_RAINBOW", str(rainbow)).lower() in ("true", "1", "yes")
    
    try:
        import pyfiglet
        # 生成ASCII艺术字
        banner_text = pyfiglet.figlet_format("HKEX Agent", font=font)
        
        if rainbow:
            # 创建彩虹渐变效果
            text = Text()
            lines = banner_text.split("\n")
            
            for i, line in enumerate(lines):
                # 为每行分配颜色（渐变效果）
                color_idx = i % len(RAINBOW_COLORS)
                text.append(line + "\n", style=f"bold {RAINBOW_COLORS[color_idx]}")
            
            return text
        else:
            return banner_text
            
    except ImportError:
        # 如果pyfiglet未安装，返回简单版本
        return "🏢 HKEX Agent | 港交所公告分析助手\n"
    except Exception:
        # 如果字体不存在或其他错误，返回默认
        return "🏢 HKEX Agent | 港交所公告分析助手\n"


# ASCII art banner - 动态生成
HKEX_AGENT_ASCII = get_hkex_banner()

# Interactive commands
COMMANDS = {
    "clear": "Clear screen and reset conversation",
    "help": "Show help information",
    "skills": "Manage and view available skills (list/show/search)",
    "memory": "View memory configuration paths",
    "tokens": "Show token usage for current session",
    "quit": "Exit the CLI",
    "exit": "Exit the CLI",
}

# Maximum argument length for display
MAX_ARG_LENGTH = 150

# Agent configuration
config = {"recursion_limit": 1000}

# Rich console instance
console = Console(highlight=False)


class SessionState:
    """Holds mutable session state (auto-approve mode, etc)."""

    def __init__(self, auto_approve: bool = False, show_thinking: bool = False):
        self.auto_approve = auto_approve
        self.show_thinking = show_thinking
        self.show_tool_outputs = False
        self.exit_hint_until: float | None = None
        self.exit_hint_handle = None

    def toggle_auto_approve(self) -> bool:
        """Toggle auto-approve and return new state."""
        self.auto_approve = not self.auto_approve
        return self.auto_approve
    
    def toggle_tool_outputs(self) -> bool:
        """Toggle tool output visibility and return new state."""
        self.show_tool_outputs = not self.show_tool_outputs
        return self.show_tool_outputs


def create_model():
    """Create the appropriate model based on available API keys.
    
    Uses unified configuration from agent_model_config for temperature and max_tokens.

    Priority: SiliconFlow > OpenAI > Anthropic

    Returns:
        ChatModel instance (SiliconFlow, OpenAI, or Anthropic)

    Raises:
        SystemExit if no API key is configured
    """
    # Import unified config
    from src.config.agent_config import agent_model_config
    
    # Check SiliconFlow first (highest priority)
    siliconflow_key = os.environ.get("SILICONFLOW_API_KEY")
    if siliconflow_key:
        from langchain_openai import ChatOpenAI

        model_name = os.environ.get("SILICONFLOW_MODEL", "deepseek-chat")
        console.print(f"[dim]Using SiliconFlow model: {model_name}[/dim]", justify="center")
        console.print(f"[dim]  temperature={agent_model_config.temperature}, max_tokens={agent_model_config.max_tokens}[/dim]", justify="center")
        return ChatOpenAI(
            model=model_name,
            base_url="https://api.siliconflow.cn/v1",
            api_key=siliconflow_key,
            temperature=agent_model_config.temperature,
            max_tokens=agent_model_config.max_tokens,
        )

    # Check OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        from langchain_openai import ChatOpenAI

        model_name = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
        console.print(f"[dim]Using OpenAI model: {model_name}[/dim]", justify="center")
        console.print(f"[dim]  temperature={agent_model_config.temperature}, max_tokens={agent_model_config.max_tokens}[/dim]", justify="center")
        return ChatOpenAI(
            model=model_name,
            temperature=agent_model_config.temperature,
            max_tokens=agent_model_config.max_tokens,
        )

    # Check Anthropic
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        from langchain_anthropic import ChatAnthropic

        model_name = os.environ.get(
            "ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"
        )
        console.print(f"[dim]Using Anthropic model: {model_name}[/dim]", justify="center")
        console.print(f"[dim]  max_tokens={agent_model_config.max_tokens}[/dim]", justify="center")
        return ChatAnthropic(
            model_name=model_name,
            max_tokens=agent_model_config.max_tokens,
        )

    # No API key found
    console.print("[bold red]Error:[/bold red] No API key configured.")
    console.print("\nPlease set one of the following environment variables:")
    console.print("  - SILICONFLOW_API_KEY  (for SiliconFlow models like deepseek-chat)")
    console.print("  - OPENAI_API_KEY       (for OpenAI models like gpt-5-mini)")
    console.print("  - ANTHROPIC_API_KEY    (for Claude models)")
    console.print("\nExample:")
    console.print("  export SILICONFLOW_API_KEY=your_api_key_here")
    console.print("  export SILICONFLOW_MODEL=deepseek-chat  # optional")
    console.print("\nOr add it to your .env file.")
    sys.exit(1)

