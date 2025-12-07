"""
HKEX Agent - Chainlit Web Interface

港股智能分析系统 Web 界面，基于 Chainlit 构建。
支持对话历史持久化、用户配置和恢复。
"""

import json
import logging
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Optional

# 配置日志
logger = logging.getLogger(__name__)

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
from chainlit.server import app as fastapi_app
from fastapi import HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel, EmailStr, field_validator
from langchain_core.messages import HumanMessage, AIMessage

from src.agents.main_agent import create_hkex_agent
from local_storage import LocalStorageClient
from config_models import (
    UserConfig,
    UserScene,
    APIProvider,
    MODEL_PRESETS,
    BUILTIN_SCENES,
    DEFAULT_SYSTEM_PROMPT,
    get_default_config,
    get_models_for_provider,
)

# 兼容旧代码
UserPreset = UserScene
BUILTIN_PRESETS = BUILTIN_SCENES
CONFIG_PRESETS = BUILTIN_SCENES
from config_storage import get_config_storage, init_config_storage
import auth_service

# ============== 数据持久化配置 ==============
# 使用 SQLite 存储对话历史
DB_PATH = project_root / "chainlit_data" / "chat_history.db"
STORAGE_PATH = project_root / "chainlit_data" / "files"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
STORAGE_PATH.mkdir(parents=True, exist_ok=True)

# ⭐ 自动初始化数据库（确保 users 表等存在）
from init_db import init_database
try:
    init_database()
    logger.info("数据库初始化完成")
except Exception as e:
    logger.warning(f"数据库初始化警告: {e}")

# 创建本地存储客户端
storage_client = LocalStorageClient(storage_dir=STORAGE_PATH)

# 初始化配置存储
config_storage = get_config_storage(DB_PATH)


