"""Souls economy — balance, daily claim, peer transfer."""
import time
import random

import discord
from discord.ext import commands

import config


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="balance", aliases=["bal", "souls"])
    async def balance(self, ctx, member: discord.Member = None):
        """Check soul balance."""
        member = member or ctx.author
        row = await self.bot.db.get_user(ctx.guild.id, member.id)
        e = discord.Embed(
            description=f"{member.mention} holds **{row['souls']:,}** {config.SOUL}",
            color=config.VELVET,
        )
        await ctx.reply(embed=e, mention_author=False)

    @commands.hybrid_command(name="daily")
    async def daily(self, ctx):
        """Claim daily souls."""
        row = await self.bot.db.get_user(ctx.guild.id, ctx.author.id)
        now = int(time.time())
        elapsed = now - (row["last_daily"] or 0)
        if elapsed < config.DAILY_COOLDOWN:
            remain = config.DAILY_COOLDOWN - elapsed
            h, m = remain // 3600, (remain % 3600) // 60
            return await ctx.reply(f"The veil is closed. Return in **{h}h {m}m**.",
                                   mention_author=False)
        amount = random.randint(config.DAILY_MIN, config.DAILY_MAX)
        await self.bot.db.add_souls(ctx.guild.id, ctx.author.id, amount)
        await self.bot.db.set_field(ctx.guild.id, ctx.author.id, "last_daily", now)
        await ctx.reply(f"You reaped **{amount}** {config.SOUL} from the veil.",
                        mention_author=False)

    @commands.hybrid_command(name="give", aliases=["pay"])
    async def give(self, ctx, member: discord.Member, amount: int):
        """Give souls to someone."""
        if member.bot or member.id == ctx.author.id:
            return await ctx.reply("Pick another living soul.", mention_author=False)
        if amount < 1:
            return await ctx.reply("Amount must be positive.", mention_author=False)
        row = await self.bot.db.get_user(ctx.guild.id, ctx.author.id)
        if row["souls"] < amount:
            return await ctx.reply(
                f"You only hold {row['souls']:,} {config.SOUL}.", mention_author=False)
        await self.bot.db.add_souls(ctx.guild.id, ctx.author.id, -amount)
        await self.bot.db.add_souls(ctx.guild.id, member.id, amount)
        await ctx.reply(
            f"{ctx.author.mention} passed **{amount}** {config.SOUL} to {member.mention}.",
            mention_author=False)


async def setup(bot):
    await bot.add_cog(Economy(bot))
