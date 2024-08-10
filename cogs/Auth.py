import discord
import datetime
from discord.ext import commands
from tools.Checks.checks import auth_perms
from tools.Managers.Classes import Colors, Emojis
from tools.Managers import Context
import logging

logging.basicConfig(level=logging.INFO)







class TrialView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

class Auth(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 1256851790985560148

    async def guild_change(self, state: str, guild: discord.Guild):
        if state == "joined":
            title = f"{Emojis.approve} `JOINED AN AUTHORIZED SERVER`"
            color = Colors.green
            description = f"The bot has joined an authorized server: **{guild.name}**"
        elif state == "left unauthorized":
            title = f"{Emojis.warning} `AUTOMATICALLY LEFT AN UNAUTHORIZED SERVER`"
            color = Colors.yellow
            description = None
        elif state == "added unauthorized":
            title = f"{Emojis.warning} `ADDED TO AN UNAUTHORIZED SERVER`"
            color = Colors.yellow
            description = None
        elif state == "removed":
            title = f"{Emojis.deny} `REMOVED FROM GUILD`"
            color = Colors.red
            description = None

        embed = discord.Embed(
            title=title,
            color=color,
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Guild Name", value=f"`{guild.name}`", inline=True)
        embed.add_field(name="Members", value=f"`{guild.member_count}`", inline=True)
        embed.add_field(name="Owned by", value=f"`{str(guild.owner)}`", inline=True)
        embed.add_field(name="Guild ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="Owner ID", value=f"`{guild.owner.id}`", inline=True)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.set_footer(text=f"Currently in {len(self.bot.guilds)} servers")

        if description:
            embed.description = description

        await self.bot.get_channel(self.channel_id).send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        if not self.bot.is_ready():
            return

        await self.guild_change("left unauthorized", guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if not guild.chunked:
            await guild.chunk(cache=True)

        check = await self.bot.db.fetchrow(
            "SELECT * FROM authorize WHERE guild_id = $1", guild.id
        )
        if not check:
            if channel := next(
                (
                    c
                    for c in guild.text_channels
                    if c.permissions_for(guild.me).send_messages
                ),
                None,
            ):
                button = discord.ui.Button(
                    label="Authorize your server",
                    emoji=Emojis.link,
                    url="https://discord.gg/95bNzAxX",
                    style=discord.ButtonStyle.link,
                )
                view = discord.ui.View()
                view.add_item(button)
                embed = discord.Embed(
                    color=0xe2cd65,
                    description=f"{Emojis.warning} **`LEAVING SERVER: This server has not been authorized.`**"
                )
                await channel.send(
                    embed=embed,
                    view=view
                )
                await self.guild_change("added unauthorized", guild)
                await guild.leave()  # Ensure the bot leaves the guild after sending the message
        else:
            await self.guild_change("joined", guild)

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            check = await self.bot.db.fetchrow(
                "SELECT * FROM authorize WHERE guild_id = $1", guild.id
            )
            if not check:
                await self.guild_change("left unauthorized", guild)
                await guild.leave()

    @commands.command(name="auth")
    @auth_perms()
    async def auth_guild(self, ctx: Context, guild_id: int):
        """
        Authorize a guild
        """
        if await self.bot.db.fetchrow("SELECT * FROM authorize WHERE guild_id = $1", guild_id):
            return await ctx.warn("This guild is **already** authorized")

        await self.bot.db.execute(
            """
            INSERT INTO authorize
            VALUES ($1, $2, $3, $4)
            """,
            guild_id,
            ctx.author.id,
            None,
            2,
        )

        await ctx.approve(f"{ctx.author.mention} Successfully **authorized** to function in GID: `{guild_id}`")
        print(f"Authorized guild: {guild_id}")

    @commands.command(name="unauth")
    @auth_perms()
    async def unauth_guild(self, ctx: Context, guild_id: int):
        """
        Unauthorize a guild
        """
        check = await self.bot.db.fetchrow("SELECT * FROM authorize WHERE guild_id = $1", guild_id)
        if not check:
            return await ctx.warn("This guild is **not** authorized")

        await self.bot.db.execute(
            "DELETE FROM authorize WHERE guild_id = $1",
            guild_id,
        )

        guild = self.bot.get_guild(guild_id)
        if guild:
            await self.guild_change("removed", guild)
            await guild.leave()

        await ctx.approve(f"{ctx.author.mention} Successfully **unauthorized** from functioning in GID: `{guild_id}`")
        print(f"Unauthorized guild: {guild_id}")

    @commands.command(name="authcurrent")
    @auth_perms()
    async def auth_current_guilds(self, ctx: Context):
        """
        Authorize all current guilds
        """
        for guild in self.bot.guilds:
            check = await self.bot.db.fetchrow("SELECT * FROM authorize WHERE guild_id = $1", guild.id)
            if not check:
                await self.bot.db.execute(
                    """
                    INSERT INTO authorize
                    VALUES ($1, $2, $3, $4)
                    """,
                    guild.id,
                    ctx.author.id,
                    None,
                    2,
                )
                await ctx.warn(f"Successfully **authorized** to function in GID: `{guild.id}`")
                await ctx.warn(f"Authorized guild: {guild.id}")
            else:
                await ctx.warn(f"Guild {guild.id} is already authorized")

async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(Auth(bot))