# ============== 文件下载功能 ==============
async def check_and_send_file_download(tool_output: str, tool_name: str, config: "UserConfig" = None) -> None:
    """检测工具输出中的文件路径并提供下载链接。
    
    支持的文件类型：
    - Markdown (.md)
    - PDF (.pdf)
    - Excel (.xlsx, .xls)
    - JSON (.json)
    - 文本 (.txt)
    
    Args:
        tool_output: 工具输出内容
        tool_name: 工具名称
        config: 用户配置，用于检查是否启用下载链接
    """
    # 调试日志
    logger.debug(f"[文件下载检测] 工具: {tool_name}, 输出长度: {len(tool_output)}")
    
    # 检查是否启用下载链接
    if config and not getattr(config, 'show_download_links', True):
        logger.debug("[文件下载检测] 下载链接已禁用")
        return
    
    # 匹配常见文件路径模式
    # 支持 /md/xxx.md, /pdf_cache/xxx.pdf, ./xxx.xlsx 等格式
    # 注意：中文字符和特殊字符需要更宽松的匹配
    file_patterns = [
        r'(/md/[^\s\'"`,\[\]]+\.md)',  # /md/ 目录下的 markdown（排除方括号）
        r'(/pdf_cache/[^\s\'"`,\[\]]+\.(?:pdf|txt|json|xlsx|xls))',  # pdf_cache 目录
        r'(\.?/[^\s\'"`,\[\]]+\.(?:md|pdf|txt|json|xlsx|xls))',  # 相对路径（更宽松）
        r'([A-Za-z]:\\[^\s\'"`,\[\]]+\.(?:md|pdf|txt|json|xlsx|xls))',  # Windows 绝对路径
    ]
    
    found_files = set()
    for pattern in file_patterns:
        matches = re.findall(pattern, tool_output)
        if matches:
            logger.debug(f"[文件下载检测] 模式匹配到: {matches}")
        found_files.update(matches)
    
    # 如果没有找到文件，尝试更宽松的匹配
    if not found_files:
        logger.debug("[文件下载检测] 标准模式未匹配，尝试宽松匹配")
        # 匹配任何以 .md, .pdf, .txt, .json, .xlsx, .xls 结尾的路径
        loose_pattern = r'([^\s\'"`,\[\]]+\.(?:md|pdf|txt|json|xlsx|xls))'
        matches = re.findall(loose_pattern, tool_output)
        logger.debug(f"[文件下载检测] 宽松匹配结果: {matches}")
        for match in matches:
            # 过滤掉明显不是路径的匹配
            if '/' in match or '\\' in match or match.startswith('.'):
                found_files.add(match)
    
    logger.debug(f"[文件下载检测] 最终找到的文件: {found_files}")
    
    for file_path in found_files:
        actual_path = None
        
        # 转换虚拟路径到实际路径，并检查多个可能的位置
        # CompositeBackend 可能将文件路由到不同目录
        candidate_paths = []
        
        if file_path.startswith('/md/'):
            candidate_paths.append(project_root / 'md' / file_path[4:])
        elif file_path.startswith('/pdf_cache/'):
            candidate_paths.append(project_root / 'pdf_cache' / file_path[11:])
        elif file_path.startswith('./'):
            candidate_paths.append(project_root / file_path[2:])
        elif file_path.startswith('/'):
            # 检查是否是项目内的绝对路径
            if str(project_root) in file_path:
                candidate_paths.append(Path(file_path))
            else:
                # 对于根目录的文件，检查多个可能位置
                file_name = file_path[1:]  # 去掉开头的 /
                candidate_paths.append(project_root / file_name)
                # CompositeBackend 可能将 .md 文件路由到 /md/ 目录
                if file_name.endswith('.md'):
                    candidate_paths.append(project_root / 'md' / file_name)
                # 也检查 pdf_cache 目录
                if file_name.endswith(('.pdf', '.txt', '.json')):
                    candidate_paths.append(project_root / 'pdf_cache' / file_name)
        else:
            candidate_paths.append(project_root / file_path)
            # 也检查 md 和 pdf_cache 目录
            if file_path.endswith('.md'):
                candidate_paths.append(project_root / 'md' / file_path)
            if file_path.endswith(('.pdf', '.txt', '.json')):
                candidate_paths.append(project_root / 'pdf_cache' / file_path)
        
        # 查找第一个存在的文件
        for candidate in candidate_paths:
            logger.debug(f"[文件下载检测] 检查路径: {candidate}")
            if candidate.exists() and candidate.is_file():
                actual_path = candidate
                break
        
        if actual_path:
            try:
                # 创建 Chainlit 文件元素
                file_name = actual_path.name
                logger.debug(f"[文件下载检测] ✅ 文件存在，创建下载链接: {file_name}")
                
                # 发送文件下载链接
                elements = [
                    cl.File(
                        name=file_name,
                        path=str(actual_path),
                        display="inline",
                    )
                ]
                
                await cl.Message(
                    content=f"📎 **文件已生成**: `{file_name}`\n\n点击下方链接下载：",
                    elements=elements,
                ).send()
                
            except Exception as e:
                logger.warning(f"[文件下载检测] 创建下载链接失败: {actual_path}: {e}")
        else:
            logger.debug(f"[文件下载检测] 文件不存在于任何候选位置: {candidate_paths}")


# ============== 聊天记录分享功能 ==============
@cl.on_shared_thread_view
async def on_shared_thread_view(thread: dict, current_user: cl.User | None) -> bool:
    """处理共享聊天记录的访问请求。
    
    允许所有用户查看共享的聊天记录。
    
    Args:
        thread: 被分享的聊天线程
        current_user: 当前查看的用户（可能为 None，表示匿名用户）
        
    Returns:
        True 表示允许查看，False 表示拒绝
    """
    # 允许所有用户查看共享的聊天记录
    return True


@cl.data_layer
def get_data_layer():
    """配置 SQLite 数据持久化层（带本地文件存储）。"""
    return SQLAlchemyDataLayer(
        conninfo=f"sqlite+aiosqlite:///{DB_PATH}",
        storage_provider=storage_client,
    )


# ============== 用户注册 API ==============

class RegisterRequest(BaseModel):
    """用户注册请求模型。"""
    username: str
    password: str
    email: EmailStr
    display_name: str
    invite_code: str  # 邀请码（必填）
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式。"""
        if len(v) < 3:
            raise ValueError("用户名至少需要 3 个字符")
        if len(v) > 32:
            raise ValueError("用户名不能超过 32 个字符")
        if not v.isalnum() and "_" not in v:
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度。"""
        if len(v) < 6:
            raise ValueError("密码至少需要 6 个字符")
        return v
    
    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        """验证显示名称。"""
        if len(v) < 1:
            raise ValueError("显示名称不能为空")
        if len(v) > 64:
            raise ValueError("显示名称不能超过 64 个字符")
        return v
    
    @field_validator("invite_code")
    @classmethod
    def validate_invite_code(cls, v: str) -> str:
        """验证邀请码格式。"""
        if not v or len(v.strip()) == 0:
            raise ValueError("请输入邀请码")
        return v.strip().upper()


