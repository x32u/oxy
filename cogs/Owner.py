import time
import logging
from tools.oxy import oxy
from tools.Managers import Context
from tools.Managers.Classes import Emojis
from tools.paginator import Paginator
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from aiohttp import ClientSession



log = logging.getLogger(__name__)



from discord.ext.commands import (
    Cog, 
    command,  
    cooldown, 
    BucketType, 
    is_owner,
)

from discord import (
    Embed,
    HTTPException,
    Forbidden
)

class Developer(Cog):
    def __init__(self, bot):
        self.bot: oxy = bot
        self.db = None


    async def cog_check(self, ctx):
        # Check if the author of the command is the bot owner
        return await self.bot.is_owner(ctx.author)
    

    @command(name="restart", aliases=['rs'], description="Restarts the bot")
    async def restart(self, ctx: Context):
        try:
            # Use jishaku to run the pm2 command and capture the output
            prefix = (await self.bot.get_prefix(ctx.message))[0]  # Get the command prefix
            command_string = f"{prefix}jsk sh pm2 restart oxy"
            new_message = ctx.message
            new_message.content = command_string
            new_ctx = await self.bot.get_Context(new_message)

            # Capture the output of the command
            f = StringIO()
            with redirect_stdout(f), redirect_stderr(f):
                await self.bot.invoke(new_ctx)
            output = f.getvalue()

            # Send the captured output as a message
            formatted_output = f"```\n{output}\n```"
            await ctx.send(formatted_output)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
            log.error(f"An error occurred during restart: {str(e)}")
    
    @command(
        name="commands",
        aliases=["cmds", "allcommands"],
    )
    @cooldown(1, 2, BucketType.user)
    @is_owner()
    async def list_commands(self, ctx: Context):
        """
        Lists all commands available in the bot.
        """
        commands = []
        for cog in self.bot.cogs.values():
            commands.extend(cog.get_commands())
        commands = sorted(commands, key=lambda cmd: cmd.name)
        
        if not commands:
            await ctx.warn(f"{ctx.author.mention}: No commands found.")
            return

        # Create pages for the paginator
        pages = []
        per_page = 10
        for i in range(0, len(commands), per_page):
            chunk = commands[i:i + per_page]
            command_list = "\n".join(f"`{i+1:02}` {cmd.name}" for i, cmd in enumerate(chunk, start=i))
            embed = Embed(title="Available Commands", description=command_list)
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
            embed.set_footer(text=f"Page {i//per_page + 1}/{(len(commands) + per_page - 1) // per_page} ({len(commands)} commands)", icon_url=self.bot.user.avatar.url)
            pages.append(embed)

        # Initialize and start the paginator
        paginator = Paginator(ctx, pages)
        await paginator.start()


    @command(name="reload", aliases=['rl'], description="Reload all functions")
    async def reload(self, ctx: Context):
        reloaded = []
        
        # Loop through all loaded extensions (cogs)
        for extension_name in list(self.bot.extensions):
            try:
                await self.bot.reload_extension(extension_name)  # Correctly await the coroutine
                reloaded.append(extension_name)
            except Exception as e:
                # Log the error for debugging purposes
                print(f"Failed to reload {extension_name}: {e}")
                await ctx.warn(f"Failed to reload `{extension_name}`!")
        
        await ctx.approve(f"Successfully reloaded `{len(reloaded)}` features!", reference=ctx.message)



    @command(name="sync", aliases=['slash'], description="Sync slash commands with Discord")
    async def sync(self: "Developer", ctx: Context):
        await self.bot.tree.sync()
        await ctx.reply("Slash commands have been synchronized with Discord.")


    @command(name="restart", aliases=['rs'], description="Restarts the bot")
    async def restart(self, ctx):
        try:
            # Get the command prefix
            prefix = (await self.bot.get_prefix(ctx.message))[0]
    
            # Construct the command string for jishaku
            command_string = f"{prefix}jsk sh pm2 restart oxy"
    
            # Create a new message object with the command
            new_message = ctx.message
            new_message.content = command_string
    
            # Create a new context to invoke the command
            new_ctx = await self.bot.get_context(new_message)
    
            # Capture the output of the command
            f = StringIO()
            with redirect_stdout(f), redirect_stderr(f):
                await self.bot.invoke(new_ctx)
            output = f.getvalue()
    
            # Send the captured output as a message
            formatted_output = f"```\n{output}\n```"
            await ctx.send(formatted_output)
    
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
            log.error(f"An error occurred during restart: {str(e)}")

    @command(name="globalban", aliases=['gban'], description="Bans a user globally from all guilds the bot is in")
    async def globalban(self: "Developer", ctx: Context, user_id: int):
        user = await self.bot.fetch_user(user_id)
        if not user:
            return await ctx.send("User not found.")

        banned_guilds = 0
        for guild in self.bot.guilds:
            if guild.me.guild_permissions.ban_members:
                try:
                    await guild.ban(user, reason="Global ban executed.")
                    banned_guilds += 1
                except Forbidden:
                    await ctx.send(f"Failed to ban in {guild.name} (insufficient permissions).")
                except HTTPException:
                    await ctx.send(f"Failed to ban in {guild.name} (HTTP error).")

        await ctx.send(f"User {user} has been banned from {banned_guilds} guilds.")

    @command(name="botavatar", aliases=['ba', 'setpfp', 'botpfp'], description="Sets bot's profile picture")
    async def botavatar(self: "Developer", ctx: Context, image: str = None):
        if not image:
            image = ctx.message.attachments[0].url

        async with ClientSession() as session:
            async with session.get(image) as response:
                if response.status != 200:
                    raise ValueError("Image unreadable.")

                img = await response.read()

        await self.bot.user.edit(avatar=img)

        embed = Embed(description=f"{self.bot.user.name} Avatar changed to")
        embed.set_image(url=image)
        await ctx.reply(embed=embed)

    @command(name="botname", aliases=["bn", "changename"], description="Changes bot's name")
    async def botname(self: "Developer", ctx: Context, new_name: str):
        await ctx.guild.me.edit(nick=new_name)
        await ctx.approve(f"Changed my display name to `{new_name}`")

    #@command(name="selfpurge", aliases=["self", "clean"], description="Self purges the owner's messages")
    #async def selfpurge(self: "Developer", ctx: Context, limit: int = 100):
    #    deleted = await ctx.message.channel.purge(limit=limit, check=lambda msg: msg.author == ctx.author)
    #    m = await ctx.approve(f"> Deleted `{len(deleted)}` messages from {ctx.author.mention}.")
    #    time.sleep(0.2)
    #    await m.delete()

    @command(name="eval", aliases=['evaluate', 'ev'], description="Evaluates code")
    async def eval(self: "Developer", ctx: Context, code: str):
        await ctx.reply(f"```{eval(code)}```")

    @command(name="exec", aliases=['ex'], description="Executes code")
    async def exec(self: "Developer", ctx: Context, code: str):
        await ctx.reply(f"```{exec(code)}```")

    @command(name="shutdown", aliases=['sd'], description="Shuts down the bot")
    async def shutdown(self: "Developer", ctx: Context):
        await ctx.reply(f"```{self.bot.logout()}```")


    @command(name="leave", aliases=['lv'], description="Leaves the guild")
    async def leave(self: "Developer", ctx: Context):
        await ctx.guild.leave()
        await ctx.approve("Successfully left the guild")

    @command(name="join", aliases=['jn'], description="Generates an invite link for the bot")
    async def join(self: "Developer", ctx: Context):
        try:
            invite_link = f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot"
            await ctx.send(f"Use this link to invite the bot to a server: {invite_link}")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
    
    @command(name="guilds", aliases=['gs'], description="Lists guilds")
    async def guilds(self: "Developer", ctx: Context):
        guilds = self.bot.guilds
        if not guilds:
            await ctx.send("No guilds found.")
            return
        pages = []
        per_page = 10
        for i in range(0, len(guilds), per_page):
            chunk = guilds[i:i + per_page]
            guild_list = "\n".join(f"{Emojis.separator_curved} `#{i+1:02}` {guild.name} ( `{guild.id}` )" for i, guild in enumerate(chunk, start=i))
            embed = Embed(title="Guilds", description=guild_list, color=0x2B2D31)
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
            embed.set_footer(text=f"Page {i//per_page + 1}/{(len(guilds) + per_page - 1) // per_page} ({len(guilds)} guilds)", icon_url=self.bot.user.avatar.url)
            pages.append(embed)
        paginator = Paginator(ctx, pages)
        await paginator.start()





    @command(name="sync", aliases=['slash'], description="Sync slash commands with Discord")
    async def sync(self: "Developer", ctx: Context):
        await self.bot.tree.sync()
        await ctx.reply("Slash commands have been synchronized with Discord.")


        




    @command(name="getinvite", aliases=['gi'], description="Generates an invite link for a specific guild by ID")
    async def getinvite(self: "Developer", ctx: Context, guild_id: int):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return await ctx.send("Guild not found.")
    
        # Check if the bot has the necessary permissions to create an invite
        if not guild.me.guild_permissions.create_instant_invite:
            return await ctx.send("I do not have permissions to create invites in this guild.")
    
        # Try to create an invite from the first available channel
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).create_instant_invite:
                invite = await channel.create_invite(max_age=3600, reason=f"Requested by {ctx.author}")
                return await ctx.send(f"Here is an invite link: {invite.url}")
    
        await ctx.send("No suitable channel found to create an invite.")











async def setup(bot):
    await bot.add_cog(Developer(bot))