"""Level role rewards — admins map levels to roles; the bot assigns them on
level-up (and grants any missed lower-tier roles too)."""
import discord
from discord.ext import commands

import config


class Rewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_velvet_levelup(self, member, level, channel):
        rows = await self.bot.db.roles_up_to(member.guild.id, level)
        if not rows:
            return
        to_add = []
        for r in rows:
            role = member.guild.get_role(r["role_id"])
            if role and role not in member.roles and role < member.guild.me.top_role:
                to_add.append(role)
        if to_add:
            try:
                await member.add_roles(*to_add, reason=f"Velvet Reaper level {level} reward")
            except discord.Forbidden:
                pass

    @commands.hybrid_command(name="levelrole")
    @commands.has_permissions(manage_roles=True)
    async def levelrole(self, ctx, level: int, role: discord.Role):
        """Reward a role at a level. e.g. ^levelrole 10 @Specter"""
        if level < 1:
            return await ctx.reply("Level must be 1 or higher.", mention_author=False)
        if role >= ctx.guild.me.top_role:
            return await ctx.reply(
                "That role is above mine — move my role higher or pick a lower role.",
                mention_author=False)
        await self.bot.db.set_level_role(ctx.guild.id, level, role.id)
        await ctx.reply(f"✅ {role.mention} will be granted at **level {level}**.",
                        mention_author=False)

    @commands.hybrid_command(name="dellevelrole")
    @commands.has_permissions(manage_roles=True)
    async def dellevelrole(self, ctx, level: int):
        """Remove the reward at a level."""
        await self.bot.db.remove_level_role(ctx.guild.id, level)
        await ctx.reply(f"✅ Removed the reward at level {level}.", mention_author=False)

    @commands.hybrid_command(name="levelroles")
    async def levelroles(self, ctx):
        """List configured level rewards."""
        rows = await self.bot.db.get_level_roles(ctx.guild.id)
        if not rows:
            return await ctx.reply("No level rewards set. `^levelrole <level> @role`",
                                   mention_author=False)
        lines = [f"**L{r['level']}** → <@&{r['role_id']}>" for r in rows]
        e = discord.Embed(title="Level rewards", description="\n".join(lines),
                          color=config.BLOOD)
        await ctx.reply(embed=e, mention_author=False)


async def setup(bot):
    await bot.add_cog(Rewards(bot))
