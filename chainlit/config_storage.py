"""
配置持久化层 - SQLite 存储用户配置和自定义预设

扩展现有 SQLite 数据库，实现用户配置和预设的存储和加载。
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import aiosqlite

from config_models import UserConfig, get_default_config, UserScene

# 兼容别名
UserPreset = UserScene


class ConfigStorage:
    """用户配置存储管理器.
    
    使用 SQLite 存储用户配置，支持异步操作。
    """
    
    def __init__(self, db_path: Path):
        """初始化配置存储.
        
        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_dir()
    
    def _ensure_db_dir(self) -> None:
        """确保数据库目录存在."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def init_table(self) -> None:
        """初始化配置表.
        
        创建 user_configs 表（如果不存在）。
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_configs (
                    user_id TEXT PRIMARY KEY,
                    config_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # 创建更新时间触发器
            await db.execute("""
                CREATE TRIGGER IF NOT EXISTS update_user_config_timestamp
                AFTER UPDATE ON user_configs
                BEGIN
                    UPDATE user_configs SET updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = NEW.user_id;
                END
            """)
            await db.commit()
    
    def init_table_sync(self) -> None:
        """同步初始化配置表和预设表.
        
        用于启动时确保表存在。
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            # 用户配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_configs (
                    user_id TEXT PRIMARY KEY,
                    config_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # 用户自定义场景表（含提示词）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_presets (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    temperature REAL DEFAULT 0.7,
                    max_tokens INTEGER DEFAULT 8000,
                    top_p REAL DEFAULT 0.9,
                    system_prompt TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_presets_user_id 
                ON user_presets(user_id)
            """)
            # 创建更新时间触发器
            try:
                cursor.execute("""
                    CREATE TRIGGER update_user_config_timestamp
                    AFTER UPDATE ON user_configs
                    BEGIN
                        UPDATE user_configs SET updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = NEW.user_id;
                    END
                """)
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("""
                    CREATE TRIGGER update_user_preset_timestamp
                    AFTER UPDATE ON user_presets
                    BEGIN
                        UPDATE user_presets SET updated_at = CURRENT_TIMESTAMP
                        WHERE id = NEW.id;
                    END
                """)
            except sqlite3.OperationalError:
                pass
            conn.commit()
        finally:
            conn.close()
    
    async def save_config(self, user_id: str, config: UserConfig) -> bool:
        """保存用户配置.
        
        Args:
            user_id: 用户标识
            config: 用户配置对象
            
        Returns:
            是否保存成功
        """
        try:
            config_json = config.to_json()
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO user_configs (user_id, config_json)
                    VALUES (?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        config_json = excluded.config_json,
                        updated_at = CURRENT_TIMESTAMP
                """, (user_id, config_json))
                await db.commit()
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    async def load_config(self, user_id: str) -> Optional[UserConfig]:
        """加载用户配置.
        
        Args:
            user_id: 用户标识
            
        Returns:
            用户配置对象，不存在则返回 None
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT config_json FROM user_configs WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return UserConfig.from_json(row["config_json"])
            return None
        except Exception as e:
            print(f"加载配置失败: {e}")
            return None
    
    async def load_or_default(self, user_id: str) -> UserConfig:
        """加载用户配置，不存在则返回默认配置.
        
        Args:
            user_id: 用户标识
            
        Returns:
            用户配置对象
        """
        config = await self.load_config(user_id)
        if config is None:
            config = get_default_config()
        return config
    
    async def delete_config(self, user_id: str) -> bool:
        """删除用户配置.
        
        Args:
            user_id: 用户标识
            
        Returns:
            是否删除成功
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "DELETE FROM user_configs WHERE user_id = ?",
                    (user_id,)
                )
                await db.commit()
            return True
        except Exception as e:
            print(f"删除配置失败: {e}")
            return False
    
    async def reset_to_default(self, user_id: str) -> UserConfig:
        """重置用户配置为默认值.
        
        Args:
            user_id: 用户标识
            
        Returns:
            默认配置对象
        """
        default_config = get_default_config()
        await self.save_config(user_id, default_config)
        return default_config
    
    async def get_all_users(self) -> list[str]:
        """获取所有有配置的用户列表.
        
        Returns:
            用户 ID 列表
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT user_id FROM user_configs"
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [row[0] for row in rows]
        except Exception as e:
            print(f"获取用户列表失败: {e}")
            return []
    
    async def get_config_stats(self) -> Dict[str, Any]:
        """获取配置统计信息.
        
        Returns:
            统计信息字典
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 总用户数
                async with db.execute(
                    "SELECT COUNT(*) FROM user_configs"
                ) as cursor:
                    row = await cursor.fetchone()
                    total_users = row[0] if row else 0
                
                # 最近更新时间
                async with db.execute(
                    "SELECT MAX(updated_at) FROM user_configs"
                ) as cursor:
                    row = await cursor.fetchone()
                    last_updated = row[0] if row else None
                
                return {
                    "total_users": total_users,
                    "last_updated": last_updated,
                }
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {"total_users": 0, "last_updated": None}
    
    # ============== 用户自定义预设管理 ==============
    
    async def create_preset(self, user_id: str, preset: UserScene) -> bool:
        """创建用户场景.
        
        Args:
            user_id: 用户标识
            preset: 场景对象
            
        Returns:
            是否创建成功
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO user_presets (id, user_id, name, description, temperature, max_tokens, top_p, system_prompt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (preset.id, user_id, preset.name, preset.description, 
                      preset.temperature, preset.max_tokens, preset.top_p, preset.system_prompt))
                await db.commit()
            return True
        except Exception as e:
            print(f"创建场景失败: {e}")
            return False
    
    async def update_preset(self, user_id: str, preset: UserScene) -> bool:
        """更新用户场景.
        
        Args:
            user_id: 用户标识
            preset: 场景对象
            
        Returns:
            是否更新成功
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE user_presets 
                    SET name = ?, description = ?, temperature = ?, max_tokens = ?, top_p = ?, system_prompt = ?
                    WHERE id = ? AND user_id = ?
                """, (preset.name, preset.description, preset.temperature, 
                      preset.max_tokens, preset.top_p, preset.system_prompt, preset.id, user_id))
                await db.commit()
            return True
        except Exception as e:
            print(f"更新场景失败: {e}")
            return False
    
    async def delete_preset(self, user_id: str, preset_id: str) -> bool:
        """删除用户预设.
        
        Args:
            user_id: 用户标识
            preset_id: 预设 ID
            
        Returns:
            是否删除成功
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "DELETE FROM user_presets WHERE id = ? AND user_id = ?",
                    (preset_id, user_id)
                )
                await db.commit()
            return True
        except Exception as e:
            print(f"删除预设失败: {e}")
            return False
    
    async def get_preset(self, user_id: str, preset_id: str) -> Optional[UserScene]:
        """获取单个场景.
        
        Args:
            user_id: 用户标识
            preset_id: 场景 ID
            
        Returns:
            场景对象，不存在返回 None
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM user_presets WHERE id = ? AND user_id = ?",
                    (preset_id, user_id)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return UserScene(
                            id=row["id"],
                            user_id=row["user_id"],
                            name=row["name"],
                            description=row["description"] or "",
                            temperature=row["temperature"],
                            max_tokens=row["max_tokens"],
                            top_p=row["top_p"],
                            system_prompt=row["system_prompt"] if "system_prompt" in row.keys() else "",
                            created_at=row["created_at"],
                            updated_at=row["updated_at"],
                        )
            return None
        except Exception as e:
            print(f"获取场景失败: {e}")
            return None
    
    async def get_user_presets(self, user_id: str) -> List[UserScene]:
        """获取用户的所有自定义场景.
        
        Args:
            user_id: 用户标识
            
        Returns:
            场景列表
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM user_presets WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    results = []
                    for row in rows:
                        results.append(UserScene(
                            id=row["id"],
                            user_id=row["user_id"],
                            name=row["name"],
                            description=row["description"] or "",
                            temperature=row["temperature"],
                            max_tokens=row["max_tokens"],
                            top_p=row["top_p"],
                            system_prompt=row["system_prompt"] if "system_prompt" in row.keys() else "",
                            created_at=row["created_at"],
                            updated_at=row["updated_at"],
                        ))
                    return results
        except Exception as e:
            print(f"获取用户场景列表失败: {e}")
            return []


# 全局配置存储实例（延迟初始化）
_config_storage: Optional[ConfigStorage] = None


def get_config_storage(db_path: Path) -> ConfigStorage:
    """获取配置存储实例（单例模式）.
    
    Args:
        db_path: 数据库路径
        
    Returns:
        ConfigStorage 实例
    """
    global _config_storage
    if _config_storage is None:
        _config_storage = ConfigStorage(db_path)
        _config_storage.init_table_sync()
    return _config_storage


async def init_config_storage(db_path: Path) -> ConfigStorage:
    """异步初始化配置存储.
    
    Args:
        db_path: 数据库路径
        
    Returns:
        ConfigStorage 实例
    """
    storage = get_config_storage(db_path)
    await storage.init_table()
    return storage

