import logging
from tools.Managers.Context import CustomContext as Context
from tools.oxy import oxy
from discord.utils import format_dt
from tools.Managers.Classes import Colors, Emojis
import discord
import aiohttp
from asyncio import gather
import asyncio

from datetime import (
    datetime, 
    timezone
)


from discord.ext.commands import(
    Cog,
    
)

from discord import (
    Message, 
    Embed, 
    Member,
    Webhook,
)
log = logging.getLogger(__name__)



class events(Cog):
    def __init__(self, bot):
        self.bot: oxy = bot
        self.db = None
        self.blacklisted_users: set[int] = set()


        """
        AFK EVENT.
        """
    @Cog.listener("on_message")
    async def check_afk(self, message: Message):
        ctx = await self.bot.get_context(message)
    
        if ctx.command:
            return  # Ignore messages that are commands

        user_id = message.author.id
        mentions = message.mentions

        afk_query = """
            DELETE FROM afk
            WHERE user_id = $1
            RETURNING date
        """
        afk_mention_query = """
            SELECT reason, date FROM afk
            WHERE user_id = $1
        """

        afk, afk2 = await asyncio.gather(
            self.bot.db.fetchval(afk_query, user_id),
            self.bot.db.fetchrow(afk_mention_query, mentions[0].id) if len(mentions) == 1 else asyncio.sleep(0)
        )

        if afk is not None:
            afk = afk.replace(tzinfo=timezone.utc)  # Ensure afk time is in UTC
            embed = Embed(
                color=Colors.oxy,
                description=f"👋 {message.author.mention}: **Welcome back** , you were last seen: {format_dt(afk, style='R')}"
            )
            await message.reply(embed=embed, mention_author=False)
            return

        if afk2 is not None and afk2 != asyncio.sleep(0):
            afk_time = afk2['date'].replace(tzinfo=timezone.utc)  # Ensure afk time is in UTC
            embed = Embed(
                color=Colors.oxy,
                description=f"{Emojis.warning}{mentions[0].mention} is currently afk , reason: **{afk2['reason']}**"
            )
            await message.reply(embed=embed, mention_author=False, delete_after=300)
            return



    """
    SNIPE EVENT.
    """
    @Cog.listener()
    async def on_message_delete(self, message: Message):
        if message.author.bot:
            return  # Ignore bot messages

        attachment_url = message.attachments[0].url if message.attachments else None

    

        try:
            # Insert the new deleted message
            await self.bot.db.execute(
                """
                INSERT INTO snipe_messages (author_id, content, attachment_url, deleted_at, channel_id)
                VALUES ($1, $2, $3, $4, $5)
                """,
                message.author.id,
                message.content,
                attachment_url,
                datetime.utcnow(),
                message.channel.id
            )
            # Delete messages older than 10 minutes
            await self.bot.db.execute(
                """
                DELETE FROM snipe_messages
                WHERE deleted_at < (NOW() - INTERVAL '10 minutes')
                """
            )
        except Exception as e:
            log.error(f"Failed to insert/delete deleted message: {e}")
    
    """
    EDIT SNIPE EVENT.
    """
    @Cog.listener()
    async def on_message_edit(self, before: Message, after: Message):
        if before.author.bot or before.content == after.content:
            return  # Ignore bot messages and unchanged content
    
        attachment_url = after.attachments[0].url if after.attachments else None
    
        try:
            # Insert the new edited message
            await self.bot.db.execute(
                """
                INSERT INTO edit_snipe_messages (author_id, before_content, after_content, attachment_url, edited_at, channel_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                before.author.id,
                before.content,
                after.content,
                attachment_url,
                datetime.utcnow(),
                after.channel.id
            )
            # Delete messages older than 10 minutes
            await self.bot.db.execute(
                """
                DELETE FROM edit_snipe_messages
                WHERE edited_at < (NOW() - INTERVAL '10 minutes')
                """
            )
        except Exception as e:
            log.error(f"Failed to insert/delete edited message: {e}")

    """
    AUTOROLE EVENT.
    """

    @Cog.listener()
    async def on_member_join(self, member: Member):
        try:
            async with self.bot.db.acquire() as connection:
                role_id = await connection.fetchval("SELECT role_id FROM autoroles WHERE guild_id = $1", member.guild.id)
                if role_id:
                    role = member.guild.get_role(role_id)
                    if role:
                        await member.add_roles(role)
                    # Removed logging statements
        except Exception as e:
            pass  # Silently handle the exception or you can handle it in another way if needed







async def setup(bot):
    await bot.add_cog(events(bot))