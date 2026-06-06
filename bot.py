"""Velvet Reaper — a reaper-themed leveling, economy, and light-moderation bot.

Cogs:
  leveling   — text XP, rank, leaderboard, level-up announce, ^set config
  voice      — XP for active voice time
  rewards    — auto-assign Discord roles at configured levels
  economy    — souls currency: balance, daily, give
  shop       — spend souls (boost / card color / mark)
  moderation — purge + warn
  help       — command index

Level-ups are dispatched as a custom 'velvet_levelup' event so rewards/economy
react without the leveling cog importing them.
"""
import logging
import discord
from discord.ext import commands

import config
from db import Database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("velvetreaper")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True        # needed to assign role rewards
intents.voice_states = True   # needed for voice XP

COGS = ("leveling", "voice", "rewards", "economy", "shop", "moderation", "help")


class VelvetReaper(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=config.PREFIX,
            intents=intents,
            help_command=None,
            owner_ids=config.OWNER_IDS or None,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False),
        )
        self.db = Database("data/velvet.db")

    async def setup_hook(self):
        import os
        os.makedirs("data", exist_ok=True)
        await self.db.connect()
        for c in COGS:
            await self.load_extension(f"cogs.{c}")
            log.info("loaded cogs.%s", c)

    async def close(self):
        await self.db.close()
        await super().close()

    async def on_ready(self):
        log.info("Velvet Reaper online as %s (%s)", self.user, self.user.id)


if __name__ == "__main__":
    if not config.TOKEN:
        raise SystemExit("DISCORD_TOKEN missing from .env")
    VelvetReaper().run(config.TOKEN)
