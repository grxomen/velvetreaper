"""Light moderation — purge (the observed core command) plus a simple warn."""
import discord
from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="purge", aliases=["clear"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        """Delete the last N messages (max 100)."""
        if amount < 1:
            return await ctx.reply("Give a positive number.", mention_author=False)
        amount = min(amount, 100)
        # +1 to also remove the invoking command for prefix usage
        deleted = await ctx.channel.purge(limit=amount + 1)
        n = max(len(deleted) - 1, 0)
        msg = await ctx.send(f"✅ Deleted {n} messages.")
        await msg.delete(delay=4)

    @commands.hybrid_command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason given"):
        """Warn a member (DMs them; logs nothing persistent in v1)."""
        e = discord.Embed(
            title="⚠️ Warning",
            description=f"You were warned in **{ctx.guild.name}**.\n**Reason:** {reason}",
            color=0xD29922,
        )
        try:
            await member.send(embed=e)
            dmed = "and DMed"
        except discord.HTTPException:
            dmed = "(couldn't DM)"
        await ctx.reply(f"⚠️ Warned {member.mention} {dmed}. Reason: {reason}",
                        mention_author=False)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
