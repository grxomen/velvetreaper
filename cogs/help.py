"""Help — a themed command index."""
import discord
from discord.ext import commands

import config


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help")
    async def help(self, ctx):
        """Show the command list."""
        p = config.PREFIX
        e = discord.Embed(
            title="☠️ Velvet Reaper",
            description="*Chat, lurk in voice, and reap souls. The more you speak, "
                        "the higher you rise.*",
            color=config.BLOOD,
        )
        e.add_field(
            name="Leveling",
            value=f"`{p}rank [@user]` · `{p}top`",
            inline=False)
        e.add_field(
            name="Souls",
            value=f"`{p}balance [@user]` · `{p}daily` · `{p}give @user <n>`\n"
                  f"`{p}shop` · `{p}buy <item>` · `{p}setcolor #hex`",
            inline=False)
        e.add_field(
            name="Admin — leveling",
            value=f"`{p}set <time> <n>` · `{p}setvcxp <n>` · "
                  f"`{p}levelchannel [#ch]` · `{p}leveltoggle <on/off>`",
            inline=False)
        e.add_field(
            name="Admin — rewards & mod",
            value=f"`{p}levelrole <lvl> @role` · `{p}dellevelrole <lvl>` · `{p}levelroles`\n"
                  f"`{p}purge <n>` · `{p}warn @user [reason]`",
            inline=False)
        e.set_footer(text=f"Rank ladder: {' → '.join(name for _, name in config.RANKS)}")
        await ctx.reply(embed=e, mention_author=False)


async def setup(bot):
    await bot.add_cog(Help(bot))