@fastapi_app.post("/api/register")
async def register_user(req: RegisterRequest):
    """用户注册 API。
    
    创建新用户账户，需要有效邀请码。
    密码使用 bcrypt 加密存储。
    """
    try:
        # 1. 验证邀请码
        valid, message = auth_service.validate_invite_code(req.invite_code)
        if not valid:
            raise HTTPException(status_code=400, detail=message)
        
        # 2. 创建用户
        user = auth_service.create_user(
            username=req.username,
            password=req.password,
            email=req.email,
            display_name=req.display_name,
            role="USER"
        )
        
        # 3. 标记邀请码已使用
        auth_service.use_invite_code(req.invite_code, req.username)
        
        return {
            "success": True,
            "message": "注册成功",
            "user": {
                "username": user["identifier"],
                "email": user["email"],
                "display_name": user["display_name"]
            }
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("注册失败")
        raise HTTPException(status_code=500, detail="注册失败，请稍后重试")


@fastapi_app.get("/register")
async def register_page():
    """重定向到注册页面。"""
    return RedirectResponse(url="/public/register.html", status_code=302)


class CheckUsernameRequest(BaseModel):
    """检查用户名请求模型。"""
    username: str


class CheckEmailRequest(BaseModel):
    """检查邮箱请求模型。"""
    email: str


@fastapi_app.post("/api/check-username")
async def check_username(req: CheckUsernameRequest):
    """检查用户名是否可用。"""
    user = auth_service.get_user_by_username(req.username)
    return {"available": user is None}


@fastapi_app.post("/api/check-email")
async def check_email(req: CheckEmailRequest):
    """检查邮箱是否可用。"""
    user = auth_service.get_user_by_email(req.email)
    return {"available": user is None}


# ============== 邀请码 API ==============

class CheckInviteCodeRequest(BaseModel):
    """检查邀请码请求模型。"""
    invite_code: str


@fastapi_app.post("/api/check-invite-code")
async def check_invite_code(req: CheckInviteCodeRequest):
    """检查邀请码是否有效。"""
    valid, message = auth_service.validate_invite_code(req.invite_code)
    return {"valid": valid, "message": message}


class GenerateInviteCodeRequest(BaseModel):
    """生成邀请码请求模型。"""
    max_uses: int = 1
    expires_days: Optional[int] = None
    note: Optional[str] = None


@fastapi_app.post("/api/admin/invite-codes")
async def generate_invite_code(req: GenerateInviteCodeRequest):
    """生成新邀请码（管理员接口）。
    
    注意：生产环境应添加管理员权限验证。
    """
    try:
        invite = auth_service.generate_invite_code(
            max_uses=req.max_uses,
            expires_days=req.expires_days,
            note=req.note
        )
        return {"success": True, "invite_code": invite}
    except Exception as e:
        logger.exception("生成邀请码失败")
        raise HTTPException(status_code=500, detail="生成邀请码失败")


@fastapi_app.get("/api/admin/invite-codes")
async def list_invite_codes():
    """列出所有邀请码（管理员接口）。
    
    注意：生产环境应添加管理员权限验证。
    """
    codes = auth_service.list_invite_codes()
    return {"invite_codes": codes}


class DeleteInviteCodeRequest(BaseModel):
    """删除邀请码请求模型。"""
    code: str


@fastapi_app.delete("/api/admin/invite-codes")
async def delete_invite_code(req: DeleteInviteCodeRequest):
    """删除邀请码（管理员接口）。
    
    注意：生产环境应添加管理员权限验证。
    """
    success = auth_service.delete_invite_code(req.code)
    if success:
        return {"success": True, "message": "邀请码已删除"}
    raise HTTPException(status_code=404, detail="邀请码不存在")


# ============== 用户预设管理 API ==============

class PresetRequest(BaseModel):
    """预设请求模型。"""
    id: str
    name: str
    description: str = ""
    temperature: float = 0.7
    max_tokens: int = 8000
    top_p: float = 0.9


@fastapi_app.get("/api/presets")
async def get_presets():
    """获取所有可用预设（内置 + 用户自定义）。
    
    需要用户登录，从 session 获取用户 ID。
    """
    # 注意：这个 API 不需要认证，返回内置预设
    # 用户自定义预设需要通过 Chainlit session 获取
    return {
        "builtin": [
            {"id": k, **v}
            for k, v in BUILTIN_PRESETS.items()
        ],
        "user_scenes": []  # 用户预设需要通过 Chainlit session 获取
    }


# ============== 提示词管理 API ==============

PROMPTS_DIR = project_root / "src" / "prompts"
# 内置提示词（不可删除）
BUILTIN_PROMPTS = {"main_system_prompt.md", "pdf_analyzer_prompt.md", "report_generator_prompt.md", "longterm_memory_prompt.md", "default_agent_md.md"}


@fastapi_app.get("/api/prompts")
async def list_prompts():
    """列出所有可用的提示词文件。"""
    prompts = []
    if PROMPTS_DIR.exists():
        for f in PROMPTS_DIR.glob("*.md"):
            is_builtin = f.name in BUILTIN_PROMPTS
            prompts.append({
                "name": f.stem,  # 不带扩展名
                "filename": f.name,
                "builtin": is_builtin,
                "deletable": not is_builtin,
            })
    # 按名称排序，内置在前
    prompts.sort(key=lambda x: (not x["builtin"], x["name"]))
    return {"prompts": prompts}


@fastapi_app.get("/api/prompts/{filename}")
async def read_prompt(filename: str):
    """读取指定提示词文件内容。"""
    # 安全检查：防止路径遍历
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
    
    file_path = PROMPTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="提示词不存在")
    
    try:
        content = file_path.read_text(encoding="utf-8")
        return {
            "filename": filename,
            "name": file_path.stem,
            "content": content,
            "builtin": filename in BUILTIN_PROMPTS,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取失败: {e}")


class PromptSaveRequest(BaseModel):
    """保存提示词请求。"""
    filename: str
    content: str


@fastapi_app.post("/api/prompts")
async def save_prompt(req: PromptSaveRequest):
    """保存/更新提示词文件。"""
    filename = req.filename
    
    # 安全检查
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
    
    # 确保是 .md 文件
    if not filename.endswith(".md"):
        filename = filename + ".md"
    
    file_path = PROMPTS_DIR / filename
    
    try:
        PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
        file_path.write_text(req.content, encoding="utf-8")
        return {
            "success": True,
            "filename": filename,
            "message": "提示词已保存",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {e}")


@fastapi_app.delete("/api/prompts/{filename}")
async def delete_prompt(filename: str):
    """删除提示词文件（仅可删除用户创建的）。"""
    # 安全检查
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
    
    # 检查是否为内置提示词
    if filename in BUILTIN_PROMPTS:
        raise HTTPException(status_code=403, detail="无法删除内置提示词")
    
    file_path = PROMPTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="提示词不存在")
    
    try:
        file_path.unlink()
        return {"success": True, "message": "提示词已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {e}")


# ============== 用户认证 ==============
@cl.password_auth_callback
async def auth_callback(username: str, password: str):
    """
    密码认证回调。
    
    通过数据库验证注册用户，无默认账号。
    新用户需要通过注册页面创建账号。
    
    注意：必须返回 PersistedUser 才能正确关联用户到对话（用于分享功能）。
    """
    from chainlit.data import get_data_layer
    
    # 从数据库验证用户
    authenticated_user = auth_service.authenticate_user(username, password)
    
    if not authenticated_user:
        # 验证失败，无默认账号
        return None
    
    # 用户验证成功
    user = cl.User(
        identifier=authenticated_user["identifier"],
        metadata={
            "role": authenticated_user.get("role", "USER"),
            "provider": "credentials",
            "email": authenticated_user.get("email"),
            "display_name": authenticated_user.get("display_name")
        }
    )
    
    # 使用数据层创建或获取 PersistedUser，以便正确关联用户到对话
    data_layer = get_data_layer()
    if data_layer:
        try:
            persisted_user = await data_layer.create_user(user)
            if persisted_user:
                return persisted_user
        except Exception as e:
            logger.warning(f"Failed to persist user: {e}")
    
    # 如果数据层不可用，返回普通用户（分享功能可能不可用）
    return user


# ============== 配置辅助函数 ==============
def create_model_from_config(config: UserConfig):
    """根据用户配置创建模型实例.
    
    Args:
        config: 用户配置对象
        
    Returns:
        LangChain Chat 模型实例
    """
    # 获取实际使用的模型名称（自定义优先）
    effective_model = config.get_effective_model()
    
    # 获取 API Key（优先使用用户配置，否则使用环境变量）
    if config.provider == APIProvider.SILICONFLOW.value:
        api_key = config.api_key_override or os.environ.get("SILICONFLOW_API_KEY")
        if not api_key:
            raise ValueError("未配置 SiliconFlow API Key")
        
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=effective_model,
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
            model=effective_model,
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
            model_name=effective_model,
            api_key=api_key,
            max_tokens=config.max_tokens,
            # Anthropic 不支持 top_p 等参数
        )
    
    elif config.provider == APIProvider.OPENROUTER.value:
        api_key = config.api_key_override or os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("未配置 OpenRouter API Key")
        
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=effective_model,
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            frequency_penalty=config.frequency_penalty,
            presence_penalty=config.presence_penalty,
            default_headers={
                "HTTP-Referer": "https://github.com/deepagents-hk",
                "X-Title": "HKEX Agent",
            },
        )
    
    else:
        raise ValueError(f"不支持的 API Provider: {config.provider}")


