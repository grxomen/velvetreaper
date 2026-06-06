"""Shop — spend souls on self-fulfilling perks (boost, card color, mark)."""
import re
import time

import discord
from discord.ext import commands

import config

HEX_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="shop")
    async def shop(self, ctx):
        """Browse the shop."""
        lines = []
        for key, item in config.SHOP.items():
            lines.append(
                f"{item['emoji']} **{item['name']}** — {item['price']} {config.SOUL}\n"
                f"`^buy {key}` · {item['desc']}")
        e = discord.Embed(title="🩸 The Reaper's Wares", description="\n\n".join(lines),
                          color=config.VELVET)
        await ctx.reply(embed=e, mention_author=False)

    @commands.hybrid_command(name="buy")
    async def buy(self, ctx, item: str):
        """Buy a shop item by key (boost / color / mark)."""
        item = item.lower().strip()
        spec = config.SHOP.get(item)
        if not spec:
            return await ctx.reply(
                f"No such ware. Try `{config.PREFIX}shop`.", mention_author=False)
        row = await self.bot.db.get_user(ctx.guild.id, ctx.author.id)
        if row["souls"] < spec["price"]:
            return await ctx.reply(
                f"Not enough souls — need {spec['price']}, you hold {row['souls']}.",
                mention_author=False)

        # fulfilment
        if item == "boost":
            until = int(time.time()) + config.BOOST_DURATION
            await self.bot.db.set_field(ctx.guild.id, ctx.author.id, "boost_until", until)
            extra = f"{config.BOOST_MULTIPLIER}× XP active for the next hour."
        elif item == "color":
            await self.bot.db.set_field(ctx.guild.id, ctx.author.id, "card_color", "#8B0000")
            extra = f"Custom card color unlocked — set it with `{config.PREFIX}setcolor #hex`."
        elif item == "mark":
            if row["has_mark"]:
                return await ctx.reply("You already bear the Mark.", mention_author=False)
            await self.bot.db.set_field(ctx.guild.id, ctx.author.id, "has_mark", 1)
            extra = "The Reaper's Mark now stains your rank card."
        else:
            extra = ""

        await self.bot.db.add_souls(ctx.guild.id, ctx.author.id, -spec["price"])
        await ctx.reply(
            f"✅ Bought **{spec['name']}** for {spec['price']} {config.SOUL}. {extra}",
            mention_author=False)

    @commands.hybrid_command(name="setcolor")
    async def setcolor(self, ctx, hex_color: str):
        """Set your rank-card accent (requires the Custom Card Color unlock)."""
        row = await self.bot.db.get_user(ctx.guild.id, ctx.author.id)
        if not row["card_color"]:
            return await ctx.reply(
                f"You haven't unlocked custom colors. `{config.PREFIX}buy color` first.",
                mention_author=False)
        if not HEX_RE.match(hex_color):
            return await ctx.reply("Give a hex color like `#8B0000`.", mention_author=False)
        value = hex_color if hex_color.startswith("#") else "#" + hex_color
        await self.bot.db.set_field(ctx.guild.id, ctx.author.id, "card_color", value)
        await ctx.reply(f"✅ Card accent set to `{value}`.", mention_author=False)


async def setup(bot):
    await bot.add_cog(Shop(bot))
