"""Database helper cho SQLite"""

import aiosqlite
import json
import os
from typing import Optional, Dict
import logging
from utils.error_handler import DatabaseError
from datetime import datetime, timedelta, timezone
from collections import OrderedDict

logger = logging.getLogger('BlastBot.Database')
# Ngăn logger của Database ghi ra console thông qua root logger
# và đảm bảo vẫn ghi vào file log chung.
if not logger.handlers:
    file_handler = logging.FileHandler('bot.log', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
logger.setLevel(logging.INFO)
logger.propagate = False


class LRUCache:
    """Simple LRU Cache implementation with TTL support"""
    
    def __init__(self, maxsize: int = 128, ttl_seconds: int = 300):
        self.maxsize = maxsize
        self.ttl = timedelta(seconds=ttl_seconds)
        self.cache: OrderedDict[int, dict] = OrderedDict()
        self.timestamps: Dict[int, datetime] = {}
    
    def get(self, key: int) -> Optional[dict]:
        """Get item from cache"""
        if key not in self.cache:
            return None
        
        # Check if expired
        timestamp = self.timestamps.get(key)
        if timestamp and datetime.now(timezone.utc) - timestamp >= self.ttl:
            self.delete(key)
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return self.cache[key].copy()
    
    def set(self, key: int, value: dict):
        """Set item in cache"""
        # Remove if exists
        if key in self.cache:
            del self.cache[key]
        
        # Add new item
        self.cache[key] = value.copy()
        self.timestamps[key] = datetime.now(timezone.utc)
        
        # Remove oldest if over maxsize
        if len(self.cache) > self.maxsize:
            oldest_key = next(iter(self.cache))
            self.delete(oldest_key)
    
    def delete(self, key: int):
        """Delete item from cache"""
        if key in self.cache:
            del self.cache[key]
        if key in self.timestamps:
            del self.timestamps[key]
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.timestamps.clear()
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        current_time = datetime.now(timezone.utc)
        valid_entries = sum(
            1 for key, timestamp in self.timestamps.items()
            if current_time - timestamp < self.ttl
        )
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self.cache) - valid_entries,
            'maxsize': self.maxsize,
            'ttl_seconds': self.ttl.total_seconds()
        }


