import asyncio
import asyncpg
import discord
import os
import logging
from typing import Any 
from tools.Managers.Help import Help
from pathlib import Path
from discord.utils import utcnow
from datetime import datetime, timezone
from loguru import logger
from dotenv import load_dotenv
from tools.Managers.Classes import Emojis, Colors
from tools.Managers.Context import CustomContext
from discord.ext import commands
from cashews import cache

from discord import (
    Embed,
    Intents,
    AllowedMentions,
    Message,
    AuditLogEntry,
    Streaming,
    Activity,
    ActivityType,
    Status,
)

from discord.ext.commands import (
    AutoShardedBot,
    CommandOnCooldown,
    CommandError,
    CommandNotFound,
    MissingRequiredArgument,
    when_mentioned_or,
)
logging.getLogger("discord").setLevel(logging.CRITICAL)
logging.getLogger("discord.http").setLevel(logging.CRITICAL)
logging.getLogger("discord.client").setLevel(logging.CRITICAL)
logging.getLogger("discord.gateway").setLevel(logging.CRITICAL)
logging.getLogger("discord.ext.ipc.server").setLevel(logging.CRITICAL)
logging.getLogger("pomice").setLevel(logging.CRITICAL)
load_dotenv()
cache.setup("mem://")









class oxy(commands.AutoShardedBot):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self: "oxy"):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        
    def __init__(self: "oxy"):
        intents = Intents.all()
        intents.members = True  # SERVER MEMBERS INTENT
        intents.message_content = True  # MESSAGE CONTENT INTENT

        super().__init__(
            auto_update=False,
            intents=intents,
            help_command=Help(),
            command_prefix=self.get_prefix,
            case_insensitive=True,
            owner_ids=[1247076592556183598, 971464344749629512],
            allowed_mentions=AllowedMentions(
                replied_user=False,
                everyone=False,
                roles=False,
                users=True,
            ),
        )
        self.uptime: datetime = utcnow()
        self.start_time = datetime.now(timezone.utc)
        self.version = "v1.0.0"
        self.description = "A bot that is made by oxycodone"
        self.prefix_cache = {}
        self.run(
            os.getenv('TOKEN'),
            log_handler=None,
        )
            
    @property
    def members(self):
        return list(self.get_all_members())

    @property
    def channels(self):
        return list(self.get_all_channels())

    @property
    def commandss(self):
        return set(self.walk_commands())

    async def setup_hook(self: "oxy"):
        try:
            self.db = await asyncpg.create_pool(
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_DATABASE'),
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT'),
                statement_cache_size=0  # Enable statement caching
            )
            with open("tools/Schema/tables.sql", "r") as f:
                schema = f.read()
                await self.db.execute(schema)

            logger.info("Database connection successfully established and tables are ready.")
        except Exception as e:
            logger.error(f"Failed to establish database connection: {e}")
    
        # Load extensions
        await self.load_extension("jishaku")
        for file in Path("cogs").rglob("*.py"):
            extension = f"{file.parent}.{file.stem}".replace("/", ".")
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")

    async def get_context(self, message, *, cls=CustomContext):
        return await super().get_context(message, cls=cls)
    
    async def get_prefix(self, message: Message) -> Any:
        guild_id = message.guild.id
        if guild_id not in self.prefix_cache:
            prefix = await self.db.fetchval(
                """
                SELECT prefix FROM prefixes
                WHERE guild_id = $1
                """,
                guild_id,
            ) or ';'
            self.prefix_cache[guild_id] = prefix
        return when_mentioned_or(self.prefix_cache[guild_id])(self, message)
    
    async def process_commands(self: "oxy", message: Message):
        if not message.guild:
            return
        
        ctx = await self.get_context(message)
        await super().process_commands(message)

    async def on_message(self, message):
        ctx = await self.get_context(message)
        
        if message.content in [f"<@{message.guild.me.id}>", f"<@!{message.guild.me.id}>"]:
            prefix = self.prefix_cache.get(message.guild.id, ';')
            if ctx.command is None:
                await ctx.utility(
                    f"{Emojis.bot} guild prefix is **`{prefix}`** [oxycodone](https://discord.gg/RY3yhVsG)", 
                    reference=ctx.message
                )
        
        await self.process_commands(message)

    async def on_command_error(self: "oxy", ctx: CustomContext, exception: CommandError):
        if isinstance(exception, CommandNotFound):
            pass
        elif isinstance(exception, CommandOnCooldown):
            await ctx.cooldown(
                f"{ctx.author.mention} You're on a [cooldown](https://discord.gg/RY3yhVsG) & cannot use `{ctx.command.name}` for another **{int(exception.retry_after)}** second(s)", 
                reference=ctx.message,
            )
        elif isinstance(exception, commands.MissingPermissions): 
            await ctx.error(
                f"You're missing [`{', '.join(exception.missing_permissions)}`](https://discord.gg/RY3yhVsG) **permissions**", 
                reference=ctx.message, 
                delete_after=20
            )
        elif isinstance(exception, commands.BotMissingPermissions): 
            await ctx.error(
                f"I'm missing [`{', '.join(exception.missing_permissions)}`](https://discord.gg/RY3yhVsG) **permissions**", 
                reference=ctx.message, 
                delete_after=20
            )
        elif isinstance(exception, commands.DisabledCommand):
            await ctx.error(
                f"{ctx.author.mention} This command is disabled.", 
                reference=ctx.message, 
                delete_after=10
            )
        elif isinstance(exception, commands.BadArgument):
            await ctx.error(
                f"{ctx.author.mention} Invalid argument for `{ctx.command.name}`.", 
                reference=ctx.message, 
                delete_after=10
            )
        elif isinstance(exception, commands.BadUnionArgument):
            await ctx.error(
                f"{ctx.author.mention} Invalid argument for `{ctx.command.name}`.", 
                reference=ctx.message, 
                delete_after=10
            )
        elif isinstance(exception, commands.MissingRequiredArgument):
            await ctx.send_help(ctx.command)

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        
        # Set initial status to idle
        await self.change_presence(
            status=Status.idle,
            activity=Activity(
                type=ActivityType.watching,
                name=f"over {len(self.users)} users"
            )
        )
        
        self.loop.create_task(self.change_status())

    async def change_status(self):
        while True:
            # Set status to idle and watching
            await self.change_presence(
                status=Status.idle,
                activity=Activity(
                    type=ActivityType.watching,
                    name=f"over {len(self.users)} users"
                )
            )
            await asyncio.sleep(300)

            # Set status to idle and streaming
            await self.change_presence(
                status=Status.idle,
                activity=Streaming(
                    name="in discord.gg/TmSA58Qxyq",
                    url="https://www.twitch.tv/fanum"
                )
            )
            await asyncio.sleep(600)

            # Set status to idle and no activity
            await self.change_presence(
                status=Status.idle,
                activity=None
            )
            await asyncio.sleep(300)



# Ensure this is the last statement
if __name__ == "__main__":
    bot = oxy()