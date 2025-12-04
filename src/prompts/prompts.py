"""港交所智能体的提示词加载工具。

支持模块化提示词结构：
- 主提示词: default_agent_md.md, main_system_prompt.md 等
- 子模块: hkex_modules/ 目录下的专用模块
"""

from pathlib import Path
from typing import Optional


def _get_prompts_dir() -> Path:
    """获取提示词目录路径。
    
    Returns:
        提示词目录的路径。
    """
    return Path(__file__).parent


def _get_modules_dir() -> Path:
    """获取模块目录路径。
    
    Returns:
        hkex_modules 目录的路径。
    """
    return _get_prompts_dir() / "hkex_modules"


def load_prompt(filename: str) -> str:
    """从文件加载提示词模板。
    
    Args:
        filename: 提示词文件名（例如，"main_system_prompt.md"）。
        
    Returns:
        提示词内容字符串。
        
    Raises:
        FileNotFoundError: 如果提示词文件不存在。
    """
    prompts_dir = _get_prompts_dir()
    prompt_path = prompts_dir / filename
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"提示词文件未找到: {prompt_path}")
    
    return prompt_path.read_text(encoding="utf-8")


def load_module(module_name: str) -> str:
    """从 hkex_modules 目录加载模块提示词。
    
    Args:
        module_name: 模块文件名（例如，"intent_recognition.md"）。
        
    Returns:
        模块内容字符串。
        
    Raises:
        FileNotFoundError: 如果模块文件不存在。
    """
    modules_dir = _get_modules_dir()
    module_path = modules_dir / module_name
    
    if not module_path.exists():
        raise FileNotFoundError(f"模块文件未找到: {module_path}")
    
    return module_path.read_text(encoding="utf-8")


def get_main_system_prompt() -> str:
    """获取主要的港交所智能体系统提示词。
    
    Returns:
        主要系统提示词字符串。
    """
    return load_prompt("main_system_prompt.md")


def get_pdf_analyzer_prompt() -> str:
    """获取 PDF 分析器子智能体提示词。
    
    Returns:
        PDF 分析器提示词字符串。
    """
    return load_prompt("pdf_analyzer_prompt.md")


def get_report_generator_prompt() -> str:
    """获取报告生成器子智能体提示词。
    
    Returns:
        报告生成器提示词字符串。
    """
    return load_prompt("report_generator_prompt.md")


def get_longterm_memory_prompt() -> str:
    """获取长期记忆系统提示词模板。
    
    Returns:
        长期记忆提示词模板字符串（包含 {memory_path} 占位符）。
    """
    return load_prompt("longterm_memory_prompt.md")


def get_default_agent_md() -> str:
    """获取默认的 agent.md 内容。
    
    Returns:
        默认 agent.md 内容字符串。
    """
    return load_prompt("default_agent_md.md")


# ============================================================
# 模块化加载函数（新增）
# ============================================================

def get_intent_recognition_module() -> str:
    """获取意图识别模块。
    
    Returns:
        意图识别规则和流程。
    """
    return load_module("intent_recognition.md")


def get_event_types_module() -> str:
    """获取事件类型定义模块。
    
    包含三大财技事件类型定义和完整关键词表。
    
    Returns:
        事件类型定义和关键词表。
    """
    return load_module("event_types.md")


def get_search_workflow_module() -> str:
    """获取搜索工作流程模块。
    
    Returns:
        完整的搜索和分析工作流程。
    """
    return load_module("search_workflow.md")


def get_data_extraction_module() -> str:
    """获取数据提取清单模块。
    
    Returns:
        七类核心数据的提取清单。
    """
    return load_module("data_extraction_checklist.md")


def get_report_template_module() -> str:
    """获取报告模板模块。
    
    Returns:
        Markdown 报告模板和阶段定义。
    """
    return load_module("report_template.md")


def get_full_hkex_prompt(include_modules: bool = False) -> str:
    """获取完整的 HKEX 分析提示词。
    
    Args:
        include_modules: 是否将子模块内容内联到主提示词中。
                        默认 False，仅返回主提示词（引用模块路径）。
                        设为 True 时，将所有模块内容合并为一个完整文档。
    
    Returns:
        完整的 HKEX 分析提示词。
    """
    main_prompt = get_default_agent_md()
    
    if not include_modules:
        return main_prompt
    
    # 内联所有模块
    modules = [
        "\n\n---\n\n# 附录：详细模块\n",
        "\n## A1. 意图识别详细规则\n\n",
        get_intent_recognition_module(),
        "\n\n---\n\n## A2. 事件类型与关键词表\n\n",
        get_event_types_module(),
        "\n\n---\n\n## A3. 搜索工作流程详解\n\n",
        get_search_workflow_module(),
        "\n\n---\n\n## A4. 数据提取完整清单\n\n",
        get_data_extraction_module(),
        "\n\n---\n\n## A5. 报告模板\n\n",
        get_report_template_module(),
    ]
    
    return main_prompt + "".join(modules)


def list_available_modules() -> list[str]:
    """列出所有可用的模块文件。
    
    Returns:
        模块文件名列表。
    """
    modules_dir = _get_modules_dir()
    if not modules_dir.exists():
        return []
    
    return [f.name for f in modules_dir.glob("*.md")]


def get_module_by_name(name: str) -> Optional[str]:
    """根据模块名称获取内容。
    
    支持以下名称格式：
    - 完整文件名: "intent_recognition.md"
    - 无扩展名: "intent_recognition"
    - 简短别名: "intent", "keywords", "search", "data", "template"
    
    Args:
        name: 模块名称或别名。
        
    Returns:
        模块内容，如果不存在则返回 None。
    """
    # 别名映射
    aliases = {
        "intent": "intent_recognition.md",
        "keywords": "event_types.md",
        "types": "event_types.md",
        "search": "search_workflow.md",
        "workflow": "search_workflow.md",
        "data": "data_extraction_checklist.md",
        "extraction": "data_extraction_checklist.md",
        "checklist": "data_extraction_checklist.md",
        "template": "report_template.md",
        "report": "report_template.md",
    }
    
    # 处理别名
    if name in aliases:
        name = aliases[name]
    
    # 添加 .md 扩展名（如果缺少）
    if not name.endswith(".md"):
        name = f"{name}.md"
    
    try:
        return load_module(name)
    except FileNotFoundError:
        return None
