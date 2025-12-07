"""
用户认证服务 - 处理用户注册、登录验证

提供密码哈希、用户创建和验证功能。
支持邀请码机制控制注册。
"""

import secrets
import sqlite3
import string
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import bcrypt

# 数据库路径
project_root = Path(__file__).parent.parent.resolve()
DB_PATH = project_root / "chainlit_data" / "chat_history.db"


# ============== 邀请码功能 ==============

def init_invite_codes_table():
    """初始化邀请码表。"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invite_codes (
            id TEXT PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            created_by TEXT,
            created_at TEXT NOT NULL,
            used_by TEXT,
            used_at TEXT,
            max_uses INTEGER DEFAULT 1,
            use_count INTEGER DEFAULT 0,
            expires_at TEXT,
            note TEXT
        )
    """)
    
    conn.commit()
    conn.close()


def generate_invite_code(
    created_by: Optional[str] = None,
    max_uses: int = 1,
    expires_days: Optional[int] = None,
    note: Optional[str] = None,
    code_length: int = 8
) -> dict:
    """生成新的邀请码。
    
    Args:
        created_by: 创建者用户名
        max_uses: 最大使用次数，默认1次
        expires_days: 过期天数，None表示永不过期
        note: 备注信息
        code_length: 邀请码长度，默认8位
        
    Returns:
        邀请码信息字典
    """
    init_invite_codes_table()
    
    # 生成随机邀请码 (大写字母+数字)
    alphabet = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(alphabet) for _ in range(code_length))
    
    code_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat() + "Z"
    
    expires_at = None
    if expires_days:
        from datetime import timedelta
        expires_at = (datetime.utcnow() + timedelta(days=expires_days)).isoformat() + "Z"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT INTO invite_codes (id, code, created_by, created_at, max_uses, expires_at, note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (code_id, code, created_by, created_at, max_uses, expires_at, note)
    )
    
    conn.commit()
    conn.close()
    
    return {
        "id": code_id,
        "code": code,
        "created_by": created_by,
        "created_at": created_at,
        "max_uses": max_uses,
        "use_count": 0,
        "expires_at": expires_at,
        "note": note
    }


def validate_invite_code(code: str) -> tuple[bool, str]:
    """验证邀请码是否有效。
    
    Args:
        code: 邀请码
        
    Returns:
        (是否有效, 错误信息或成功信息)
    """
    init_invite_codes_table()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM invite_codes WHERE code = ?",
        (code.upper(),)
    )
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return False, "邀请码无效"
    
    invite = dict(row)
    
    # 检查使用次数
    if invite["use_count"] >= invite["max_uses"]:
        return False, "邀请码已达到使用上限"
    
    # 检查是否过期
    if invite["expires_at"]:
        expires = datetime.fromisoformat(invite["expires_at"].replace("Z", "+00:00"))
        if datetime.utcnow().replace(tzinfo=expires.tzinfo) > expires:
            return False, "邀请码已过期"
    
    return True, "邀请码有效"


def use_invite_code(code: str, used_by: str) -> bool:
    """使用邀请码（增加使用计数）。
    
    Args:
        code: 邀请码
        used_by: 使用者用户名
        
    Returns:
        是否成功使用
    """
    valid, _ = validate_invite_code(code)
    if not valid:
        return False
    
    used_at = datetime.utcnow().isoformat() + "Z"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        """
        UPDATE invite_codes 
        SET use_count = use_count + 1, used_by = ?, used_at = ?
        WHERE code = ?
        """,
        (used_by, used_at, code.upper())
    )
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    return affected > 0


