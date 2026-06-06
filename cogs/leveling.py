"""Text XP, rank cards, leaderboard, and per-guild XP config (^set)."""
import time
import asyncio

import discord
from discord.ext import commands

import config
import cards


def _parse_duration(s: str) -> int | None:
    """'30m' -> 1800, '60' -> 60, '1h' -> 3600, '45s' -> 45."""
    s = s.strip().lower()
    units = {"s": 1, "m": 60, "h": 3600}
    if s.isdigit():
        return int(s)
    if len(s) >= 2 and s[-1] in units and s[:-1].isdigit():
        return int(s[:-1]) * units[s[-1]]
    return None


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns: dict[tuple[int, int], float] = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if len(message.content.strip()) < config.MIN_MESSAGE_LEN:
            return

        gid, uid = message.guild.id, message.author.id
        now = time.time()
        key = (gid, uid)
        if now < self.cooldowns.get(key, 0):
            return
        cfg = await self.bot.db.get_config(gid)
        self.cooldowns[key] = now + cfg["xp_cooldown"]

        # active XP boost?
        row = await self.bot.db.get_user(gid, uid)
        amount = cfg["xp_amount"]
        if row["boost_until"] and now < row["boost_until"]:
            amount *= config.BOOST_MULTIPLIER

        old_lvl, new_lvl = await self.bot.db.add_xp(gid, uid, amount)
        if new_lvl > old_lvl:
            self.bot.dispatch("velvet_levelup", message.author, new_lvl, message.channel)

    @commands.Cog.listener()
    async def on_velvet_levelup(self, member, level, channel):
        # souls reward + announcement (role rewards live in the rewards cog)
        await self.bot.db.add_souls(member.guild.id, member.id, config.LEVELUP_SOULS(level))
        cfg = await self.bot.db.get_config(member.guild.id)
        if not cfg["levelup_enabled"]:
            return
        dest = channel
        if cfg["levelup_channel"]:
            ch = member.guild.get_channel(cfg["levelup_channel"])
            if ch:
                dest = ch
        title = config.rank_title(level)
        e = discord.Embed(
            description=f"{member.mention} reaped their way to **level {level}** — *{title}*.\n"
                        f"+{config.LEVELUP_SOULS(level)} {config.SOUL}",
            color=config.BLOOD,
        )
        try:
            await dest.send(embed=e)
        except discord.HTTPException:
            pass

    @commands.hybrid_command(name="rank", aliases=["level", "card"])
    async def rank(self, ctx, member: discord.Member = None):
        """Show your (or someone's) rank card."""
        member = member or ctx.author
        await ctx.typing()
        row = await self.bot.db.get_user(ctx.guild.id, member.id)
        lvl, into, need = config.progress(row["xp"])
        pos = await self.bot.db.rank_position(ctx.guild.id, member.id)

        avatar_bytes = None
        try:
            avatar_bytes = await member.display_avatar.replace(size=256).read()
        except Exception:
            pass

        buf = await asyncio.get_event_loop().run_in_executor(
            None, lambda: cards.render_card(
                username=member.display_name, avatar_bytes=avatar_bytes,
                level=lvl, rank_title=config.rank_title(lvl),
                xp_into=into, xp_need=need, position=pos, souls=row["souls"],
                accent_hex=row["card_color"], has_mark=bool(row["has_mark"]),
            )
        )
        await ctx.reply(file=discord.File(buf, "rank.png"), mention_author=False)

    @commands.hybrid_command(name="top", aliases=["leaderboard", "lb"])
    async def top(self, ctx):
        """Top 10 by XP."""
        rows = await self.bot.db.leaderboard(ctx.guild.id, by="xp", limit=10)
        if not rows:
            return await ctx.reply("No souls reaped yet.", mention_author=False)
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, r in enumerate(rows):
            tag = medals[i] if i < 3 else f"`#{i+1}`"
            lvl = config.level_from_xp(r["xp"])
            lines.append(f"{tag} <@{r['user_id']}> — L{lvl} · {r['xp']:,} XP")
        e = discord.Embed(title="☠️ The Reaped", description="\n".join(lines), color=config.BLOOD)
        await ctx.reply(embed=e, mention_author=False)

    # ---- config (owner/admin) -------------------------------------------
    async def cog_check(self, ctx):
        return True  # most commands public; admin gating is per-command below

    @commands.hybrid_command(name="set")
    @commands.has_permissions(manage_guild=True)
    async def set_xp(self, ctx, cooldown: str, amount: int):
        """Set XP cooldown and amount. e.g. ^set 30m 40 or ^set 60 20"""
        secs = _parse_duration(cooldown)
        if secs is None or amount < 1:
            return await ctx.reply(
                "Usage: `^set <time> <number>` (e.g. `^set 30m 40`)", mention_author=False)
        await self.bot.db.set_config(ctx.guild.id, xp_cooldown=secs, xp_amount=amount)
        await ctx.reply(
            f"✅ XP cooldown set to **{cooldown}**, **{amount} XP** per message.",
            mention_author=False)

    @commands.hybrid_command(name="levelchannel")
    @commands.has_permissions(manage_guild=True)
    async def levelchannel(self, ctx, channel: discord.TextChannel = None):
        """Route level-up announcements to a channel (omit to use the active one)."""
        cid = channel.id if channel else None
        await self.bot.db.set_config(ctx.guild.id, levelup_channel=cid)
        where = channel.mention if channel else "wherever the level-up happens"
        await ctx.reply(f"✅ Level-ups will post to {where}.", mention_author=False)

    @commands.hybrid_command(name="leveltoggle")
    @commands.has_permissions(manage_guild=True)
    async def leveltoggle(self, ctx, on: bool):
        """Turn level-up announcements on/off."""
        await self.bot.db.set_config(ctx.guild.id, levelup_enabled=1 if on else 0)
        await ctx.reply(f"✅ Level-up announcements **{'on' if on else 'off'}**.",
                        mention_author=False)


async def setup(bot):
    await bot.add_cog(Leveling(bot))
