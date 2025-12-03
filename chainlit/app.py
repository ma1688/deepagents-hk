"""
HKEX Agent - Chainlit Web Interface

港股智能分析系统 Web 界面，基于 Chainlit 构建。
支持对话历史持久化、用户配置和恢复。
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

# 获取项目根目录
project_root = Path(__file__).parent.parent.resolve()

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(project_root))

# 切换工作目录到项目根目录，确保相对路径正确解析
# 这样 mcp_config.json、pdf_cache/ 等路径都能正常工作
os.chdir(project_root)

import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.input_widget import Select, Slider, Switch, TextInput
from langchain_core.messages import HumanMessage, AIMessage

from src.agents.main_agent import create_hkex_agent
from local_storage import LocalStorageClient
from config_models import (
    UserConfig,
    APIProvider,
    MODEL_PRESETS,
    CONFIG_PRESETS,
    DEFAULT_SYSTEM_PROMPT,
    get_default_config,
    get_models_for_provider,
    get_preset_options,
)
from config_storage import get_config_storage, init_config_storage

# ============== 数据持久化配置 ==============
# 使用 SQLite 存储对话历史
DB_PATH = project_root / "chainlit_data" / "chat_history.db"
STORAGE_PATH = project_root / "chainlit_data" / "files"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
STORAGE_PATH.mkdir(parents=True, exist_ok=True)

# 创建本地存储客户端
storage_client = LocalStorageClient(storage_dir=STORAGE_PATH)

# 初始化配置存储
config_storage = get_config_storage(DB_PATH)


@cl.data_layer
def get_data_layer():
    """配置 SQLite 数据持久化层（带本地文件存储）。"""
    return SQLAlchemyDataLayer(
        conninfo=f"sqlite+aiosqlite:///{DB_PATH}",
        storage_provider=storage_client,
    )


# ============== 简单用户认证 ==============
@cl.password_auth_callback
def auth_callback(username: str, password: str):
    """
    简单密码认证。
    
    默认用户：
    - 用户名: admin, 密码: admin (管理员)
    - 用户名: user, 密码: user (普通用户)
    """
    # 简单用户验证
    if (username, password) == ("admin", "admin"):
        return cl.User(
            identifier="admin", 
            metadata={"role": "ADMIN", "provider": "credentials"}
        )
    elif (username, password) == ("user", "user"):
        return cl.User(
            identifier="user", 
            metadata={"role": "USER", "provider": "credentials"}
        )
    else:
        return None


# ============== 配置辅助函数 ==============
def create_model_from_config(config: UserConfig):
    """根据用户配置创建模型实例.
    
    Args:
        config: 用户配置对象
        
    Returns:
        LangChain Chat 模型实例
    """
    # 获取 API Key（优先使用用户配置，否则使用环境变量）
    if config.provider == APIProvider.SILICONFLOW.value:
        api_key = config.api_key_override or os.environ.get("SILICONFLOW_API_KEY")
        if not api_key:
            raise ValueError("未配置 SiliconFlow API Key")
        
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config.model,
            base_url="https://api.siliconflow.cn/v1",
            api_key=api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            frequency_penalty=config.frequency_penalty,
            presence_penalty=config.presence_penalty,
        )
    
    elif config.provider == APIProvider.OPENAI.value:
        api_key = config.api_key_override or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("未配置 OpenAI API Key")
        
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config.model,
            api_key=api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            frequency_penalty=config.frequency_penalty,
            presence_penalty=config.presence_penalty,
        )
    
    elif config.provider == APIProvider.ANTHROPIC.value:
        api_key = config.api_key_override or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("未配置 Anthropic API Key")
        
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model_name=config.model,
            api_key=api_key,
            max_tokens=config.max_tokens,
            # Anthropic 不支持 top_p 等参数
        )
    
    else:
        raise ValueError(f"不支持的 API Provider: {config.provider}")


def build_settings_widgets(config: UserConfig) -> list:
    """构建设置面板组件.
    
    Args:
        config: 当前用户配置
        
    Returns:
        Chainlit 输入组件列表
    """
    # 获取当前 provider 的模型列表
    models = get_models_for_provider(config.provider)
    model_options = [m["id"] for m in models]
    model_labels = {m["id"]: f"{m['name']} ({m['context']})" for m in models}
    
    # 预设选项
    preset_options = list(CONFIG_PRESETS.keys())
    preset_labels = {k: v["name"] for k, v in CONFIG_PRESETS.items()}
    
    return [
        # === API 设置 ===
        Select(
            id="provider",
            label="API Provider",
            description="选择 AI 模型提供商",
            values=APIProvider.choices(),
            initial_value=config.provider,
        ),
        Select(
            id="model",
            label="模型",
            description="选择使用的模型",
            values=model_options if model_options else ["deepseek-chat"],
            initial_value=config.model if config.model in model_options else (model_options[0] if model_options else "deepseek-chat"),
        ),
        TextInput(
            id="api_key_override",
            label="API Key (可选)",
            description="覆盖环境变量中的 API Key，留空则使用默认配置",
            initial=config.api_key_override or "",
            placeholder="sk-...",
        ),
        
        # === 模型参数 ===
        Slider(
            id="temperature",
            label="Temperature",
            description="控制输出随机性 (0=确定性, 1=创意性)",
            min=0.0,
            max=1.5,
            step=0.1,
            initial=config.temperature,
        ),
        Slider(
            id="max_tokens",
            label="Max Tokens",
            description="最大输出 Token 数",
            min=1000,
            max=32000,
            step=1000,
            initial=config.max_tokens,
        ),
        Slider(
            id="top_p",
            label="Top P",
            description="核采样参数",
            min=0.1,
            max=1.0,
            step=0.05,
            initial=config.top_p,
        ),
        
        # === 系统设置 ===
        Switch(
            id="enable_mcp",
            label="启用 MCP 集成",
            description="启用 Model Context Protocol 扩展功能",
            initial=config.enable_mcp,
        ),
        TextInput(
            id="system_prompt",
            label="系统提示词",
            description="自定义 Agent 系统提示词",
            initial=config.system_prompt,
            placeholder="你是港股智能分析系统...",
        ),
        
        # === 预设 ===
        Select(
            id="preset",
            label="配置预设",
            description="快速应用预定义配置",
            values=preset_options,
            initial_value=config.preset,
        ),
    ]


def settings_to_config(settings: dict, current_config: UserConfig) -> UserConfig:
    """将设置面板值转换为配置对象.
    
    Args:
        settings: 设置面板返回的字典
        current_config: 当前配置（用于获取未修改的值）
        
    Returns:
        更新后的 UserConfig 对象
    """
    # 检查是否切换了预设
    new_preset = settings.get("preset", current_config.preset)
    if new_preset != current_config.preset and new_preset in CONFIG_PRESETS:
        # 应用预设
        preset = CONFIG_PRESETS[new_preset]
        return UserConfig(
            provider=settings.get("provider", current_config.provider),
            model=settings.get("model", current_config.model),
            api_key_override=settings.get("api_key_override") or None,
            temperature=preset["temperature"],
            max_tokens=preset["max_tokens"],
            top_p=preset["top_p"],
            frequency_penalty=current_config.frequency_penalty,
            presence_penalty=current_config.presence_penalty,
            system_prompt=settings.get("system_prompt", current_config.system_prompt),
            enable_mcp=settings.get("enable_mcp", current_config.enable_mcp),
            preset=new_preset,
        )
    
    # 正常更新
    return UserConfig(
        provider=settings.get("provider", current_config.provider),
        model=settings.get("model", current_config.model),
        api_key_override=settings.get("api_key_override") or None,
        temperature=settings.get("temperature", current_config.temperature),
        max_tokens=int(settings.get("max_tokens", current_config.max_tokens)),
        top_p=settings.get("top_p", current_config.top_p),
        frequency_penalty=current_config.frequency_penalty,
        presence_penalty=current_config.presence_penalty,
        system_prompt=settings.get("system_prompt", current_config.system_prompt),
        enable_mcp=settings.get("enable_mcp", current_config.enable_mcp),
        preset=new_preset,
    )


# ============== 设置更新处理 ==============
@cl.on_settings_update
async def on_settings_update(settings: dict):
    """处理设置更新.
    
    当用户在设置面板中修改配置时触发。
    """
    user = cl.user_session.get("user")
    user_id = user.identifier if user else "anonymous"
    
    # 获取当前配置
    current_config = cl.user_session.get("config") or get_default_config()
    
    # 转换为新配置
    new_config = settings_to_config(settings, current_config)
    
    # 验证配置
    errors = new_config.validate()
    if errors:
        await cl.Message(
            content=f"⚠️ **配置验证失败**\n\n" + "\n".join(f"- {e}" for e in errors),
            author="system",
        ).send()
        return
    
    # 检查 provider 是否变更（需要更新模型列表）
    provider_changed = new_config.provider != current_config.provider
    
    # 如果 provider 变更，重置模型为该 provider 的第一个
    if provider_changed:
        models = get_models_for_provider(new_config.provider)
        if models:
            new_config.model = models[0]["id"]
    
    # 保存配置
    await config_storage.save_config(user_id, new_config)
    cl.user_session.set("config", new_config)
    
    # 如果 provider 变更，需要重新初始化设置面板
    if provider_changed:
        settings_widgets = build_settings_widgets(new_config)
        await cl.ChatSettings(settings_widgets).send()
    
    # 重新创建 Agent
    try:
        model = create_model_from_config(new_config)
        agent = await create_hkex_agent(
            model=model,
            assistant_id=cl.context.session.id,
            enable_mcp=new_config.enable_mcp,
            system_prompt=new_config.system_prompt,
            use_checkpointer=False,  # Chainlit has its own persistence
        )
        cl.user_session.set("agent", agent)
        
        # 显示更新成功消息
        provider_name = APIProvider.display_names().get(new_config.provider, new_config.provider)
        await cl.Message(
            content=f"✅ **配置已更新**\n\n"
                    f"- Provider: {provider_name}\n"
                    f"- 模型: {new_config.get_model_display_name()}\n"
                    f"- Temperature: {new_config.temperature}\n"
                    f"- Max Tokens: {new_config.max_tokens}\n"
                    f"- MCP: {'启用' if new_config.enable_mcp else '禁用'}",
            author="system",
        ).send()
        
    except Exception as e:
        await cl.Message(
            content=f"❌ **配置更新失败**\n\n```\n{str(e)}\n```\n\n请检查 API Key 是否正确配置。",
            author="system",
        ).send()


# ============== 对话恢复 ==============
@cl.on_chat_resume
async def on_chat_resume(thread: dict):
    """恢复历史对话时的处理。"""
    user = cl.user_session.get("user")
    user_id = user.identifier if user else "anonymous"
    
    # 加载用户配置
    config = await config_storage.load_or_default(user_id)
    cl.user_session.set("config", config)
    
    # ⭐ 从 thread["steps"] 恢复历史消息（关键修复！）
    message_history = []
    for step in thread.get("steps", []):
        step_type = step.get("type")
        step_output = step.get("output", "")
        
        # 跳过空消息和系统消息
        if not step_output or step_type == "system_message":
            continue
            
        # 用户消息
        if step_type == "user_message":
            message_history.append(HumanMessage(content=step_output))
        # AI 助手消息
        elif step_type == "assistant_message":
            message_history.append(AIMessage(content=step_output))
    
    cl.user_session.set("message_history", message_history)
    
    # 创建模型和 Agent
    try:
        model = create_model_from_config(config)
        
        agent = await create_hkex_agent(
            model=model,
            assistant_id=thread["id"],
            enable_mcp=config.enable_mcp,
            system_prompt=config.system_prompt,
            use_checkpointer=False,  # Chainlit has its own persistence
        )
        
        cl.user_session.set("agent", agent)
        cl.user_session.set("thread_id", thread["id"])
        
        # 初始化设置面板
        settings_widgets = build_settings_widgets(config)
        await cl.ChatSettings(settings_widgets).send()
        
        await cl.Message(
            content=f"📂 已恢复对话: **{thread.get('name', '未命名对话')}**\n\n"
                    f"✅ 已加载 **{len(message_history)}** 条历史消息，继续您的分析..."
        ).send()
        
    except Exception as e:
        await cl.Message(
            content=f"❌ **恢复对话失败**\n\n```\n{str(e)}\n```"
        ).send()


@cl.on_chat_start
async def on_chat_start():
    """初始化聊天会话，创建 HKEX Agent。"""
    user = cl.user_session.get("user")
    user_id = user.identifier if user else "anonymous"
    
    # 加载用户配置
    config = await config_storage.load_or_default(user_id)
    cl.user_session.set("config", config)
    
    # ⭐ 初始化消息历史（关键：保持对话上下文）
    cl.user_session.set("message_history", [])
    
    # 初始化设置面板
    settings_widgets = build_settings_widgets(config)
    await cl.ChatSettings(settings_widgets).send()
    
    # 发送欢迎消息
    provider_name = APIProvider.display_names().get(config.provider, config.provider)
    await cl.Message(
        content="🏛️ **港股智能分析系统** 已就绪！\n\n"
                "我可以帮助您：\n"
                "- 📰 搜索和分析港交所公告\n"
                "- 📄 解析 PDF 文档\n"
                "- 📊 生成分析报告\n"
                "- 💹 查询股票信息\n\n"
                f"当前配置：**{provider_name}** / **{config.get_model_display_name()}**\n\n"
                "💡 点击右上角 ⚙️ 图标可修改模型和参数设置。"
    ).send()

    # 创建模型
    try:
        model = create_model_from_config(config)
    except Exception as e:
        await cl.Message(
            content=f"❌ **模型初始化失败**\n\n请检查 API 密钥配置：\n```\n{str(e)}\n```\n\n"
                    f"💡 您可以在设置面板中输入 API Key 或配置环境变量。"
        ).send()
        return

    # 创建 HKEX Agent
    try:
        agent = await create_hkex_agent(
            model=model,
            assistant_id=cl.context.session.id,
            enable_mcp=config.enable_mcp,
            system_prompt=config.system_prompt,
            use_checkpointer=False,  # Chainlit has its own persistence
        )
        # 保存到用户会话
        cl.user_session.set("agent", agent)
        cl.user_session.set("thread_id", cl.context.session.id)
        
        if config.enable_mcp:
            await cl.Message(content="🔌 MCP 集成已启用", author="system").send()
            
    except Exception as e:
        await cl.Message(
            content=f"❌ **Agent 创建失败**\n\n```\n{str(e)}\n```"
        ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """处理用户消息，支持工具调用步骤显示。"""
    agent = cl.user_session.get("agent")
    thread_id = cl.user_session.get("thread_id")

    if not agent:
        await cl.Message(
            content="⚠️ Agent 未初始化，请刷新页面重试。"
        ).send()
        return

    # 获取并更新消息历史
    message_history = cl.user_session.get("message_history", [])
    
    # 添加当前用户消息到历史
    current_message = HumanMessage(content=message.content)
    message_history.append(current_message)

    # 配置
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    # 创建响应消息
    response_msg = cl.Message(content="")
    await response_msg.send()

    # 跟踪活跃的工具调用 Steps
    active_steps: dict[str, cl.Step] = {}

    try:
        # 流式处理 Agent 响应
        full_response = ""

        async for event in agent.astream(
            {"messages": message_history},
            config=config,
            stream_mode="messages",
        ):
            msg, metadata = event
            node = metadata.get("langgraph_node", "")

            # 1. 检测工具调用开始 --> 创建 Step
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get("name", "unknown")
                    tool_args = tool_call.get("args", {})
                    tool_id = tool_call.get("id", tool_name)

                    # 创建可折叠的工具调用卡片
                    step = cl.Step(name=tool_name, type="tool")
                    step.input = json.dumps(tool_args, ensure_ascii=False, indent=2)
                    await step.send()
                    active_steps[tool_id] = step

            # 2. 检测工具执行结果 --> 更新并关闭 Step
            if hasattr(msg, 'type') and msg.type == "tool":
                tool_id = getattr(msg, 'tool_call_id', None)
                if tool_id and tool_id in active_steps:
                    step = active_steps[tool_id]
                    
                    # 截断过长输出 (> 2000 字符)
                    content = str(msg.content)
                    if len(content) > 2000:
                        step.output = content[:2000] + "\n... [已截断]"
                    else:
                        step.output = content
                    
                    await step.update()
                    del active_steps[tool_id]

            # 3. 处理 AI 最终响应
            if hasattr(msg, 'content') and msg.content:
                if isinstance(msg, AIMessage) or node in ["agent", "final"]:
                    # 流式输出 token
                    await response_msg.stream_token(msg.content)
                    full_response += msg.content

        # 更新最终消息
        if full_response:
            response_msg.content = full_response
            await response_msg.update()
            # 将 AI 响应也添加到历史
            message_history.append(AIMessage(content=full_response))
        else:
            response_msg.content = "✅ 任务已完成"
            await response_msg.update()
        
        # 保存更新后的消息历史
        cl.user_session.set("message_history", message_history)

    except Exception as e:
        # 异常时关闭所有未完成的 Steps
        for step in active_steps.values():
            step.output = f"❌ 错误: {str(e)}"
            await step.update()
        
        error_msg = f"❌ **处理出错**\n\n```\n{str(e)}\n```"
        response_msg.content = error_msg
        await response_msg.update()


@cl.on_stop
async def on_stop():
    """处理用户停止请求。"""
    await cl.Message(content="⏹️ 已停止当前任务").send()


# 处理人机交互审批
@cl.action_callback("approve")
async def on_action_approve(action: cl.Action):
    """处理工具审批。"""
    await cl.Message(content="✅ 已批准执行").send()
    return "approve"


@cl.action_callback("reject")
async def on_action_reject(action: cl.Action):
    """处理工具拒绝。"""
    await cl.Message(content="❌ 已拒绝执行").send()
    return "reject"
