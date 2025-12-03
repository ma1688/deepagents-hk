"""
HKEX Agent - Chainlit Web Interface

港股智能分析系统 Web 界面，基于 Chainlit 构建。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import chainlit as cl
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage

from src.cli.config import create_model
from src.agents.main_agent import create_hkex_agent


@cl.on_chat_start
async def on_chat_start():
    """初始化聊天会话，创建 HKEX Agent。"""
    # 发送欢迎消息
    await cl.Message(
        content="🏛️ **港股智能分析系统** 已就绪！\n\n"
                "我可以帮助您：\n"
                "- 📰 搜索和分析港交所公告\n"
                "- 📄 解析 PDF 文档\n"
                "- 📊 生成分析报告\n"
                "- 💹 查询股票信息\n\n"
                "请输入您的问题或指令开始分析。"
    ).send()

    # 创建模型
    try:
        model = create_model()
    except Exception as e:
        await cl.Message(
            content=f"❌ **模型初始化失败**\n\n请检查 API 密钥配置：\n```\n{str(e)}\n```"
        ).send()
        return

    # 检查是否启用 MCP
    enable_mcp = os.getenv("ENABLE_MCP", "false").lower() == "true"

    # 创建 HKEX Agent
    try:
        agent = await create_hkex_agent(
            model=model,
            assistant_id=cl.context.session.id,
            enable_mcp=enable_mcp,
        )
        # 保存到用户会话
        cl.user_session.set("agent", agent)
        cl.user_session.set("thread_id", cl.context.session.id)
        
        if enable_mcp:
            await cl.Message(content="🔌 MCP 集成已启用").send()
            
    except Exception as e:
        await cl.Message(
            content=f"❌ **Agent 创建失败**\n\n```\n{str(e)}\n```"
        ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """处理用户消息。"""
    agent = cl.user_session.get("agent")
    thread_id = cl.user_session.get("thread_id")

    if not agent:
        await cl.Message(
            content="⚠️ Agent 未初始化，请刷新页面重试。"
        ).send()
        return

    # 配置
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    # 创建响应消息
    response_msg = cl.Message(content="")
    await response_msg.send()

    try:
        # 流式处理 Agent 响应
        full_response = ""
        tool_calls_info = []

        async for event in agent.astream(
            {"messages": [HumanMessage(content=message.content)]},
            config=config,
            stream_mode="messages",
        ):
            msg, metadata = event
            
            # 处理 AI 消息内容
            if hasattr(msg, 'content') and msg.content:
                if isinstance(msg, AIMessage) or metadata.get("langgraph_node") in ["agent", "final"]:
                    # 流式输出 token
                    await response_msg.stream_token(msg.content)
                    full_response += msg.content

            # 收集工具调用信息
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_calls_info.append({
                        "name": tool_call.get("name", "unknown"),
                        "args": tool_call.get("args", {}),
                    })

        # 如果有工具调用，显示工具使用信息
        if tool_calls_info:
            tools_used = ", ".join([t["name"] for t in tool_calls_info])
            await cl.Message(
                content=f"🔧 *使用工具: {tools_used}*",
                author="system",
            ).send()

        # 更新最终消息
        if full_response:
            response_msg.content = full_response
            await response_msg.update()
        else:
            response_msg.content = "✅ 任务已完成"
            await response_msg.update()

    except Exception as e:
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

