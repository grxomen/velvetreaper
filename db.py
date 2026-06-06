"""aiosqlite layer for Velvet Reaper. One connection, attached to the bot as
bot.db. All XP/souls/config access goes through here so writes from the
on_message hot path stay off the main thread.
"""
import time
import aiosqlite

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    guild_id      INTEGER NOT NULL,
    user_id       INTEGER NOT NULL,
    xp            INTEGER NOT NULL DEFAULT 0,
    souls         INTEGER NOT NULL DEFAULT 0,
    voice_seconds INTEGER NOT NULL DEFAULT 0,
    card_color    TEXT,
    has_mark      INTEGER NOT NULL DEFAULT 0,
    boost_until   INTEGER NOT NULL DEFAULT 0,
    last_daily    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
);
CREATE TABLE IF NOT EXISTS guild_config (
    guild_id        INTEGER PRIMARY KEY,
    xp_amount       INTEGER,
    xp_cooldown     INTEGER,
    vc_xp_per_min   INTEGER,
    levelup_channel INTEGER,
    levelup_enabled INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS level_roles (
    guild_id INTEGER NOT NULL,
    level    INTEGER NOT NULL,
    role_id  INTEGER NOT NULL,
    PRIMARY KEY (guild_id, level)
);
"""


class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self):
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.executescript(SCHEMA)
        await self.conn.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()

    # ---- users -----------------------------------------------------------
    async def get_user(self, guild_id: int, user_id: int) -> aiosqlite.Row:
        await self.conn.execute(
            "INSERT OR IGNORE INTO users (guild_id, user_id) VALUES (?, ?)",
            (guild_id, user_id),
        )
        await self.conn.commit()
        cur = await self.conn.execute(
            "SELECT * FROM users WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
        return await cur.fetchone()

    async def add_xp(self, guild_id: int, user_id: int, amount: int):
        """Add xp; return (old_level, new_level)."""
        row = await self.get_user(guild_id, user_id)
        old_xp = row["xp"]
        new_xp = old_xp + amount
        await self.conn.execute(
            "UPDATE users SET xp=? WHERE guild_id=? AND user_id=?",
            (new_xp, guild_id, user_id),
        )
        await self.conn.commit()
        return config.level_from_xp(old_xp), config.level_from_xp(new_xp)

    async def add_souls(self, guild_id: int, user_id: int, amount: int):
        await self.get_user(guild_id, user_id)
        await self.conn.execute(
            "UPDATE users SET souls = souls + ? WHERE guild_id=? AND user_id=?",
            (amount, guild_id, user_id),
        )
        await self.conn.commit()

    async def add_voice_seconds(self, guild_id: int, user_id: int, secs: int):
        await self.get_user(guild_id, user_id)
        await self.conn.execute(
            "UPDATE users SET voice_seconds = voice_seconds + ? WHERE guild_id=? AND user_id=?",
            (secs, guild_id, user_id),
        )
        await self.conn.commit()

    async def set_field(self, guild_id: int, user_id: int, field: str, value):
        if field not in {"card_color", "has_mark", "boost_until", "last_daily", "souls", "xp"}:
            raise ValueError(f"refusing to set unknown field {field!r}")
        await self.get_user(guild_id, user_id)
        await self.conn.execute(
            f"UPDATE users SET {field}=? WHERE guild_id=? AND user_id=?",
            (value, guild_id, user_id),
        )
        await self.conn.commit()

    async def leaderboard(self, guild_id: int, by: str = "xp", limit: int = 10):
        col = "xp" if by == "xp" else "souls"
        cur = await self.conn.execute(
            f"SELECT user_id, xp, souls FROM users WHERE guild_id=? ORDER BY {col} DESC LIMIT ?",
            (guild_id, limit),
        )
        return await cur.fetchall()

    async def rank_position(self, guild_id: int, user_id: int) -> int:
        cur = await self.conn.execute(
            "SELECT COUNT(*)+1 AS pos FROM users WHERE guild_id=? AND xp > "
            "(SELECT xp FROM users WHERE guild_id=? AND user_id=?)",
            (guild_id, guild_id, user_id),
        )
        row = await cur.fetchone()
        return row["pos"]

    # ---- guild config ----------------------------------------------------
    async def get_config(self, guild_id: int) -> dict:
        cur = await self.conn.execute(
            "SELECT * FROM guild_config WHERE guild_id=?", (guild_id,)
        )
        row = await cur.fetchone()
        if row is None:
            return {
                "xp_amount": config.DEFAULT_XP_AMOUNT,
                "xp_cooldown": config.DEFAULT_XP_COOLDOWN,
                "vc_xp_per_min": config.DEFAULT_VC_XP_PER_MIN,
                "levelup_channel": None,
                "levelup_enabled": 1,
            }
        return {
            "xp_amount": row["xp_amount"] if row["xp_amount"] is not None else config.DEFAULT_XP_AMOUNT,
            "xp_cooldown": row["xp_cooldown"] if row["xp_cooldown"] is not None else config.DEFAULT_XP_COOLDOWN,
            "vc_xp_per_min": row["vc_xp_per_min"] if row["vc_xp_per_min"] is not None else config.DEFAULT_VC_XP_PER_MIN,
            "levelup_channel": row["levelup_channel"],
            "levelup_enabled": row["levelup_enabled"],
        }

    async def set_config(self, guild_id: int, **fields):
        allowed = {"xp_amount", "xp_cooldown", "vc_xp_per_min", "levelup_channel", "levelup_enabled"}
        cols = {k: v for k, v in fields.items() if k in allowed}
        if not cols:
            return
        await self.conn.execute(
            "INSERT OR IGNORE INTO guild_config (guild_id) VALUES (?)", (guild_id,)
        )
        sets = ", ".join(f"{k}=?" for k in cols)
        await self.conn.execute(
            f"UPDATE guild_config SET {sets} WHERE guild_id=?",
            (*cols.values(), guild_id),
        )
        await self.conn.commit()

    # ---- level roles -----------------------------------------------------
    async def set_level_role(self, guild_id: int, level: int, role_id: int):
        await self.conn.execute(
            "INSERT OR REPLACE INTO level_roles (guild_id, level, role_id) VALUES (?, ?, ?)",
            (guild_id, level, role_id),
        )
        await self.conn.commit()

    async def remove_level_role(self, guild_id: int, level: int):
        await self.conn.execute(
            "DELETE FROM level_roles WHERE guild_id=? AND level=?", (guild_id, level)
        )
        await self.conn.commit()

    async def get_level_roles(self, guild_id: int):
        cur = await self.conn.execute(
            "SELECT level, role_id FROM level_roles WHERE guild_id=? ORDER BY level",
            (guild_id,),
        )
        return await cur.fetchall()

    async def roles_up_to(self, guild_id: int, level: int):
        cur = await self.conn.execute(
            "SELECT level, role_id FROM level_roles WHERE guild_id=? AND level<=? ORDER BY level",
            (guild_id, level),
        )
        return await cur.fetchall()
