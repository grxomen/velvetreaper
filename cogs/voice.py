"""Voice XP — award XP per minute of *active* voice time (not muted/deafened).

Session start times are in-memory; a bot restart resets any open session
(deliberate, to avoid a heartbeat loop writing to the DB constantly).
"""
import time

import discord
from discord.ext import commands

import config


def _active(state: discord.VoiceState) -> bool:
    return bool(
        state.channel
        and not state.self_mute and not state.self_deaf
        and not state.mute and not state.deaf
        and not getattr(state, "afk", False)
    )


class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessions: dict[tuple[int, int], float] = {}  # (guild,user) -> start ts

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot or not member.guild:
            return
        key = (member.guild.id, member.id)
        was, now_active = _active(before), _active(after)

        if not was and now_active:
            self.sessions[key] = time.time()
            return

        if was and not now_active and key in self.sessions:
            elapsed = int(time.time() - self.sessions.pop(key))
            if elapsed < 30:
                return
            cfg = await self.bot.db.get_config(member.guild.id)
            await self.bot.db.add_voice_seconds(member.guild.id, member.id, elapsed)
            xp = (elapsed // 60) * cfg["vc_xp_per_min"]
            if xp <= 0:
                return
            old_lvl, new_lvl = await self.bot.db.add_xp(member.guild.id, member.id, xp)
            if new_lvl > old_lvl:
                dest = after.channel if after.channel else member.guild.system_channel
                self.bot.dispatch("velvet_levelup", member, new_lvl, dest)

    @commands.hybrid_command(name="setvcxp")
    @commands.has_permissions(manage_guild=True)
    async def setvcxp(self, ctx, per_minute: int):
        """Set XP earned per active voice minute."""
        if per_minute < 0:
            return await ctx.reply("Must be 0 or higher.", mention_author=False)
        await self.bot.db.set_config(ctx.guild.id, vc_xp_per_min=per_minute)
        await ctx.reply(f"✅ Voice XP set to **{per_minute}/min**.", mention_author=False)


async def setup(bot):
    await bot.add_cog(Voice(bot))
