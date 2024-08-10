from discord.ext import commands
from discord.ui import Select, View, Modal, TextInput
import discord
import datetime
import pytz
import logging
from tools.paginator import Paginator
from .Classes import Colors, Emojis
from .Interactions import CustomInteraction

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PageNumberModal(Modal):
    def __init__(self, help_view):
        super().__init__(title="Enter Page Number")
        self.help_view = help_view



class HelpSelect(Select):
    def __init__(self, placeholder: str, options: list, commands: dict, help_view: View):
        super().__init__(placeholder=placeholder, options=options)
        self.commands = commands
        self.help_view = help_view

    async def callback(self, interaction: discord.Interaction):
        cog_name = self.values[0]
        self.help_view.page = list(self.commands.keys()).index(cog_name) + 1  # Adjust for the main help menu page
        await self.help_view.update_embed(interaction)

class HelpView(View):
    def __init__(self, commands, author):
        super().__init__(timeout=60)  # Set the timeout to 60 seconds
        self.commands = commands
        self.author = author
        self.page = 1
        self.max_page = len(commands)
        self.message = None

        options = [
            discord.SelectOption(
                label=cog,
                description="Click to see commands in this category",
                value=cog
            )
            for cog in commands if cog != "No Category"
        ]
        self.add_item(HelpSelect(placeholder="choose a category", options=options, commands=commands, help_view=self))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        custom_interaction = CustomInteraction(interaction)
        if interaction.user != self.author:
            await custom_interaction.error("You are not authorized to use this **Interaction**.")
            return False
        return True

    async def update_embed(self, interaction: discord.Interaction):
        try:
            cog_name = list(self.commands.keys())[self.page - 1]
            commands_list = self.commands[cog_name]
            command_names = ", ".join([f"{command.name}*" if isinstance(command, commands.Group) else command.name for command in commands_list])
            embed = discord.Embed(
                title=f"Category: {cog_name}",
                description=f"```{command_names}```",
                color=Colors.oxy
            )
            embed.set_author(name="Command Menu", icon_url=interaction.client.user.avatar.url)
            embed.set_footer(text=f"{len(commands_list)} commands • Requested by {self.author}")
    
            if interaction.response.is_done():
                await interaction.edit_original_response(content=None, embed=embed, view=self)
            else:
                await interaction.response.edit_message(content=None, embed=embed, view=self)
            
            if self.message is None:
                self.message = await interaction.original_response()
        except Exception as e:
            logger.error(f"Failed to update embed: {e}")
            await interaction.response.send_message("An error occurred while updating the embed.", ephemeral=True)
    
class Help(commands.MinimalHelpCommand):

    context: "context"

    def __init__(self, **options):
        super().__init__(
            command_attrs={
                "help": "Shows help about the bot, a command, or a category of commands.",
                "aliases": ["h"],
            },
            **options,
        )

    async def send_bot_help(self, mapping):
        commands_by_cog = {}
        for cog, commands in mapping.items():
            if cog and cog.qualified_name in ["Owner", "Developer", "Jishaku", "Events", "Auth"]:
                continue
            # Remove the filtering step to include all commands
            filtered = commands  # No filtering
            if filtered:
                cog_name = getattr(cog, "qualified_name", None)
                if cog_name:
                    commands_by_cog[cog_name] = filtered

        view = HelpView(commands_by_cog, self.context.author)
        prefix = self.context.clean_prefix
        embed = discord.Embed(
            description="**Information**\n"
                        "> **[]** = optional, **<>** = required\n"
                        "> Sub commands are indicated by an asterisk(*) next to it.\n\n"
                        "**Useful Links:**\n"
                        "**[Support](https://discord.gg/NndU7KMH)** • "
                        "**[Invite](https://discord.com/oauth2/authorize?client_id=1256758107753676892&permissions=8&integration_type=0&scope=bot)**",
            color=Colors.oxy
        )
        embed.set_author(name="command menu", icon_url=self.context.bot.user.avatar.url)
        
        # Get the number of commands in the first category
        first_cog_name = list(commands_by_cog.keys())[0] if commands_by_cog else "No Category"
        num_commands = len(commands_by_cog[first_cog_name]) if first_cog_name in commands_by_cog else 0
        embed.set_footer(text=f"Select a category from the dropdown menu below")

        view.message = await self.context.reply(embed=embed, view=view)

    async def send_command_help(self, command):
        command_syntax = getattr(command, 'usage', f"{self.context.clean_prefix}{command.name} {command.signature}")
        command_example = command.extras.get('example', 'No example provided')
        formatted_example = f"{self.context.clean_prefix}{command_example}"

        # Ensure permissions are properly formatted
        permissions = ', '.join(command.brief) if isinstance(command.brief, (list, set)) else command.brief  # Convert list/set to string

        embed = discord.Embed(
            title=f"{command.name.capitalize()} • {command.cog_name} module",
            color=Colors.oxy
        )
        embed.add_field(
            name=f"{command.help or 'No description provided.'}", 
            value=f"```css\nSyntax: {command_syntax}\nExample: {formatted_example}\n```",  # Combine 'yaml' and 'css' without extra newlines
            inline=False
        )
        embed.add_field(
            name="Permissions", 
            value=permissions if permissions else 'None', 
            inline=False
        )  # Adjust permissions as needed
        embed.set_footer(
            text=f"Aliases: {', '.join(command.aliases) if command.aliases else 'None'}",
            icon_url=self.context.author.avatar.url
        )
        await self.context.reply(embed=embed)



    async def send_group_help(self, group):
        # Dictionary mapping module names to emojis
        # Get the emoji for the group's module, default to a generic emoji if not found
    
        # Create pages for the paginator
        pages = []
        commands = list(group.commands)  # Convert the set to a list
        for i, cmd in enumerate(commands):
            command_syntax = getattr(cmd, 'usage', f"{self.context.clean_prefix}{cmd.name} {cmd.signature}")
            command_example = cmd.extras.get('example', 'No example provided')
            formatted_example = f"{self.context.clean_prefix}{command_example}"
            
            embed = discord.Embed(
                title=f"{group.name.capitalize()} {cmd.name.capitalize()} • {group.cog_name} module",
                color=Colors.oxy
            )
            embed.add_field(name=f"{cmd.help or 'No description provided.'}", value=f"```css\nSyntax: {command_syntax}\nExample: {formatted_example}\n```", inline=False)
            permissions = ', '.join(cmd.brief) if isinstance(cmd.brief, (list, set)) else cmd.brief  # Convert list/set to string
            embed.add_field(name="Permissions", value=permissions if permissions else 'None', inline=False)  # Adjust permissions as needed
            embed.set_footer(text=f"Aliases: {', '.join(cmd.aliases) if cmd.aliases else 'None'} • Page {i + 1} of {len(commands)}", icon_url=self.context.author.avatar.url)
            pages.append(embed)
    
        # Initialize and start the paginator
        paginator = Paginator(ctx=self.context, pages=pages)
        await paginator.start()
    
def setup(bot):
    bot.help_command = Help()
