import asyncio
import aiohttp
import os
import psutil
import platform
import discord
import time
import random
import pytz
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typing import Optional, Union
from datetime import datetime, timedelta, timezone
from pytz import timezone, FixedOffset
from discord.ext.commands import (
    Cog, group, command, Author, has_permissions, RoleNotFound, RoleConverter,
    cooldown, BucketType, MemberConverter, hybrid_command
)
from discord import (
    Message, Embed, Member, User, Permissions, Role, ButtonStyle, StickerItem,
    Attachment, File, Status, utils, TextChannel
)
from discord.ui import Button, View

from tools.utilities.humanize import human_timedelta, humanize
from tools.paginator import Paginator
from tools.Managers.Classes import Colors, Emojis
from tools.Managers.Context import CustomContext as Context
from tools.oxy import oxy


class Servers(Cog):
    def __init__(self, bot):
        self.bot: oxy = bot
        self.db = None



    @group(
        name="reskin",
        usage="(subcommand) <args>",
        example="name Destroy Lonely",
        invoke_without_command=True,
    )
    async def reskin(self, ctx: Context):
        """Customize the bot's appearance"""

        await ctx.send_help()

    @reskin.command(
        name="setup",
        aliases=["webhooks"],
    )
    @checks.donator()
    @has_permissions(manage_guild=True)
    @cooldown(1, 600, BucketType.guild)
    async def reskin_setup(self, ctx: Context):
        """Set up the reskin webhooks"""

        await ctx.prompt("Are you sure you want to set up the **reskin webhooks**?\n> This will create a webhook in **every channel** in the server!")

        configuration = await self.bot.db.fetch_config(ctx.guild.id, "reskin") or {}
        configuration["status"] = True
        webhooks = configuration.get("webhooks", {})

        async with ctx.typing():
            tasks = list()
            for channel in ctx.guild.text_channels:
                if any(ext in channel.name.lower() for ext in ("ticket", "log", "discrim", "bleed")) or (
                    channel.category
                    and any(ext in channel.category.name.lower() for ext in ("tickets", "logs", "pfps", "pfp", "icons", "icon", "banners", "banner"))
                ):
                    continue

                tasks.append(functions.configure_reskin(self.bot, channel, webhooks))

            gathered = await asyncio.gather(*tasks)
            created = [webhook for webhook in gathered if webhook]

        configuration["webhooks"] = webhooks
        await self.bot.db.update_config(ctx.guild.id, "reskin", configuration)

        if not created:
            return await ctx.warn("No **webhooks** were created" + (str(gathered) if ctx.author.id in self.bot.owner_ids and any(gathered) else ""))

        await ctx.approve(f"The **reskin webhooks** have been set across {functions.plural(created, bold=True):channel}")

    @reskin.command(
        name="disable",
    )
    @has_permissions(manage_guild=True)
    async def reskin_disable(self, ctx: Context):
        """Disable the reskin webhooks"""

        configuration = await self.bot.db.fetch_config(ctx.guild.id, "reskin") or {}
        if not configuration.get("status"):
            return await ctx.warn("Reskin webhooks are already **disabled**")

        configuration["status"] = False
        await self.bot.db.update_config(ctx.guild.id, "reskin", configuration)
        await ctx.approve("Disabled **reskin** across the server")

    @reskin.group(
        name="server",
        usage="(subcommand) <args>",
        example="name opium bot",
        aliases=["event"],
        invoke_without_command=True,
    )
    @has_permissions(manage_guild=True)
    async def reskin_server(self, ctx: Context):
        """Customize the appearance of events"""

        await ctx.send_help()

    @reskin_server.command(
        name="name",
        usage="(username)",
        example="Destroy Lonely",
        aliases=["username"],
    )
    @checks.donator()
    @has_permissions(manage_guild=True)
    async def reskin_server_name(self, ctx: Context, *, username: str):
        """Change the server reskin username"""

        configuration = await self.bot.db.fetch_config(ctx.guild.id, "reskin") or {}
        if not configuration.get("status"):
            return await ctx.warn(f"Reskin webhooks are **disabled**\n> Use `{ctx.prefix}reskin setup` to set them up")

        if len(username) > 32:
            return await ctx.warn("Your name can't be longer than **32 characters**")

        configuration["username"] = username
        await self.bot.db.update_config(ctx.guild.id, "reskin", configuration)
        await cache.delete_match(f"reskin:channel:{ctx.guild.id}:*")
        await ctx.approve(f"Set the **server reskin username** to **{username}**")

    @reskin.command(
        name="avatar",
        usage="(image)",
        example="https://i.imgur.com/0X0X0X0.png",
        aliases=["icon", "av"],
    )
    @checks.donator()
    async def reskin_avatar(self, ctx: Context, *, image: ImageFinderStrict = None):
        """Change your personal reskin avatar"""

        image = image or await ImageFinderStrict.search(ctx)

        configuration = await self.bot.db.fetch_config(ctx.guild.id, "reskin") or {}
        if not configuration.get("status"):
            return await ctx.warn(f"Reskin webhooks are **disabled**\n> Use `{ctx.prefix}reskin setup` to set them up")

        await self.bot.db.execute(
            "INSERT INTO reskin (user_id, avatar_url) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET avatar_url = $2",
            ctx.author.id,
            image,
        )
        await ctx.approve(f"Changed your **reskin avatar** to [**image**]({image})")

    @reskin_server.command(
        name="remove",
        aliases=["delete", "reset"],
    )
    @has_permissions(manage_guild=True)
    async def reskin_server_remove(self, ctx: Context):
        """Remove the server reskin"""

        configuration = await self.bot.db.fetch_config(ctx.guild.id, "reskin") or {}
        if not (configuration.get("username") or configuration.get("avatar_url")):
            return await ctx.warn("The **server reskin** hasn't been set")

        configuration["username"] = None
        configuration["avatar_url"] = None
        configuration["colors"] = {}
        configuration["emojis"] = {}
        await self.bot.db.update_config(ctx.guild.id, "reskin", configuration)
        await cache.delete_match(f"reskin:channel:{ctx.guild.id}:*")
        await ctx.approve("Removed the **server reskin**")

    @reskin.command(
        name="name",
        usage="(username)",
        example="Destroy Lonely",
        aliases=["username"],
    )
    @checks.donator()
    async def reskin_name(self, ctx: Context, *, username: str):
        """Change your personal reskin username"""

        configuration = await self.bot.db.fetch_config(ctx.guild.id, "reskin") or {}
        if not configuration.get("status"):
            return await ctx.warn(f"Reskin webhooks are **disabled**\n> Use `{ctx.prefix}reskin setup` to set them up")

        if len(username) > 32:
            return await ctx.warn("Your name can't be longer than **32 characters**")

        await self.bot.db.execute(
            "INSERT INTO reskin (user_id, username) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET username = $2",
            ctx.author.id,
            username,
        )
        await ctx.approve(f"Changed your **reskin username** to **{username}**")

    @reskin.command(
        name="avatar",
        usage="(image)",
        example="https://i.imgur.com/0X0X0X0.png",
        aliases=["icon", "av"],
    )
    @checks.donator()
    async def reskin_avatar(self, ctx: Context, *, image: ImageFinderStrict = None):
        """Change your personal reskin avatar"""

        image = image or await ImageFinderStrict.search(ctx)

        configuration = await self.bot.db.fetch_config(ctx.guild.id, "reskin") or {}
        if not configuration.get("status"):
            return await ctx.warn(f"Reskin webhooks are **disabled**\n> Use `{ctx.prefix}reskin setup` to set them up")

        await self.bot.db.execute(
            "INSERT INTO reskin (user_id, avatar_url) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET avatar_url = $2",
            ctx.author.id,
            image,
        )
        await ctx.approve(f"Changed your **reskin avatar** to [**image**]({image})")

    @reskin.group(
        name="color",
        usage="(option) (color)",
        example="main #BBAAEE",
        aliases=["colour"],
        invoke_without_command=True,
    )
    @checks.donator()
    async def reskin_color(
        self,
        ctx: Context,
        option: Literal["main", "approve", "warn", "search", "load", "all"],
        color: Colors = Colors.oxy
    ):
        """Change your personal reskin embed colors"""

        configuration = await self.bot.db.fetch_config(ctx.guild.id, "reskin") or {}
        if not configuration.get("status"):
            return await ctx.warn(f"Reskin webhooks are **disabled**\n> Use `{ctx.prefix}reskin setup` to set them up")

        colors = await self.bot.db.fetchval("SELECT colors FROM reskin WHERE user_id = $1", ctx.author.id) or {}
        if option == "all":
            colors = {
                "main": color.value,
                "approve": color.value,
                "warn": color.value,
                "search": color.value,
                "load": color.value,
            }
        else:
            colors[option] = color.value

        await self.bot.db.execute(
            "INSERT INTO reskin (user_id, colors) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET colors = $2",
            ctx.author.id,
            colors,
        )
        await ctx.approve(
            f"Changed your **reskin color** for " + (f"**{option}** to `{color}`" if option != "all" else f"all **embeds** to `{color}`")
        )

    @reskin_color.command(
        name="reset",
        usage="(option)",
        example="all",
        aliases=["clear"],
    )
    @checks.donator()
    async def reskin_color_reset(
        self,
        ctx: Context,
        option: Literal["main", "approve", "warn", "search", "load", "all"],
    ):
        """Reset your personal reskin embed colors"""

        configuration = await self.bot.db.fetch_config(ctx.guild.id, "reskin") or {}
        if not configuration.get("status"):
            return await ctx.warn(f"Reskin webhooks are **disabled**\n> Use `{ctx.prefix}reskin setup` to set them up")

        colors = await self.bot.db.fetchval("SELECT colors FROM reskin WHERE user_id = $1", ctx.author.id) or {}
        if option == "all":
            colors = {}
        else:
            colors.pop(option, None)

        await self.bot.db.execute(
            "INSERT INTO reskin (user_id, colors) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET colors = $2",
            ctx.author.id,
            colors,
        )
        await ctx.approve(f"Reset your **reskin color** for " + (f"**{option}**" if option != "all" else f"all **embeds**"))

    @reskin.group(
        name="emoji",
        usage="(option) (emoji)",
        example="approve ✨",
        invoke_without_command=True,
    )
    @checks.donator()
    async def reskin_emoji(
        self,
        ctx: Context,
        option: Literal["approve", "warn", "search", "load", "all"],
        emoji: str,
    ):
        """Change your personal reskin embed emojis"""

        configuration = await self.bot.db.fetch_config(ctx.guild.id, "reskin") or {}
        if not configuration.get("status"):
            return await ctx.warn(f"Reskin webhooks are **disabled**\n> Use `{ctx.prefix}reskin setup` to set them up")

        try:
            await ctx.message.add_reaction(emoji)
        except discord.HTTPException:
            return await ctx.warn(f"**{emoji}** is not a valid emoji")

        emojis = await self.bot.db.fetchval("SELECT emojis FROM reskin WHERE user_id = $1", ctx.author.id) or {}
        if option == "all":
            emojis = {
                "approve": emoji,
                "warn": emoji,
                "search": emoji,
                "load": emoji,
            }
        else:
            emojis[option] = emoji

        await self.bot.db.execute(
            "INSERT INTO reskin (user_id, emojis) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET emojis = $2",
            ctx.author.id,
            emojis,
        )
        await ctx.approve(f"Changed your **reskin emoji** for " + (f"**{option}** to {emoji}" if option != "all" else f"all **embeds** to {emoji}"))

    @reskin_emoji.command(
        name="reset",
        usage="(option)",
        example="all",
        aliases=["clear"],
    )
    @checks.donator()
    async def reskin_emoji_reset(
        self,
        ctx: Context,
        option: Literal["approve", "warn", "search", "load", "all"],
    ):
        """Reset your personal reskin embed emojis"""

        configuration = await self.bot.db.fetch_config(ctx.guild.id, "reskin") or {}
        if not configuration.get("status"):
            return await ctx.warn(f"Reskin webhooks are **disabled**\n> Use `{ctx.prefix}reskin setup` to set them up")

        emojis = await self.bot.db.fetchval("SELECT emojis FROM reskin WHERE user_id = $1", ctx.author.id) or {}
        if option == "all":
            emojis = {}
        else:
            emojis.pop(option, None)

        await self.bot.db.execute(
            "INSERT INTO reskin (user_id, emojis) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET emojis = $2",
            ctx.author.id,
            emojis,
        )
        await ctx.approve(f"Reset your **reskin emoji** for " + (f"**{option}**" if option != "all" else f"all **embeds**"))

    @reskin.command(
        name="remove",
        aliases=["delete", "reset"],
    )
    @checks.donator()
    async def reskin_remove(self, ctx: Context):
        """Remove your personal reskin"""

        try:
            await self.bot.db.execute("DELETE FROM reskin WHERE user_id = $1", ctx.author.id)
        except:
            await ctx.warn("You haven't set a **reskin**")
        else:
            await ctx.approve("Removed your **reskin**")











async def setup(bot):
    await bot.add_cog(Servers(bot))
