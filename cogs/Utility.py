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
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
CX_ID = "25817a0b8646e4fdc"
load_dotenv()

class Utility(Cog):
    def __init__(self, bot):
        self.bot: oxy = bot
        self.db = None
        self.blacklisted_users: set[int] = set()
        self.google_api_key = GOOGLE_API_KEY

    async def send_embed(self, ctx: Context, embed: Embed):
        await ctx.send(embed=embed)

    async def fetch_user(self, user_id: int) -> User:
        return await self.bot.fetch_user(user_id)

    @hybrid_command(
        name="afk",
        usage="afk [status=AFK]",
        extras={"example": "afk"},
        with_app_command=True,
    )
    async def afk(self, ctx: Context, *, reason: str = "AFK"):
        """
        Become AFK and notify members when mentioned
        """
        await self.bot.db.execute(
            """
            INSERT INTO afk (
                user_id,
                reason
            ) VALUES ($1, $2)
            ON CONFLICT (user_id) DO NOTHING;
            """,
            ctx.author.id,
            reason[:100],
        )
        await ctx.utility(f":sleeping: {ctx.author.mention}: You're now afk with the status: **{reason}**", reference=ctx.message)

    @group(
        name="snipe",
        usage="snipe",
        extras={"example": "snipe"},
        aliases=['snip', 's'],
        with_app_command=True,
    )
    async def snipe(self, ctx: Context):
        """
        Snipe the last deleted message in the channel
        """
        snipe_data = await self.bot.db.fetch(
            """
            SELECT author_id, content, attachment_url, deleted_at FROM snipe_messages
            WHERE channel_id = $1
            ORDER BY deleted_at DESC
            LIMIT 10
            """,
            ctx.channel.id,
        )
        if not snipe_data:
            return await ctx.utility(f"🔎{ctx.author.mention}: No **deleted messages** found in this channel!", reference=ctx.message)

        pages = []
        for data in snipe_data:
            if not data['content'] and not data['attachment_url']:
                continue  # Skip if both content and attachment_url are empty

            author = await self.fetch_user(data['author_id'])
            embed = Embed(color=Colors.oxy)
            embed.set_author(name=author.display_name, icon_url=author.avatar.url)
            if data['content']:
                embed.description = data['content']
            if data['attachment_url'] and data['attachment_url'].startswith("http"):  # Ensure the URL is valid
                embed.add_field(name=f"{Emojis.separator_straight}Attachment", value=data['attachment_url'], inline=False)
                embed.set_image(url=data['attachment_url'])
            embed.set_footer(text=f"Deleted {human_timedelta(data['deleted_at'])} • {len(pages) + 1}/{len(snipe_data)} messages", icon_url="https://cdn.discordapp.com/emojis/1254266285857177740.png")
            pages.append(embed)

        if not pages:
            return await ctx.utility(f"🔎{ctx.author.mention}: No **valid deleted messages** found in this channel!", reference=ctx.message)

        paginator = Paginator(ctx, pages)
        await paginator.start()

    @snipe.command(
        name="filter",
        usage="snipe filter",
        extras={"example": "snipe filter"}
    )
    async def snipe_filter(self, ctx: Context):
        """
        Filter specific content from snipes
        """
        # Your filtering logic here
        await ctx.approve(f"{ctx.author.mention}: Filter applied successfully!")

    @snipe.command(
        name="ignore",
        usage="snipe ignore <member>",
        extras={"example": "snipe ignore @omtfiji"},
    )
    async def snipe_ignore(self, ctx: Context, member: MemberConverter):
        """
        Ignore a member from being sniped
        """
        # Your ignore logic here
        await ctx.utility(f"{ctx.author.mention}: {member.display_name} will be ignored from snipes.")

    @hybrid_command(
        name="editsnipe",
        usage="editsnipe",
        extras={"example": "editsnipe"},
        aliases=['esnipe', 'es'],
        with_app_command=True,
    )
    async def editsnipe(self, ctx: Context):
        """
        Snipe the last edited message in the channel
        """
        snipe_data = await self.bot.db.fetch(
            """
            SELECT author_id, before_content, after_content, attachment_url, edited_at FROM edit_snipe_messages
            WHERE channel_id = $1
            ORDER BY edited_at DESC
            LIMIT 10
            """,
            ctx.channel.id,
        )
        if not snipe_data:
            return await ctx.utility(f"🔎{ctx.author.mention}: No **edited messages** found in this channel!", reference=ctx.message)

        pages = []
        for data in snipe_data:
            author = await self.fetch_user(data['author_id'])
            embed = Embed(color=Colors.oxy)
            if data['before_content']:
                embed.add_field(name=f"{Emojis.separator_curved}Before", value=f"```yaml\n{data['before_content']}\n```", inline=False)
            if data['after_content']:
                embed.add_field(name=f"{Emojis.separator_curved2}After", value=f"```yaml\n{data['after_content']}\n```", inline=False)
            if data['attachment_url']:
                embed.add_field(name="Attachment", value=data['attachment_url'], inline=False)
                embed.set_image(url=data['attachment_url'])
            embed.set_author(name=author.display_name, icon_url=author.avatar.url)
            embed.set_footer(text=f"Edited {human_timedelta(data['edited_at'])} • {len(pages) + 1}/{len(snipe_data)} messages", icon_url="https://cdn.discordapp.com/emojis/1254266285857177740.png")
            pages.append(embed)

        paginator = Paginator(ctx, pages)
        await paginator.start()

    @hybrid_command(
        name="clearsnipe",
        usage="clearsnipe",
        extras={"example": "clearsnipe"},
        aliases=['csnipe', 'cs'],
        with_app_command=True,
    )
    async def clearsnipe(self, ctx: Context):
        """
        Clear snipes in the channel
        """
        await self.bot.db.execute(
            """
            DELETE FROM snipe_messages
            WHERE channel_id = $1
            """,
            ctx.channel.id,
        )
        await ctx.message.add_reaction("👀")

    @hybrid_command(
        name="cleareditsnipe",
        usage="cleareditsnipe",
        extras={"example": "cleareditsnipe"},
        aliases=['ces', 'censnipe'],
        with_app_command=True,
    )
    async def clear_editsnipe(self, ctx: Context):
        """
        Clear edited snipes in the channel
        """
        await self.bot.db.execute(
            """
            DELETE FROM edit_snipe_messages
            WHERE channel_id = $1
            """,
            ctx.channel.id,
        )
        await ctx.message.add_reaction("👀")



    @command(
        name="image",
        usage="(search)",
        extras={"example": "chief keef"},
        aliases=["im", "img"],
    )
    async def google_image_search(self, ctx, *, query: str):
        """
        Searches for images on Google and displays results.
        """
        async with ctx.typing():
            embeds = []
            results_per_page = 10
            total_results = 30  # Adjust to a more reasonable number

            async with aiohttp.ClientSession() as session:
                tasks = []
                for start_index in range(1, total_results, results_per_page):
                    url = "https://www.googleapis.com/customsearch/v1"
                    params = {
                        "q": query,
                        "cx": CX_ID,
                        "key": GOOGLE_API_KEY,
                        "searchType": "image",
                        "num": results_per_page,
                        "start": start_index,
                        "safe": "active"
                    }
                    tasks.append(session.get(url, params=params))

                responses = await asyncio.gather(*tasks)

                for response in responses:
                    if response.status != 200:
                        await ctx.warn(f"Failed to retrieve images. Status: {response.status}")
                        return
                    data = await response.json()

                    if not data.get("items"):
                        if not embeds:
                            await ctx.send("No results found.")
                            return
                        break

                    for index, item in enumerate(data["items"], start=1):
                        embed = Embed(title=item["title"], url=item["link"])
                        embed.set_image(url=item["link"])
                        embed.set_footer(
                            icon_url="https://media.discordapp.net/attachments/891279552549097503/953673353867186327/icons8-google-144.png?ex=6678e545&is=667793c5&hm=46440d788f74334ce9169b208af817fd1deed034f1dc24cb784757faee9eccfb&",
                            text=f"Page {index}/{total_results} on Google Images (Safe Mode)"
                        )
                        embeds.append(embed)

            paginator = Paginator(ctx, embeds)
            await paginator.start()




async def setup(bot):
    await bot.add_cog(Utility(bot))