def get_all_scenes(user_scenes: list = None) -> dict:
    """获取所有场景（内置 + 用户自定义）.
    
    Args:
        user_scenes: 用户自定义场景列表
        
    Returns:
        场景字典 {scene_id: scene_data}
    """
    all_scenes = dict(BUILTIN_SCENES)
    if user_scenes:
        for s in user_scenes:
            all_scenes[f"user:{s.id}"] = s.to_scene_dict()
    return all_scenes


def build_settings_widgets(config: UserConfig) -> list:
    """构建设置面板组件 - 简洁布局.
    
    分为三部分：
    1. API/模型 - 选择Provider和模型
    2. 提示词 - 系统提示词编辑
    3. 参数 - 模型参数调节
    
    Args:
        config: 当前用户配置
        
    Returns:
        Chainlit 输入组件列表
    """
    # 获取当前 provider 的模型列表
    models = get_models_for_provider(config.provider)
    model_options = [m["id"] for m in models]
    
    return [
        # ═══════════════════════════════════════════
        # 第一部分：🔧 API/模型
        # ═══════════════════════════════════════════
        Select(
            id="provider",
            label="🔧 API Provider",
            description="选择 AI 模型提供商",
            values=APIProvider.choices(),
            initial_value=config.provider,
        ),
        Select(
            id="model",
            label="模型",
            description="选择预设模型",
            values=model_options if model_options else ["deepseek-chat"],
            initial_value=config.model if config.model in model_options else (model_options[0] if model_options else "deepseek-chat"),
        ),
        TextInput(
            id="custom_model",
            label="自定义模型",
            description="填写后优先使用此模型（可选）",
            initial=config.custom_model or "",
            placeholder="例如: anthropic/claude-sonnet-4",
        ),
        TextInput(
            id="api_key_override",
            label="API Key",
            description="覆盖环境变量（可选）",
            initial=config.api_key_override or "",
            placeholder="sk-...",
        ),
        
        # ═══════════════════════════════════════════
        # 第二部分：📝 提示词
        # ═══════════════════════════════════════════
        TextInput(
            id="system_prompt_edit",
            label="📝 系统提示词",
            description="定义 AI 角色和行为",
            initial=config.system_prompt,
            placeholder="输入系统提示词...",
        ),
        
        # ═══════════════════════════════════════════
        # 第三部分：📊 参数
        # ═══════════════════════════════════════════
        Slider(
            id="temperature",
            label="📊 Temperature",
            description="控制输出随机性 (0=确定性, 1=创意性)",
            min=0.0,
            max=1.5,
            step=0.1,
            initial=config.temperature,
        ),
        TextInput(
            id="max_tokens",
            label="Max Tokens",
            description="最大输出 Token 数",
            initial=str(config.max_tokens),
            placeholder="8000",
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
        
        # ═══════════════════════════════════════════
        # 其他设置
        # ═══════════════════════════════════════════
        Switch(
            id="enable_mcp",
            label="⚙️ 启用 MCP 集成",
            description="启用 Model Context Protocol 扩展",
            initial=config.enable_mcp,
        ),
        Switch(
            id="auto_approve",
            label="自动审批工具调用",
            description="关闭后需手动审批危险操作",
            initial=config.auto_approve,
        ),
        Switch(
            id="test_connection",
            label="🔌 测试连接",
            description="开启后点击确认测试模型",
            initial=False,
        ),
    ]


def settings_to_config(settings: dict, current_config: UserConfig) -> UserConfig:
    """将设置面板值转换为配置对象.
    
    Args:
        settings: 设置面板返回的字典
        current_config: 当前配置
        
    Returns:
        更新后的 UserConfig 对象
    """
    # 处理自定义模型
    custom_model = settings.get("custom_model", current_config.custom_model)
    if custom_model:
        custom_model = custom_model.strip() or None
    
    # 处理 max_tokens
    max_tokens_raw = settings.get("max_tokens", current_config.max_tokens)
    try:
        max_tokens = int(max_tokens_raw) if max_tokens_raw else current_config.max_tokens
    except (ValueError, TypeError):
        max_tokens = current_config.max_tokens
    
    # 处理提示词
    edited_prompt = settings.get("system_prompt_edit", "")
    new_system_prompt = edited_prompt if edited_prompt else current_config.system_prompt
    
    return UserConfig(
        provider=settings.get("provider", current_config.provider),
        model=settings.get("model", current_config.model),
        custom_model=custom_model,
        api_key_override=settings.get("api_key_override") or None,
        temperature=settings.get("temperature", current_config.temperature),
        max_tokens=max_tokens,
        top_p=settings.get("top_p", current_config.top_p),
        system_prompt=new_system_prompt,
        enable_mcp=settings.get("enable_mcp", current_config.enable_mcp),
        auto_approve=settings.get("auto_approve", current_config.auto_approve),
        show_download_links=current_config.show_download_links,
    )


# ============== 模型连接测试 ==============
async def test_model_connection(config: UserConfig) -> tuple[bool, str, float]:
    """测试模型连接是否正常.
    
    Args:
        config: 用户配置
        
    Returns:
        (成功与否, 消息, 响应时间秒)
    """
    import time
    
    try:
        model = create_model_from_config(config)
        effective_model = config.get_effective_model()
        
        # 发送简单测试消息
        start_time = time.time()
        response = await model.ainvoke([{"role": "user", "content": "Hi, respond with just 'OK'"}])
        elapsed = time.time() - start_time
        
        # 检查响应
        content = response.content if hasattr(response, 'content') else str(response)
        if content:
            return True, f"模型 `{effective_model}` 响应正常", elapsed
        else:
            return False, f"模型 `{effective_model}` 返回空响应", elapsed
            
    except Exception as e:
        error_msg = str(e)
        # 提取关键错误信息
        if "401" in error_msg or "Unauthorized" in error_msg:
            return False, "❌ API Key 无效或已过期", 0
        elif "404" in error_msg or "not found" in error_msg.lower():
            return False, f"❌ 模型 `{config.get_effective_model()}` 不存在", 0
        elif "rate limit" in error_msg.lower() or "429" in error_msg:
            return False, "❌ API 请求频率超限，请稍后重试", 0
        elif "timeout" in error_msg.lower():
            return False, "❌ 连接超时，请检查网络", 0
        else:
            return False, f"❌ 连接失败: {error_msg[:100]}", 0


@cl.action_callback("test_connection")
async def on_test_connection(action: cl.Action):
    """处理测试连接按钮点击."""
    config = cl.user_session.get("config")
    if not config:
        await cl.Message(content="⚠️ 配置未加载，请刷新页面", author="system").send()
        return
    
    # 显示测试中状态
    test_msg = cl.Message(content="🔄 **正在测试连接...**", author="system")
    await test_msg.send()
    
    # 执行测试
    success, message, elapsed = await test_model_connection(config)
    
    # 更新消息显示结果
    if success:
        test_msg.content = (
            f"✅ **连接测试成功**\n\n"
            f"- {message}\n"
            f"- 响应时间: {elapsed:.2f} 秒"
        )
    else:
        test_msg.content = (
            f"**连接测试失败**\n\n"
            f"- {message}\n\n"
            f"💡 请检查 API Key 和模型名称是否正确"
        )
    
    await test_msg.update()


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
    
    # 转换设置为配置
    new_config = settings_to_config(settings, current_config)
    
    # 验证配置
    errors = new_config.validate()
    if errors:
        await cl.Message(
            content=f"⚠️ **配置验证失败**\n\n" + "\n".join(f"- {e}" for e in errors),
            author="system",
        ).send()
        return
    
    # 检查 provider 是否变更
    provider_changed = new_config.provider != current_config.provider
    
    # 如果 provider 变更，重置模型
    if provider_changed:
        models = get_models_for_provider(new_config.provider)
        if models:
            new_config.model = models[0]["id"]
    
    # 保存配置
    await config_storage.save_config(user_id, new_config)
    cl.user_session.set("config", new_config)
    
    # 如果 provider 变更，刷新设置面板
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
            enable_hitl=not new_config.auto_approve,  # 自动审批 = 禁用 HITL
        )
        cl.user_session.set("agent", agent)
        
        # 显示更新成功消息
        provider_name = APIProvider.display_names().get(new_config.provider, new_config.provider)
        
        await cl.Message(
            content=f"✅ **配置已更新**\n\n"
                    f"📡 Provider: {provider_name}\n"
                    f"🤖 模型: {new_config.get_model_display_name()}\n"
                    f"📊 参数: T={new_config.temperature}, {new_config.max_tokens//1000}K, P={new_config.top_p}",
            author="system",
        ).send()
        
        # 检查是否需要测试连接
        should_test = settings.get("test_connection", False)
        if should_test:
            # 显示测试中状态
            test_msg = cl.Message(content="🔄 **正在测试连接...**", author="system")
            await test_msg.send()
            
            # 执行测试
            success, message, elapsed = await test_model_connection(new_config)
            
            # 更新消息显示结果
            if success:
                test_msg.content = (
                    f"✅ **连接测试成功**\n\n"
                    f"- {message}\n"
                    f"- 响应时间: {elapsed:.2f} 秒"
                )
            else:
                test_msg.content = (
                    f"**连接测试失败**\n\n"
                    f"- {message}\n\n"
                    f"💡 请检查 API Key 和模型名称是否正确"
                )
            
            await test_msg.update()
        
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
            enable_hitl=not config.auto_approve,  # 自动审批 = 禁用 HITL
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
                "- 📄 解析 PDF / Excel 文档\n"
                "- 📊 生成分析报告\n"
                "- 💹 查询股票信息\n\n"
                f"当前配置：**{provider_name}** / **{config.get_model_display_name()}**\n\n"
                "💡 点击底部 ⚙️ 图标可修改设置，拖拽或点击 📎 上传文件。"
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
            enable_hitl=not config.auto_approve,  # 自动审批 = 禁用 HITL
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
    """处理用户消息，支持工具调用步骤显示和文件上传。"""
    agent = cl.user_session.get("agent")
    thread_id = cl.user_session.get("thread_id")

    if not agent:
        await cl.Message(
            content="⚠️ Agent 未初始化，请刷新页面重试。"
        ).send()
        return

    # 处理 /upload 命令 - 主动请求文件上传
    if message.content.strip().lower() in ["/upload", "/上传", "上传文件"]:
        files = await cl.AskFileMessage(
            content="请上传文件进行分析（支持 PDF、Excel）：",
            accept=["*/*"],  # 接受所有文件类型
            max_size_mb=100,
            max_files=5,
            timeout=180,
        ).send()
        
        if files:
            uploaded_files_info = []
            for file in files:
                # 复制到 pdf_cache/uploads 目录
                cache_dir = project_root / "pdf_cache" / "uploads"
                cache_dir.mkdir(parents=True, exist_ok=True)
                dest_path = cache_dir / file.name
                shutil.copy2(file.path, dest_path)
                uploaded_files_info.append(f"✅ `{file.name}` -> `{dest_path}`")
            
            await cl.Message(
                content=f"📎 **文件上传成功**\n\n" + "\n".join(uploaded_files_info) + 
                        "\n\n现在您可以要求我分析这些文件。"
            ).send()
        else:
            await cl.Message(content="❌ 未收到文件").send()
        return

    # 处理上传的文件附件（通过拖拽或点击附件按钮）
    uploaded_files_info = []
    
    # 支持的文件类型
    SUPPORTED_EXTENSIONS = {'.pdf', '.xlsx', '.xls'}
    SUPPORTED_MIMES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
    }
    
    if message.elements:
        for element in message.elements:
            # 获取文件信息
            file_path = getattr(element, 'path', None)
            file_name = getattr(element, 'name', None)
            file_mime = getattr(element, 'mime', None)
            
            if file_path and file_name:
                file_ext = Path(file_name).suffix.lower()
                
                # 如果是支持的文件类型，复制到 pdf_cache/uploads 目录
                if file_mime in SUPPORTED_MIMES or file_ext in SUPPORTED_EXTENSIONS:
                    cache_dir = project_root / "pdf_cache" / "uploads"
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    dest_path = cache_dir / file_name
                    
                    if Path(file_path).exists():
                        shutil.copy2(file_path, dest_path)
                        file_type = "Excel" if file_ext in {'.xlsx', '.xls'} else "PDF"
                        uploaded_files_info.append(f"已上传 {file_type}: {dest_path}")
                else:
                    # 其他文件类型
                    uploaded_files_info.append(f"已上传文件: {file_name} ({file_mime})")
    
    # 构建消息内容（包含上传文件信息）
    user_content = message.content
    if uploaded_files_info:
        files_summary = "\n".join(uploaded_files_info)
        user_content = f"{message.content}\n\n[用户上传的文件]\n{files_summary}"
        await cl.Message(content=f"📎 {files_summary}").send()

    # 获取并更新消息历史
    message_history = cl.user_session.get("message_history", [])
    
    # 添加当前用户消息到历史
    current_message = HumanMessage(content=user_content)
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

        # 单流模式：messages 获取流式消息
        async for event in agent.astream(
            {"messages": message_history},
            config=config,
            stream_mode="messages",
        ):
            msg, metadata = event
            node = metadata.get("langgraph_node", "")
            
            # 1. 检测工具调用 - 支持 tool_calls 和 tool_call_chunks
            # AIMessage 使用 tool_calls，AIMessageChunk 使用 tool_call_chunks
            tool_calls_list = []
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_calls_list = msg.tool_calls
            elif hasattr(msg, 'tool_call_chunks') and msg.tool_call_chunks:
                tool_calls_list = msg.tool_call_chunks
            
            if tool_calls_list:
                for tool_call in tool_calls_list:
                    # 兼容字典格式
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get("name", "") or ""
                        tool_args = tool_call.get("args", {})
                        tool_id = tool_call.get("id", "")
                    else:
                        tool_name = getattr(tool_call, "name", "") or ""
                        tool_args = getattr(tool_call, "args", {})
                        tool_id = getattr(tool_call, "id", "")
                    
                    # 跳过空名称或已处理的工具
                    if not tool_name or tool_id in active_steps:
                        continue
                    
                    # 记录工具调用信息
                    active_steps[tool_id] = {
                        "name": tool_name,
                        "args": tool_args if isinstance(tool_args, dict) else {},
                        "step": None,
                    }

            # 2. 检测工具执行结果 --> 创建并完成 Step
            if hasattr(msg, 'type') and msg.type == "tool":
                tool_id = getattr(msg, 'tool_call_id', None)
                tool_name = getattr(msg, 'name', 'unknown')
                
                # 获取工具调用信息
                tool_info = active_steps.get(tool_id, {})
                if isinstance(tool_info, dict) and "name" in tool_info:
                    display_name = tool_info.get("name", tool_name)
                    display_args = tool_info.get("args", {})
                else:
                    display_name = tool_name
                    display_args = {}
                
                # 创建并完成 Step（一次性显示输入和输出）
                step = cl.Step(name=display_name, type="tool")
                step.input = json.dumps(display_args, ensure_ascii=False, indent=2) if display_args else ""
                
                # 截断过长输出
                content = str(msg.content)
                if len(content) > 2000:
                    step.output = content[:2000] + "\n... [已截断]"
                else:
                    step.output = content
                
                await step.send()
                
                # 检测生成的文件并提供下载链接
                user_config = cl.user_session.get("config")
                await check_and_send_file_download(content, display_name, user_config)
                
                # 清理
                if tool_id in active_steps:
                    del active_steps[tool_id]

            # 3. 处理 AI 最终响应
            # AIMessageChunk 是流式消息块，也需要处理
            if hasattr(msg, 'content') and msg.content:
                msg_type = type(msg).__name__
                if msg_type in ["AIMessage", "AIMessageChunk"] or node in ["agent", "model", "final"]:
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
        import traceback
        print(f"[ERROR] Exception in on_message: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        
        # 异常时关闭所有未完成的 Steps
        for tool_info in active_steps.values():
            if isinstance(tool_info, dict) and tool_info.get("step"):
                step = tool_info["step"]
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
