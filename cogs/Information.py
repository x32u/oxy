import asyncio
import aiohttp
import os
import psutil
import platform
import discord
import pytz
import asyncpg
import random
import time
import requests
import pytz
from pytz import timezone as pytz_timezone

from typing import Union
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pytz import timezone, FixedOffset
from typing import Optional
from tools.Managers.Classes import Colors, Emojis
from datetime import datetime, timedelta, timezone
from tools.Managers.Context import CustomContext as Context
from tools.oxy import oxy
from tools.paginator import Paginator
from discord.utils import format_dt
from discord.ext.commands import(
    Cog,
    group,
    command, 
    has_permissions, 
    RoleNotFound,
    RoleConverter,
    cooldown,
    BucketType,
    hybrid_command
)
from discord import ( 
    Embed, 
    Member, 
    User, 
    ButtonStyle,
    Status,
    utils,
    Message,
    TextChannel
)
from discord.ui import(
    Button, 
    View
)
from dotenv import load_dotenv

load_dotenv()




class Information(Cog):
    def __init__(self, bot):
        self.bot: oxy = bot
        self.db = None
        self.blacklisted_users: set[int] = set()
        self.tmdb_api_key = os.getenv('tmdb_api_key') # TMDb API key
        self.weather_api_key = os.getenv('OPENWEATHERMAP_API_KEY')
        self.previous_boosters = set()

    @staticmethod
    async def send_embed(ctx, title, description, color=Colors.oxy, thumbnail=None, author=None, footer=None):
        embed = discord.Embed(title=title, description=description, color=color)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if author:
            embed.set_author(name=author['name'], icon_url=author['icon'])
        if footer:
            embed.set_footer(text=footer['text'], icon_url=footer['icon'])
        await ctx.send(embed=embed)

    @staticmethod
    async def fetch_html(url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                return await response.text()

    @staticmethod
    def format_time_since(start_time):
        now = datetime.now(start_time.tzinfo)
        delta = now - start_time
        days, seconds = delta.days, delta.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{days}d {hours}h {minutes}m {seconds}s"
    




    
    @command(aliases=["bi", "aboutbot"])
    async def botinfo(self, ctx):
        """
        Displays information about the bot
        """

        process = psutil.Process()
        memory_usage_mb = process.memory_info().rss / 1024 / 1024
        memory_usage_gb = memory_usage_mb / 1024
        memory_usage = f"{memory_usage_mb:.2f} MB" if memory_usage_mb < 1024 else f"{memory_usage_gb:.2f} GB"
        cpu_usage = psutil.cpu_percent()


        # Calculate uptime
        current_time = datetime.now()
        start_time = datetime.fromtimestamp(process.create_time())
        uptime = current_time - start_time
        days, remainder = divmod(uptime.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Format uptime string
        uptime_parts = []
        if days > 0:
            uptime_parts.append(f"{int(days)} D")
        if hours > 0:
            uptime_parts.append(f"{int(hours)} H")
        if minutes > 0:
            uptime_parts.append(f"{int(minutes)} M")
        if seconds > 0:
            uptime_parts.append(f"{int(seconds)} S")
        uptime_str = ", ".join(uptime_parts)

        # Calculate bot-wide statistics
        total_files = 0
        total_lines = 0
        total_functions = 0
        total_classes = 0

        for root, _, files in os.walk("."):
            for file in files:
                if file.endswith(".py"):
                    total_files += 1
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        total_lines += len(lines)
                        total_functions += sum(1 for line in lines if line.strip().startswith("def "))
                        total_classes += sum(1 for line in lines if line.strip().startswith("class "))

        # ASCII art logo of the bot's name


        embed = Embed(
            title=f"{self.bot.user.name}",
            description=f"Serving `{len(self.bot.guilds):,}` guilds with `{len(self.bot.users):,}` users\nUtilizing **`{len(self.bot.commands):,}`** commands across `{len(self.bot.cogs):,}` cogs",
            color=Colors.oxy
        )

        embed.add_field(
            name="",
            value=(
                f"```python\n"
                f"PID----- : {process.pid}\n"
                f"CPU----- : {cpu_usage}%\n"
                f"RAM----- : {memory_usage}\n"
                f"Ping---- : {self.bot.latency*1000:.2f} ms\n"
                f"Uptime-- : {uptime_str}\n"
                f"Developer: sry4thedly \n"
                f""
                f"```"
            ),
            inline=True
        )

        embed.add_field(
            name="",
            value=(
                f"```json\n"
                f"FILES--- : {total_files}\n"
                f"LINES--- : {total_lines}\n"
                f"FUNCTS-- : {total_functions}\n"
                f"CLASSES- : {total_classes}\n"
                f"PYTHON-- : {platform.python_version()}\n"
                f"DISCORD- : {discord.__version__}\n"

                f"```"
            ),
            inline=True
        )

        embed.set_footer(text=f"{self.bot.user.name}/{self.bot.version}")
        await ctx.reply(embed=embed)

    @hybrid_command(
            name="ping",
            aliases=["ms"], 
            usage="ping",
            extras={"example": "ping"},
    )
    @cooldown(1, 2, BucketType.user)
    async def ping(self, ctx: Context):
        """
        Shows the Ping of the bot
        """
        ping_responses = [
            "diddy's house",
            "liveleak.com",
            "a connection to the server",
            "FREE YSL",
            "911",
            "a skid",
            "a shard",
            "bleed",
            "a server",
            "greed"
        ]
        start_time = time.time()  # Start timing before sending the message
        message = await ctx.send(content="ping..")
        latency = (time.time() - start_time) * 1000  # Calculate round-trip latency
        shard_latency = self.bot.get_shard(ctx.guild.shard_id).latency * 1000  # Get shard latency
        embed = Embed(description=f"{Emojis.ping} it took me `{round(shard_latency)} ms` to ping `{random.choice(ping_responses)}` rest: `{round(latency)} ms`", color=0x85ed91)
        await message.edit(content=None, embed=embed)  # Update the message with the latency information

    @command(
        name="support",
        aliases=["sup"],
        usage="support",
        extras={"example": "support"},
    )
    async def support(self, ctx):
        """
        Displays the support server
        """
        await ctx.utility(f"{Emojis.bot} **Support Server:** https://discord.gg/RY3yhVsG", reference=ctx.message)

    async def create_server_info_embed(self, guild):
        embed = Embed(title=f"{Emojis.separator_straight} {guild.name}", color=Colors.oxy)  # Adjust the color to match the screenshot
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.set_author(name=f"{guild.name}", icon_url=guild.icon.url if guild.icon else None)
    
        # Server creation date and owner
        created_at_timestamp = int(guild.created_at.timestamp())
        time_since_creation = f"<t:{created_at_timestamp}:R>"  # Use Discord's relative timestamp format
        try:
            owner = await guild.fetch_member(guild.owner_id)
            owner_name = f"**{owner}** ( `{owner.id}` )"
        except:
            owner_name = "Owner not available"
        embed.add_field(name="", value=f"{Emojis.separator_curved} **Owner:** {owner_name}\n{Emojis.separator_curved} **Created:** <t:{created_at_timestamp}:f> ({time_since_creation})", inline=False)
    
        # Members and Information
        human_count = sum(1 for member in guild.members if not member.bot)
        bot_count = sum(1 for member in guild.members if member.bot)
        members_info = f"{Emojis.separator_curved} **total:** {guild.member_count}\n{Emojis.separator_curved} **humans:** {human_count}\n{Emojis.separator_curved} **bots:** {bot_count}"
        embed.add_field(name=f"**Members**", value=members_info, inline=True)
    
        # General Information
        verification_boosts = f"**verification:** {str(guild.verification_level).lower()}\n{Emojis.separator_curved} **vanity:** /{guild.vanity_url_code or 'N/A'}"
        embed.add_field(name="**General**", value=f"{Emojis.separator_curved} {verification_boosts}", inline=True)
    
        # Emojis
        emojis_info = f"**static:** {len([e for e in guild.emojis if not e.animated])}\n{Emojis.separator_curved} **animated:** {len([e for e in guild.emojis if e.animated])}\n{Emojis.separator_curved} **total:** {len(guild.emojis)}"
        embed.add_field(name="**Emojis**", value=f"{Emojis.separator_curved} {emojis_info}", inline=True)
    
        # Channels
        channels_info = f"**text:** {len(guild.text_channels)}\n{Emojis.separator_curved} **voice:** {len(guild.voice_channels)}\n{Emojis.separator_curved} **categories:** {len(guild.categories)}"
        embed.add_field(name="**Channels**", value=f"{Emojis.separator_curved} {channels_info}", inline=True)
    
        # Miscellaneous
        misc_info = f"**roles:** {len(guild.roles)}\n{Emojis.separator_curved} **emojis:** {len(guild.emojis)}\n{Emojis.separator_curved} **stickers:** {len(guild.stickers)}"
        embed.add_field(name="**Miscellaneous**", value=f"{Emojis.separator_curved} {misc_info}", inline=True)
    
        # Boosts
        boosts_info = f"**level:** {guild.premium_tier}\n{Emojis.separator_curved} **boosts:** {guild.premium_subscription_count}\n{Emojis.separator_curved} **boosters:** {len(guild.premium_subscribers)}"
        embed.add_field(name="**Boosts**", value=f"{Emojis.separator_curved} {boosts_info}", inline=True)
        embed.color = Colors.oxy
    
        # Features
        important_features = [
            "ANIMATED_BANNER", "PRIVATE_THREADS", "ROLE_ICONS", "AUTO_MODERATION", "MEMBER_PROFILES", 
            "VANITY_URL", "SOUNDBOARD", "BANNER", "COMMUNITY", "ANIMATED_ICON"
        ]
        features = [feature.replace("_", " ").title() for feature in guild.features if feature.upper() in important_features]
        features_str = ", ".join(features) if features else "N/A"
        embed.add_field(name="**Features**", value=f"```{features_str}```")
    
        eastern = pytz.timezone('US/Eastern')
        current_time_eastern = datetime.now(eastern).strftime('%I:%M %p')
        embed.set_footer(text=f"Guild id: {guild.id} • Today at {current_time_eastern}")
    
        return embed

    @command(
        name="serverinfo",
        aliases=["si"],
        usage="serverinfo",
        extras={"example": "serverinfo"},
    )
    @cooldown(1, 2, BucketType.user)
    async def server_info(self, ctx):
        """
        Displays information about the server.
        """
        guild = ctx.guild
        embed = await self.create_server_info_embed(guild)
        
        # Create buttons for different server images
        view = View()
        if guild.banner:
            view.add_item(Button(label="Banner", url=guild.banner.url, style=ButtonStyle.link, emoji=Emojis.link))
        if guild.icon:
            view.add_item(Button(label="Icon", url=guild.icon.url, style=ButtonStyle.link, emoji=Emojis.link))
        if guild.splash:
            view.add_item(Button(label="Splash", url=guild.splash.url, style=ButtonStyle.link, emoji=Emojis.link))
    
        await ctx.send(embed=embed, view=view)    

    
    @command(
        name="servericon",
        aliases=["icon"],
        usage="servericon",
        extras={"example": "servericon"},
    )
    @cooldown(1, 2, BucketType.user)
    async def server_icon(self, ctx):
        """
        Displays the server's icon with buttons for different image formats.
        """
        guild = ctx.guild
        if not guild.icon:
            await ctx.warn("This server has no **icon**.", reference=ctx.message)
            return

        icon_url = guild.icon.url  # Get the URL of the server's icon

        embed = Embed(
            description=f"**[{guild.name}'s icon]({icon_url})**",
            color=Colors.oxy  # Ensure Colors.oxy is defined and accessible
        )
        embed.set_image(url=icon_url)
        embed.set_footer(text=f"Request by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        embed.set_author(name=guild.name, icon_url=icon_url)

        # Create buttons for different image formats with emojis
        view = View()
        view.add_item(Button(label="WEBP", url=f"{icon_url}?format=webp", style=ButtonStyle.link, emoji=Emojis.link))
        view.add_item(Button(label="PNG", url=f"{icon_url}?format=png", style=ButtonStyle.link, emoji=Emojis.link))
        view.add_item(Button(label="JPG", url=f"{icon_url}?format=jpg", style=ButtonStyle.link, emoji=Emojis.link))

        await ctx.send(embed=embed, view=view)

    @hybrid_command(
            name="avatar", 
            aliases=["pfp", "av"],
            usage="(member)",
            extras={"example": "avatar @vert"},
            user_install=True,
            )
    @cooldown(1, 2, BucketType.user)
    async def avatar(self, ctx, *, member: Member = None):
        """
        Sends the avatar of the specified user or the command invoker if no user is specified.
        """
        member = member or ctx.author  # If no member is specified, use the command invoker
        avatar_url = member.display_avatar.url  # Get the URL of the member's avatar

        embed = Embed(
            title=f"{member.name}'s avatar",
            color=Colors.oxy  # Ensure Colors.sorrow is defined and accessible
        )
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"Request by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        # Create buttons for different image formats with emojis
        view = View()
        view.add_item(Button(label="WEBP", url=f"{avatar_url}?format=webp", style=ButtonStyle.link, emoji=Emojis.link))
        view.add_item(Button(label="PNG", url=f"{avatar_url}?format=png", style=ButtonStyle.link, emoji=Emojis.link))
        view.add_item(Button(label="JPG", url=f"{avatar_url}?format=jpg", style=ButtonStyle.link, emoji=Emojis.link))

        await ctx.reply(embed=embed, view=view)



    @hybrid_command(
            name="userinfo", 
            aliases=["ui"],
            usage="userinfo (member)",
            example="userinfo @vert",
    )
    async def userinfo(self, ctx, member: Union[Member, User] = None):
        """
        Displays information about a user.
        """
        member = member or ctx.author  # If no member is specified, use the command invoker

        # Get mutual servers
        mutual_servers = len([guild for guild in self.bot.guilds if guild.get_member(member.id)])

        # Fetch the member's profile to get the banner
        user_profile = await self.bot.fetch_user(member.id)

        # Define the US Eastern timezone
        eastern = pytz_timezone('US/Eastern')

        # Check if the member is in the current guild
        if isinstance(member, Member):
            # Get user presence with emoji
            presence_emoji = {
                "online": Emojis.online,
                "offline": Emojis.offline,
                "dnd": Emojis.dnd,
                "idle": Emojis.idle,
            }
            presence = f"{presence_emoji.get(str(member.status), '')} {str(member.status).title()}"

            # Get user devices
            devices = []
            if member.web_status != Status.offline:
                devices.append("Web")
            if member.mobile_status != Status.offline:
                devices.append("Mobile")
            if member.desktop_status != Status.offline:
                devices.append("Desktop")
            device = ", ".join(devices) if devices else "None"

            # Get account creation and join dates
            created_at = member.created_at.astimezone(eastern)
            joined_at = member.joined_at.astimezone(eastern)

            # Manually format dates without the day of the week
            created_at_str = created_at.strftime("%B %d, %Y %I:%M %p")
            joined_at_str = joined_at.strftime("%B %d, %Y %I:%M %p")

            # Check if the user is a server booster
            if member.premium_since:
                boosted_at = member.premium_since.astimezone(eastern)
                boosted_at_str = boosted_at.strftime("%B %d, %Y %I:%M %p")
                boost_info = f"{Emojis.separator_curved}**Boosted:** <t:{int(boosted_at.timestamp())}:f> ( <t:{int(boosted_at.timestamp())}:R> )\n"
            else:
                boost_info = ""

            # Get roles, excluding @everyone
            roles = [role.mention for role in member.roles if role.name != "@everyone"]
            roles_count = len(roles)
            roles = ", ".join(roles) if roles else "None"

            # Check if the user is an admin
            is_admin = any(role.permissions.administrator for role in member.roles)

            # Get join position
            members = sorted(ctx.guild.members, key=lambda m: m.joined_at)
            join_pos = members.index(member) + 1

            # Create the embed
            embed = Embed(
                title=f"{member}",  # Use the full name here
                color=Colors.oxy  # Set the color of the embed
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_author(name=f"{member.display_name} ( {member.id} )", icon_url=member.display_avatar.url)  # Use the nickname here
            embed.add_field(name="", value=f"{Emojis.separator_straight}**Presence:** {presence}\n{Emojis.separator_straight}**Device(s):** {device}", inline=False)
            embed.add_field(name="**Dates**", value=(
                f"{Emojis.separator_curved}**Created:** <t:{int(created_at.timestamp())}:f> ( <t:{int(created_at.timestamp())}:R> )\n"
                f"{Emojis.separator_curved}**Joined:** <t:{int(joined_at.timestamp())}:f> ( <t:{int(joined_at.timestamp())}:R> )\n"
                f"{boost_info}"
            ), inline=False)
            embed.add_field(name=f"**Roles [{roles_count}]**", value=f"{roles}", inline=False)
            embed.set_footer(
                text=f"{'Administrator • ' if is_admin else ''}join pos: {join_pos} • {mutual_servers} mutual servers",
                icon_url="https://cdn.discordapp.com/emojis/1254266285857177740.png"
            )

            # Create buttons for avatar and banner
            view = View()
            view.add_item(Button(label="Avatar", style=ButtonStyle.link, url=member.display_avatar.url, emoji=Emojis.link))
            
            # Check if the member has a banner and add the button if it exists
            if user_profile.banner:
                view.add_item(Button(label="Banner", style=ButtonStyle.link, url=user_profile.banner.url, emoji=Emojis.link))

            await ctx.reply(embed=embed, view=view)
        else:
            # Handle the case where the member is not in the current guild
            created_at = member.created_at.astimezone(eastern)

            # Manually format dates without the day of the week
            created_at_str = created_at.strftime("%B %d, %Y %I:%M %p")

            # Create the embed for users not in the current guild
            embed = Embed(
                title=f"{member}",  # Use the full name here
                color=Colors.sorrow  # Set the color of the embed
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_author(name=f"{member.display_name} ( {member.id} )", icon_url=member.display_avatar.url)  # Use the nickname here
            embed.add_field(name="**Information**", value=(
                f"{Emojis.separator_curved}**Accent Color:** `{member.accent_color}`\n"
                f"{Emojis.separator_curved}**User ID:** `{member.id}`\n"
                f"{Emojis.separator_curved}**Created:** <t:{int(created_at.timestamp())}:f> ( <t:{int(created_at.timestamp())}:R> )"
            ), inline=False)
            embed.add_field(name=f"**Roles [0]**", value="Not in guild", inline=False)
            embed.set_footer(
                text=f"Global User • join pos: N/A • {mutual_servers} mutual servers",
                icon_url="https://cdn.discordapp.com/emojis/1254266285857177740.png"
            )

            # Create buttons for avatar and banner
            view = View()
            view.add_item(Button(label="Avatar", style=ButtonStyle.link, url=member.display_avatar.url, emoji=Emojis.link))
            
            # Check if the member has a banner and add the button if it exists
            if user_profile.banner:
                view.add_item(Button(label="Banner", style=ButtonStyle.link, url=user_profile.banner.url, emoji=Emojis.link))

            await ctx.reply(embed=embed, view=view)

            
    @command(
        name="inrole",
        usage="inrole <role>",
        extras={"example": "inrole admin"},
    )
    @cooldown(1, 2, BucketType.user)
    async def inrole(self, ctx: Context, *, role_name: str):
        """
        Lists all members in the specified role.
        """
        try:
            role = await RoleConverter().convert(ctx, role_name)
        except RoleNotFound:
            await ctx.warn(f'{ctx.author.mention}: Role **{role_name}** not found.')
            return
    
        members = role.members
        if not members:
            await ctx.warn(f"{ctx.author.mention}: No members found in the role {role.name}.")
            return
    
        # Create pages for the paginator
        pages = []
        per_page = 10
        for i in range(0, len(members), per_page):
            chunk = members[i:i + per_page]
            member_list = "\n".join(f"{Emojis.separator_curved} `#{i+1:02}` {member.mention} ( `{member.id}` )" for i, member in enumerate(chunk, start=i))
            embed = Embed(title=f"Members in {role.name}", description=member_list)
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed.set_footer(text=f"Page {i//per_page + 1}/{(len(members) + per_page - 1) // per_page} ({len(members)} members)", icon_url=self.bot.user.avatar.url)
            pages.append(embed)
    
        # Initialize and start the paginator
        paginator = Paginator(ctx, pages)   
        await paginator.start()

    @command(
        name="inrole",
        usage="inrole <role>",
        extras={"example": "inrole admin"},
    )
    @cooldown(1, 2, BucketType.user)
    async def inrole(self, ctx: Context, *, role_name: str):
        """
        Lists all members in the specified role.
        """
        try:
            role = await RoleConverter().convert(ctx, role_name)
        except RoleNotFound:
            await ctx.warn(f'{ctx.author.mention}: Role **{role_name}** not found.')
            return
    
        members = role.members
        if not members:
            await ctx.warn(f"{ctx.author.mention}: No members found in the role {role.name}.")
            return
    
        # Create pages for the paginator
        pages = []
        per_page = 10
        for i in range(0, len(members), per_page):
            chunk = members[i:i + per_page]
            member_list = "\n".join(f"{Emojis.separator_curved} `#{i+1:02}` {member.mention} ( `{member.id}` )" for i, member in enumerate(chunk, start=i))
            embed = Embed(title=f"Members in {role.name}", description=member_list)
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            embed.set_footer(text=f"Page {i//per_page + 1}/{(len(members) + per_page - 1) // per_page} ({len(members)} members)", icon_url=self.bot.user.avatar.url)
            pages.append(embed)
    
        # Initialize and start the paginator
        paginator = Paginator(ctx, pages)
        await paginator.start()

    @command(
        name="serverbanner",
        aliases=["sbanner "],
        usage="serverbanner",
        extras={"example": "serverbanner"},
    )
    @cooldown(1, 2, BucketType.user)
    async def server_banner(self, ctx):
        """
        Displays the server's banner with buttons for different image formats.
        """
        guild = ctx.guild
        if not guild.banner:
            await ctx.warn("This server has no **banner**.", reference=ctx.message)
            return

        banner_url = guild.banner.url  # Get the URL of the server's banner

        embed = Embed(
            description=f"**[{guild.name}'s banner]({banner_url})**",
            color=Colors.oxy  # Ensure Colors.oxy is defined and accessible
        )
        embed.set_image(url=banner_url)
        embed.set_footer(text=f"Request by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)

        # Create buttons for different image formats with emojis
        view = View()
        view.add_item(Button(label="WEBP", url=f"{banner_url}?format=webp", style=ButtonStyle.link, emoji=Emojis.link))
        view.add_item(Button(label="PNG", url=f"{banner_url}?format=png", style=ButtonStyle.link, emoji=Emojis.link))
        view.add_item(Button(label="JPG", url=f"{banner_url}?format=jpg", style=ButtonStyle.link, emoji=Emojis.link))

        await ctx.reply(embed=embed, view=view)

    @command(
        name="banner",
        usage="banner [member]",
        extras={"example": "banner @username"},
    )
    @cooldown(1, 2, BucketType.user)
    async def banner(self, ctx, member: Union[Member, User] = None):
        """
        Displays the banner of the specified user or the command invoker if no user is specified.
        """
        member = member or ctx.author  # If no member is specified, use the command invoker

        # Fetch the member's profile to get the banner
        user_profile = await self.bot.fetch_user(member.id)

        if not user_profile.banner:
            await ctx.warn(f"{member.mention} has no **banner**.", reference=ctx.message)
            return

        banner_url = user_profile.banner.url  # Get the URL of the user's banner

        embed = Embed(
            description=f"**[{member.name}'s banner]({banner_url})**",
            color=Colors.oxy  # Ensure Colors.oxy is defined and accessible
        )
        embed.set_image(url=banner_url)
        embed.set_footer(text=f"Request by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)

        # Create buttons for different image formats with emojis
        view = View()
        view.add_item(Button(label="WEBP", url=f"{banner_url}?format=webp", style=ButtonStyle.link, emoji=Emojis.link))
        view.add_item(Button(label="PNG", url=f"{banner_url}?format=png", style=ButtonStyle.link, emoji=Emojis.link))
        view.add_item(Button(label="JPG", url=f"{banner_url}?format=jpg", style=ButtonStyle.link, emoji=Emojis.link))

        await ctx.reply(embed=embed, view=view)

    @command(
        name="serveravatar",
        aliases=["guildavatar"],
        usage="serveravatar [member]",
        extras={"example": "serveravatar @username"},
    )
    @cooldown(1, 2, BucketType.user)
    async def server_avatar(self, ctx, member: Union[Member, None] = None):
        """
        Displays the server-specific avatar of the specified user or the command invoker if no user is specified.
        """
        member = member or ctx.author  # If no member is specified, use the command invoker

        if not member.guild_avatar:
            if member == ctx.author:
                await ctx.warn("You don't have a **server avatar** set.", reference=ctx.message)
            else:
                await ctx.warn(f"{member.mention} has no **server avatar**.", reference=ctx.message)
            return

        avatar_url = member.guild_avatar.url  # Get the URL of the user's server-specific avatar

        embed = Embed(
            description=f"**[{member.name}'s server avatar]({avatar_url})**",
            color=Colors.oxy  # Ensure Colors.oxy is defined and accessible
        )
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"Request by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)

        # Create buttons for different image formats with emojis
        view = View()
        view.add_item(Button(label="WEBP", url=f"{avatar_url}?format=webp", style=ButtonStyle.link, emoji=Emojis.link))
        view.add_item(Button(label="PNG", url=f"{avatar_url}?format=png", style=ButtonStyle.link, emoji=Emojis.link))
        view.add_item(Button(label="JPG", url=f"{avatar_url}?format=jpg", style=ButtonStyle.link, emoji=Emojis.link))

        await ctx.send(embed=embed, view=view)

    @command(
        name="membercount",
        aliases=["mc"],
        usage="membercount",
        extras={"example": "membercount"},
    )
    @cooldown(1, 2, BucketType.user)
    async def member_count(self, ctx):
        """
        Displays the total number of members, humans, and bots in the server.
        """
        guild = ctx.guild

        # Count humans and bots
        human_count = sum(1 for member in guild.members if not member.bot)
        bot_count = sum(1 for member in guild.members if member.bot)
        total_count = guild.member_count

        # Create the embed
        embed = Embed(
            title=f"{guild.name}",
            color=Colors.oxy  # Ensure Colors.oxy is defined and accessible
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(
            name="",
            value=f"```yaml\nMembers: {total_count}\nHumans: {human_count}\nBots: {bot_count}\n```",
            inline=False
        )
        embed.set_footer(text=f"Request by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)

        await ctx.reply(embed=embed)

    @command(
            name="invite",
            usage="invite",
            extras={"example": "invite"},
    )
    async def invite(self, ctx: Context):
        """
        Generates an invite link for the bot.
        """
        await ctx.utility(f"{Emojis.utils2} [Invite link](https://discord.com/oauth2/authorize?client_id=1256728352983744634&permissions=8&integration_type=0&scope=bot)", reference=ctx.message)

    @command(
        name="inviteinfo",
        aliases=["invinfo"],
        usage="inviteinfo <invite_code>",
        extras={"example": "inviteinfo abc123"},
    )
    @cooldown(1, 2, BucketType.user)
    async def invite_info(self, ctx: Context, invite_code: Optional[str]):
        """
        Displays information about a specific invite.
        """
        if not invite_code:
            await ctx.warn("Please provide an invite code.", reference=ctx.message)
            return

        try:
            invite = await self.bot.fetch_invite(invite_code, with_counts=True)
            guild = invite.guild
        except discord.NotFound:
            await ctx.warn("Could not fetch invite: Invite not found.", reference=ctx.message)
            return
        except discord.HTTPException as e:
            await ctx.warn(f"Could not fetch invite: {str(e)}", reference=ctx.message)
            return
        inviter = invite.inviter
        channel = invite.channel
        created_at = guild.created_at  # Use guild's creation date
        # Create the embed
        embed = Embed(
            title=f"{guild.name} ({guild.id})",
            color=Colors.oxy  # Ensure Colors.oxy is defined and accessible
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.set_author(name=guild.name, icon_url=guild.icon.url if guild.icon else None)
        if created_at:
            created_at_timestamp = int(created_at.timestamp())
            description = f"<t:{created_at_timestamp}:f> (<t:{created_at_timestamp}:R>)"
        else:
            description = "Creation date not available"
        embed.description = description
        embed.add_field(
            name="Guild",
            value=(
                f"```css\n"
                f"Members: {invite.approximate_member_count}\n"
                f"Members Online: {invite.approximate_presence_count}\n"
                f"Verification Level: {guild.verification_level.name.capitalize()}\n"
                f"```"
            ),
            inline=True
        )
        embed.add_field(
            name="Information",
            value=(
                f"```css\n"
                f"Inviter: {inviter.name if inviter else 'Vanity URL'}\n"
                f"Channel: {channel.name if channel else 'N/A'}\n"
                f"Created: {created_at.strftime('%Y-%m-%d %H:%M:%S %Z') if created_at else 'N/A'}\n"
                f"```"
            ),
            inline=True
        )
        embed.set_footer(text=f"Request by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.reply(embed=embed)
    

    @group(
        name="boosters",
        invoke_without_command=True,
    )
    @has_permissions(administrator=True)
    async def boosters_group(self, ctx: Context):
        """
        Base command for booster-related inquiries. If no sub-command is provided,
        it defaults to listing the current boosters.
        """
        if ctx.invoked_subcommand is None:
            await self.boosters(ctx)

    @boosters_group.command(
        name="list",
        aliases=["current"],
        help="Lists all current boosters in the server."
    )
    async def boosters(self, ctx: Context):
        """
        Lists all current boosters in the server.
        """
        boosters = ctx.guild.premium_subscribers
        if not boosters:
            await ctx.warn("No boosters found in this server.")
            return

        # Create pages for the paginator
        pages = []
        per_page = 10
        for i in range(0, len(boosters), per_page):
            chunk = boosters[i:i + per_page]
            booster_list = "\n".join(
                f"{Emojis.separator_curved} `#{i+1:02}` {booster.mention} ( `{booster.id}` ) boosted **{discord.utils.format_dt(booster.premium_since, style='R')}**"
                for i, booster in enumerate(chunk, start=i)
            )
            embed = discord.Embed(title="Current boosters", description=booster_list, color=Colors.oxy)
            embed.set_footer(text=f"Page {i//per_page + 1}/{(len(boosters) + per_page - 1) // per_page} ({len(boosters)} entries)")
            pages.append(embed)

        # Initialize and start the paginator
        paginator = Paginator(ctx, pages)
        await paginator.start()

        # Update the previous boosters list
        self.previous_boosters = {booster.id for booster in boosters}

    @boosters_group.command(
        name="lost",
        aliases=["lostboosters"],
        help="Lists all users who have lost their booster status."
    )
    async def boosters_lost(self, ctx: Context):
        """
        Lists all users who have lost their booster status.
        """
        current_boosters = {booster.id for booster in ctx.guild.premium_subscribers}
        lost_boosters = self.previous_boosters - current_boosters

        if not lost_boosters:
            await ctx.warn("No boosters have been lost since the last check.")
            return

        # Create the list of lost boosters
        lost_booster_list = "\n".join(
            f"{Emojis.separator_curved} `#{i+1:02}` <@{booster_id}> ( `{booster_id}` )"
            for i, booster_id in enumerate(lost_boosters)
        )

        # Create the embed
        embed = discord.Embed(
            title="Lost boosters",
            description=lost_booster_list,
            color=Colors.oxy
        )
        embed.set_footer(text=f"Total lost boosters: {len(lost_boosters)}")

        await ctx.send(embed=embed)

    @command(name="bots", usage="bots", extras={"example": "bots"})
    @cooldown(1, 2, BucketType.user)
    async def bots(self, ctx):
        bots = [member for member in ctx.guild.members if member.bot]
        if not bots:
            await ctx.warn(f"{ctx.author.mention}: No bots found in this server.")
            return

        pages = [
            discord.Embed(
                title="List of Bots",
                description="\n".join(
                    f"{Emojis.separator_curved} `#{i+1:02}` {bot.mention} ( `{bot.id}` )"
                    for i, bot in enumerate(bots_chunk, start=page * 10)
                ),
                color=Colors.oxy
            ).set_footer(text=f"Page {page+1}/{(len(bots) + 9) // 10} ({len(bots)} bots)")
            for page, bots_chunk in enumerate([bots[i:i + 10] for i in range(0, len(bots), 10)])
        ]

        paginator = Paginator(ctx, pages)
        await paginator.start()

    @command(name="invites", usage="invites", brief="manage guild", extras={"example": "invites"})
    @cooldown(1, 2, BucketType.user)
    @has_permissions(manage_guild=True)
    async def invites(self, ctx):
        invites = await ctx.guild.invites()
        if not invites:
            await ctx.error(f"{ctx.author.mention}: No invites found in this server.")
            return

        pages = [
            discord.Embed(
                title=f"Invites in {ctx.guild.name}",
                description="\n".join(
                    f"{Emojis.separator_curved} `#{i+1:02}` [{invite.code}]({invite.url}) by {invite.inviter.mention} expires {discord.utils.format_dt(invite.expires_at, style='R') if invite.expires_at else 'Never'}"
                    for i, invite in enumerate(invites_chunk, start=page * 10)
                ),
                color=Colors.oxy
            ).set_footer(text=f"Page {page+1}/{(len(invites) + 9) // 10} ({len(invites)} invites)")
            for page, invites_chunk in enumerate([invites[i:i + 10] for i in range(0, len(invites), 10)])
        ]

        paginator = Paginator(ctx, pages)
        await paginator.start()

    @command(name="emojis", usage="emojis", extras={"example": "emojis"})
    @cooldown(1, 2, BucketType.user)
    async def emojis(self, ctx):
        emojis = ctx.guild.emojis
        if not emojis:
            await ctx.warn(f"{ctx.author.mention}: No emojis found in this server.")
            return

        pages = [
            discord.Embed(
                title=f"Emojis in {ctx.guild.name}",
                description="\n".join(
                    f"{Emojis.separator_curved} `#{i+1:02}` {emoji} ( [`{emoji.id}`](https://cdn.discordapp.com/emojis/{emoji.id}.png) )"
                    for i, emoji in enumerate(emojis_chunk, start=page * 10)
                ),
                color=Colors.oxy
            ).set_footer(text=f"Page {page+1}/{(len(emojis) + 9) // 10} ({len(emojis)} emojis)")
            for page, emojis_chunk in enumerate([emojis[i:i + 10] for i in range(0, len(emojis), 10)])
        ]

        paginator = Paginator(ctx, pages)
        await paginator.start()

    @command(name="stickers", usage="stickers", extras={"example": "stickers"})
    @cooldown(1, 2, BucketType.user)
    async def stickers(self, ctx):
        stickers = ctx.guild.stickers
        if not stickers:
            await ctx.warn(f"{ctx.author.mention}: No stickers found in this server.")
            return

        pages = [
            discord.Embed(
                title=f"Stickers in {ctx.guild.name}",
                description="\n".join(
                    f"{Emojis.separator_curved} `#{i+1:02}` {sticker.name} ( [`{sticker.id}`](https://cdn.discordapp.com/stickers/{sticker.id}.png) )"
                    for i, sticker in enumerate(stickers_chunk, start=page * 10)
                ),
                color=Colors.oxy
            ).set_footer(text=f"Page {page+1}/{(len(stickers) + 9) // 10} ({len(stickers)} stickers)")
            for page, stickers_chunk in enumerate([stickers[i:i + 10] for i in range(0, len(stickers), 10)])
        ]

        paginator = Paginator(ctx, pages)
        await paginator.start()

    @command(
        name="firstmessage",
        usage="firstmessage [#channel]",
        extras={"example": "firstmessage #staff-chat"},
    )
    @cooldown(1, 2, BucketType.user)
    async def firstmessage(self, ctx: Context, channel: Optional[TextChannel] = None):
        """
        Provides a link to the first message sent by the user in the specified channel or the current channel if none is specified.
        """
        channel = channel or ctx.channel
        user = ctx.author

        # Fetch the first message sent by the user in the specified channel
        first_message_url = None
        async for message in channel.history(limit=1000, oldest_first=True):
            if message.author == user:
                first_message_url = message.jump_url
                break

        if not first_message_url:
            await ctx.warn(f"{user.mention}: No messages found from you in {channel.mention}.")
            return

        # Create the embed
        await ctx.utility(f"{Emojis.utils2} Jump to the [**first message**]({first_message_url}) sent by {user.mention} in {channel.mention}", reference=ctx.message)

    @hybrid_command(
        name="youngest",
        aliases=["newest", "youngestaccount", "baby"],
        usage="youngest",
        extras={"example": "youngest"},
    )
    async def youngest(self, ctx: Context):
        """
        Get the newest account created in the server
        """
        def get_creation_date(member):
            return member.created_at

        # Convert members to a list and sort by creation date, newest first
        members = list(ctx.guild.members)
        if not members:
            await ctx.send("No members found in the server.")
            return

        members.sort(key=get_creation_date, reverse=True)
        member = members[0]
        
        embed = Embed(
            description=f"{member.mention} is the newest account created in **{ctx.guild.name}**.",
            color=Colors.oxy 
        )
        embed.set_author(name=member.display_name, icon_url=member.avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name=f"{Emojis.separator_straight} Joined", value=f"{Emojis.separator_curved}{utils.format_dt(member.joined_at, 'R')}", inline=False)
        embed.add_field(name=f"{Emojis.separator_straight} Created", value=f"{Emojis.separator_curved}{utils.format_dt(member.created_at, 'R')}", inline=False)
        
        await ctx.send(embed=embed)

    @hybrid_command(
        name="oldest",
        aliases=["elder", "oldestaccount", "og"],
        usage="oldest",
        extras={"example": "oldest"},
    )
    async def oldest(self, ctx: Context):
        """
        Get the oldest account in the server
        """
        # Ensure members are sorted by creation date, oldest first
        member = sorted(
            [m for m in ctx.guild.members if not m.bot],
            key=lambda m: m.created_at
        )[0]
        
        embed = Embed(
            description=f"{member.mention} is the oldest account in **{ctx.guild.name}**.",
            color=Colors.oxy
        )
        embed.set_author(name=member.display_name, icon_url=member.avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name=f"{Emojis.separator_straight} Joined", value=f"{Emojis.separator_curved}{utils.format_dt(member.joined_at, 'R')}", inline=False)
        embed.add_field(name=f"{Emojis.separator_straight} Created", value=f"{Emojis.separator_curved}{utils.format_dt(member.created_at, 'R')}", inline=False)
        
        await ctx.send(embed=embed)

    @command(
        name="credits",
        aliases=["credit", "creds", "cred"]
    )
    async def credits(self, ctx: Context):
        """
        Sends the credits for the bot
        """
        await ctx.utility(f"> Developed & maintained by **@1chxnk** `1247076592556183598` \n > this is a side project , did it dolo")

    @command(name="uptime", help="Displays the bot's uptime.")
    @cooldown(1, 2, BucketType.user)
    async def uptime(self, ctx):
        uptime_str = self.format_time_since(self.bot.uptime)
        await self.send_embed(
            ctx,
            title=None,
            description=f"{Emojis.uptime} {self.bot.user.mention} has been online for `{uptime_str}`",
            color=Colors.oxy
        )


 
        
        
    @command(name="weather")
    @cooldown(1, 2, BucketType.user)
    async def weather(self, ctx: Context, *, location: str):
        await ctx.typing()

        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={self.weather_api_key}&units=metric"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()

        if data.get('cod') != 200:
            await ctx.warn(f"{ctx.author.mention}: Could not find weather data for {location}.")
            return

        weather = data['weather'][0]
        main = data['main']
        wind = data['wind']
        sys = data['sys']

        temp_celsius = main['temp']
        temp_fahrenheit = (temp_celsius * 9/5) + 32

        local_tz = pytz.FixedOffset(data['timezone'] // 60)
        sunrise_time = datetime.utcfromtimestamp(sys['sunrise']).replace(tzinfo=pytz.utc).astimezone(local_tz)
        sunset_time = datetime.utcfromtimestamp(sys['sunset']).replace(tzinfo=pytz.utc).astimezone(local_tz)

        embed = discord.Embed(
            title=f"{weather['description'].title()} in {data['name']}, {sys['country']}",
            color=Colors.white,
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=f"http://openweathermap.org/img/wn/{weather['icon']}.png")
        embed.add_field(name="Temperature", value=f"{temp_celsius:.2f} °C / {temp_fahrenheit:.2f} °F", inline=True)
        embed.add_field(name="Wind", value=f"{wind['speed']} mph", inline=True)
        embed.add_field(name="Humidity", value=f"{main['humidity']}%", inline=True)
        embed.add_field(name="Sunrise", value=discord.utils.format_dt(sunrise_time, style='T'), inline=True)
        embed.add_field(name="Sunset", value=discord.utils.format_dt(sunset_time, style='T'), inline=True)
        embed.add_field(name="Visibility", value=f"{data['visibility'] / 1000:.1f} km", inline=True)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    async def get_cashapp_username(self, user_id):
        async with self.bot.db.acquire() as connection:
            return await connection.fetchval("SELECT cashapp_username FROM cashapp WHERE user_id = $1", user_id)

    async def set_cashapp_username(self, user_id, username):
        async with self.bot.db.acquire() as connection:
            await connection.execute("INSERT INTO cashapp (user_id, cashapp_username) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET cashapp_username = $2", user_id, username)

    @group(name="cashapp", invoke_without_command=True)
    async def cashapp_group(self, ctx: Context):
        saved_username = await self.get_cashapp_username(ctx.author.id)

        if not saved_username:
            await ctx.warn("Use `cashapp set <username>` to set your CashApp username.")
            return

        profile_url = f"https://cash.app/{saved_username}"
        profile_pic_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Square_Cash_app_logo.svg/120px-Square_Cash_app_logo.svg.png"  # Default thumbnail
        html = await self.fetch_html(profile_url)
        if not html:
            await ctx.send(f"{ctx.author.mention}: [`{saved_username}`](https://cash.app/{saved_username}) was **not found**.")
            return

        soup = BeautifulSoup(html, 'html.parser')  # Changed from 'lxml' to 'html.parser'
        img_tag = soup.find('img', {'class': 'profile-picture-class'})  # Replace with actual class or id
        if img_tag and 'src' in img_tag.attrs:
            profile_pic_url = img_tag['src']

        embed = discord.Embed(
            description=f"[Pay ${saved_username} here]({profile_url})",
            color=0x00FF00
        )
        embed.set_thumbnail(url=profile_pic_url)
        embed.set_author(name=f"@{saved_username}", icon_url=ctx.author.avatar.url)
        embed.set_footer(text="CashApp", icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Square_Cash_app_logo.svg/120px-Square_Cash_app_logo.svg.png")

        await ctx.send(embed=embed)

    @cashapp_group.command(
            name="set", 
            help="Set your CashApp username.",
            usage="cashapp set (username)",
            extras={"example": "cashapp set omtfiji"}
            )
    async def set_cashapp(self, ctx: Context, username: str):
        await self.set_cashapp_username(ctx.author.id, username)
        await ctx.approve(f"Your CashApp username has been set to `{username}`.")

    @cashapp_group.command(
            name="search", 
            help="Search for a CashApp username.",
            usage="cashapp search (username)",
            extras={"example": "cashapp search omtfiji"}
            )
    
    async def search_cashapp(self, ctx: Context, username: str):
        profile_url = f"https://cash.app/{username}"
        profile_pic_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Square_Cash_app_logo.svg/120px-Square_Cash_app_logo.svg.png"  # Default thumbnail
        html = await self.fetch_html(profile_url)
        if not html:
            await ctx.send(f"{ctx.author.mention}: [`{username}`](https://cash.app/{username}) was **not found**.")
            return

        soup = BeautifulSoup(html, 'html.parser')  # Changed from 'lxml' to 'html.parser'
        img_tag = soup.find('img', {'class': 'profile-picture-class'})  # Replace with actual class or id
        if img_tag and 'src' in img_tag.attrs:
            profile_pic_url = img_tag['src']

        embed = discord.Embed(
            title="CashApp Search Result",
            description=f"[Pay ${username} here]({profile_url})",
            color=0x00FF00
        )
        embed.set_thumbnail(url=profile_pic_url)
        embed.set_author(name=f"@{username}", icon_url=ctx.author.avatar.url)
        embed.set_footer(text="CashApp", icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Square_Cash_app_logo.svg/120px-Square_Cash_app_logo.svg.png")

        await ctx.send(embed=embed)



async def setup(bot):
    await bot.add_cog(Information(bot))