def list_invite_codes() -> list[dict]:
    """列出所有邀请码（管理用）。
    
    Returns:
        邀请码列表
    """
    init_invite_codes_table()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT * FROM invite_codes ORDER BY created_at DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def delete_invite_code(code: str) -> bool:
    """删除邀请码。
    
    Args:
        code: 邀请码
        
    Returns:
        是否成功删除
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM invite_codes WHERE code = ?", (code.upper(),))
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    return affected > 0


def hash_password(password: str) -> str:
    """使用 bcrypt 对密码进行哈希。
    
    Args:
        password: 明文密码
        
    Returns:
        密码哈希字符串
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码是否匹配哈希。
    
    Args:
        password: 明文密码
        password_hash: 存储的密码哈希
        
    Returns:
        密码是否匹配
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def get_user_by_username(username: str) -> Optional[dict]:
    """根据用户名查询用户。
    
    Args:
        username: 用户名 (identifier)
        
    Returns:
        用户信息字典，或 None
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, identifier, metadata, createdAt, password_hash, email, display_name, is_active
        FROM users WHERE identifier = ?
        """,
        (username,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_user_by_email(email: str) -> Optional[dict]:
    """根据邮箱查询用户。
    
    Args:
        email: 用户邮箱
        
    Returns:
        用户信息字典，或 None
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, identifier, metadata, createdAt, password_hash, email, display_name, is_active
        FROM users WHERE email = ?
        """,
        (email,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def create_user(
    username: str,
    password: str,
    email: str,
    display_name: str,
    role: str = "USER"
) -> dict:
    """创建新用户。
    
    Args:
        username: 用户名 (唯一标识符)
        password: 明文密码
        email: 用户邮箱
        display_name: 显示名称
        role: 用户角色，默认 "USER"
        
    Returns:
        创建的用户信息字典
        
    Raises:
        ValueError: 用户名或邮箱已存在
    """
    # 检查用户名是否已存在
    if get_user_by_username(username):
        raise ValueError(f"用户名 '{username}' 已被使用")
    
    # 检查邮箱是否已存在
    if email and get_user_by_email(email):
        raise ValueError(f"邮箱 '{email}' 已被注册")
    
    # 生成用户 ID 和密码哈希
    user_id = str(uuid.uuid4())
    password_hash = hash_password(password)
    created_at = datetime.utcnow().isoformat() + "Z"
    
    # 构建 metadata JSON
    import json
    metadata = json.dumps({
        "role": role,
        "provider": "credentials",
        "display_name": display_name
    })
    
    # 插入用户
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT INTO users (id, identifier, metadata, createdAt, password_hash, email, display_name, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (user_id, username, metadata, created_at, password_hash, email, display_name)
    )
    
    conn.commit()
    conn.close()
    
    return {
        "id": user_id,
        "identifier": username,
        "email": email,
        "display_name": display_name,
        "role": role,
        "createdAt": created_at
    }


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """验证用户登录。
    
    Args:
        username: 用户名
        password: 明文密码
        
    Returns:
        验证成功返回用户信息，失败返回 None
    """
    user = get_user_by_username(username)
    
    if not user:
        return None
    
    # 检查用户是否激活
    if not user.get("is_active", 1):
        return None
    
    # 检查密码
    password_hash = user.get("password_hash")
    if not password_hash:
        # 无密码哈希的用户无法登录，必须通过注册创建账号
        return None
    
    # 验证密码哈希
    if not verify_password(password, password_hash):
        return None
    
    # 解析 metadata 获取角色
    import json
    metadata = {}
    if user.get("metadata"):
        try:
            metadata = json.loads(user["metadata"])
        except json.JSONDecodeError:
            pass
    
    return {
        "id": user["id"],
        "identifier": user["identifier"],
        "email": user.get("email"),
        "display_name": user.get("display_name") or metadata.get("display_name"),
        "role": metadata.get("role", "USER")
    }


def update_user_password(username: str, new_password: str) -> bool:
    """更新用户密码。
    
    Args:
        username: 用户名
        new_password: 新密码
        
    Returns:
        更新是否成功
    """
    user = get_user_by_username(username)
    if not user:
        return False
    
    password_hash = hash_password(new_password)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE identifier = ?",
        (password_hash, username)
    )
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    return affected > 0


def list_users() -> list[dict]:
    """列出所有用户（用于管理）。
    
    Returns:
        用户列表
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, identifier, email, display_name, is_active, createdAt, metadata
        FROM users ORDER BY createdAt DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