class Database:
    """Wrapper cho aiosqlite database operations với caching"""
    
    # Class-level LRU cache cho guild configs
    from utils.constants import CACHE_CONFIG
    _guild_config_cache = LRUCache(
        maxsize=CACHE_CONFIG['guild_config_maxsize'],
        ttl_seconds=CACHE_CONFIG['guild_config_ttl_seconds']
    )
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv('DB_PATH', './data/bot.db')
        self.conn: Optional[aiosqlite.Connection] = None
    
    async def connect(self):
        """Kết nối đến database"""
        try:
            self.conn = await aiosqlite.connect(self.db_path)
            if self.conn:
                self.conn.row_factory = aiosqlite.Row
                await self.conn.execute("PRAGMA foreign_keys = ON")
                await self.initialize_tables()
            logger.info(f"Database connected: {self.db_path}")
        except aiosqlite.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise DatabaseError(f"Database connection failed: {e}")
    
    async def close(self):
        """Đóng kết nối database"""
        if self.conn:
            try:
                await self.conn.close()
                logger.info("Database connection closed")
            except aiosqlite.Error as e:
                logger.error(f"Error closing database: {e}")
    
    async def initialize_tables(self):
        """Tạo tables nếu chưa tồn tại"""
        if not self.conn:
            return
        
        try:
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS guilds (
                    guild_id INTEGER PRIMARY KEY,
                    welcome_channel_id INTEGER,
                    log_channel_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await self._ensure_users_table()

            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS role_menus (
                    message_id INTEGER PRIMARY KEY,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    role_ids TEXT NOT NULL,
                    mode TEXT NOT NULL DEFAULT 'toggle',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
                )
            """)
            
            await self.conn.commit()
            logger.info("Database tables initialized")
        except aiosqlite.Error as e:
            logger.error(f"Failed to initialize tables: {e}")
            raise DatabaseError(f"Table initialization failed: {e}")

    async def _get_table_columns(self, table_name: str) -> list[dict]:
        if not self.conn:
            return []

        async with self.conn.execute(f"PRAGMA table_info({table_name})") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def _ensure_users_table(self):
        if not self.conn:
            return

        columns = await self._get_table_columns('users')
        if not columns:
            await self.conn.execute("""
                CREATE TABLE users (
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    points INTEGER DEFAULT 0,
                    warnings INTEGER DEFAULT 0,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, guild_id),
                    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
                )
            """)
            return

        pk_columns = [column['name'] for column in columns if column['pk']]
        guild_id_column = next((column for column in columns if column['name'] == 'guild_id'), None)

        if pk_columns == ['user_id', 'guild_id'] and guild_id_column and guild_id_column['notnull'] == 1:
            return

        await self._migrate_users_table()

    async def _migrate_users_table(self):
        if not self.conn:
            return

        logger.warning("Migrating users table to composite primary key (user_id, guild_id)")
        await self.conn.execute("ALTER TABLE users RENAME TO users_legacy")
        await self.conn.execute("""
            CREATE TABLE users (
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                points INTEGER DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, guild_id),
                FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
            )
        """)

        async with self.conn.execute("SELECT COUNT(*) AS count FROM users_legacy WHERE guild_id IS NULL") as cursor:
            row = await cursor.fetchone()
            skipped_rows = int(row['count']) if row else 0
            if skipped_rows:
                logger.warning(f"Skipped {skipped_rows} legacy user rows without guild_id during migration")

        await self.conn.execute("""
            INSERT OR REPLACE INTO users (user_id, guild_id, points, warnings, last_active)
            SELECT user_id, guild_id, points, warnings, last_active
            FROM users_legacy
            WHERE guild_id IS NOT NULL
        """)
        await self.conn.execute("DROP TABLE users_legacy")

    async def save_role_menu(self, message_id: int, guild_id: int, channel_id: int, role_ids: list[int], mode: str):
        if not self.conn:
            return

        await self.conn.execute(
            """
            INSERT INTO role_menus (message_id, guild_id, channel_id, role_ids, mode)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(message_id) DO UPDATE SET
                guild_id = excluded.guild_id,
                channel_id = excluded.channel_id,
                role_ids = excluded.role_ids,
                mode = excluded.mode
            """,
            (message_id, guild_id, channel_id, json.dumps(role_ids), mode)
        )
        await self.conn.commit()

    async def get_role_menus(self) -> list[dict]:
        if not self.conn:
            return []

        async with self.conn.execute("SELECT * FROM role_menus") as cursor:
            rows = await cursor.fetchall()
            menus = []
            for row in rows:
                menu = dict(row)
                try:
                    menu['role_ids'] = [int(role_id) for role_id in json.loads(menu['role_ids'])]
                except (TypeError, ValueError, json.JSONDecodeError):
                    menu['role_ids'] = []
                menus.append(menu)
            return menus

    async def delete_role_menu(self, message_id: int):
        if not self.conn:
            return

        await self.conn.execute("DELETE FROM role_menus WHERE message_id = ?", (message_id,))
        await self.conn.commit()
    
    async def get_guild_config(self, guild_id: int) -> dict:
        """Lấy config của guild (with caching)"""
        # Check cache first
        cached_config = self._guild_config_cache.get(guild_id)
        if cached_config is not None:
            logger.debug(f"Cache hit for guild {guild_id}")
            return cached_config
        
        default_config = {
            'guild_id': guild_id,
            'welcome_channel_id': None,
            'log_channel_id': None
        }
        
        if not self.conn:
            return default_config
        
        try:
            async with self.conn.execute(
                "SELECT * FROM guilds WHERE guild_id = ?",
                (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    config = dict(row)
                    # Update cache
                    self._guild_config_cache.set(guild_id, config)
                    return config
                else:
                    # Tạo config mới nếu chưa có
                    await self.conn.execute(
                        "INSERT INTO guilds (guild_id) VALUES (?)",
                        (guild_id,)
                    )
                    await self.conn.commit()
                    # Cache default config
                    self._guild_config_cache.set(guild_id, default_config)
                    return default_config
        except aiosqlite.Error as e:
            logger.error(f"Failed to get guild config for {guild_id}: {e}")
            return default_config
    
    async def update_guild_config(self, guild_id: int, **kwargs):
        """Cập nhật config của guild (invalidates cache)"""
        if not self.conn:
            return
        
        valid_fields = ['welcome_channel_id', 'log_channel_id']
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        if not updates:
            return
        
        try:
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [guild_id]
            
            await self.conn.execute(
                f"UPDATE guilds SET {set_clause} WHERE guild_id = ?",
                values
            )
            await self.conn.commit()
            
            # Invalidate cache
            self.invalidate_cache(guild_id)
            
            logger.debug(f"Updated guild config for {guild_id}: {updates}")
        except aiosqlite.Error as e:
            logger.error(f"Failed to update guild config for {guild_id}: {e}")
            await self.conn.rollback()
            raise DatabaseError(f"Failed to update guild config: {e}")
    
    @classmethod
    def invalidate_cache(cls, guild_id: Optional[int] = None):
        """
        Invalidate cache for specific guild or all guilds
        
        Args:
            guild_id: Guild ID to invalidate (None = invalidate all)
        """
        if guild_id is None:
            cls._guild_config_cache.clear()
            logger.debug("Cleared all guild config cache")
        else:
            cls._guild_config_cache.delete(guild_id)
            logger.debug(f"Invalidated cache for guild {guild_id}")
    
    @classmethod
    def get_cache_stats(cls) -> dict:
        """Get cache statistics"""
        return cls._guild_config_cache.get_stats()
    
    async def get_user_data(self, user_id: int, guild_id: int) -> dict:
        """Lấy dữ liệu user"""
        default_data = {
            'user_id': user_id,
            'guild_id': guild_id,
            'points': 0,
            'warnings': 0
        }
        
        if not self.conn:
            return default_data
        
        try:
            async with self.conn.execute(
                "SELECT * FROM users WHERE user_id = ? AND guild_id = ?",
                (user_id, guild_id)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                else:
                    # Tạo user mới nếu chưa có
                    await self.conn.execute(
                        "INSERT INTO users (user_id, guild_id) VALUES (?, ?)",
                        (user_id, guild_id)
                    )
                    await self.conn.commit()
                    return default_data
        except aiosqlite.Error as e:
            logger.error(f"Failed to get user data for {user_id} in guild {guild_id}: {e}")
            return default_data
    
    async def update_user_data(self, user_id: int, guild_id: int, **kwargs):
        """Cập nhật dữ liệu user"""
        if not self.conn:
            return
        
        valid_fields = ['points', 'warnings', 'last_active']
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        if not updates:
            return
        
        try:
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [user_id, guild_id]
            
            await self.conn.execute(
                f"UPDATE users SET {set_clause} WHERE user_id = ? AND guild_id = ?",
                values
            )
            await self.conn.commit()
            logger.debug(f"Updated user data for {user_id} in guild {guild_id}: {updates}")
        except aiosqlite.Error as e:
            logger.error(f"Failed to update user data for {user_id} in guild {guild_id}: {e}")
            await self.conn.rollback()
            raise DatabaseError(f"Failed to update user data: {e}")
