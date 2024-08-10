from discord import ButtonStyle, Embed, Interaction, Message, HTTPException
from discord.ext.commands import Context as DefaultContext
from discord.ui import Button, View, Modal, TextInput
from asyncio import TimeoutError
from contextlib import suppress
from typing import Union
from discord.ext import commands
import discord
from tools.Managers.Interactions import CustomInteraction
from tools.Managers.Classes import Colors

# Define emojis for navigation
class emoji:
    next = "<:right:1238691443900682322>"
    previous = "<:left:1238691473113874482>"
    cancel = "<:pageclose:1242674549514829916>"
    navigate = "<:navigate2:1242676587862822985>"


class EmbedBuilder:
    def ordinal(self, num: int) -> str:
        """Convert from number to ordinal (10 - 10th)"""
        numb = str(num)
        if numb.startswith("0"):
            numb = numb.strip('0')
        if numb in ["11", "12", "13"]:
            return numb + "th"
        if numb.endswith("1"):
            return numb + "st"
        elif numb.endswith("2"):
            return numb + "nd"
        elif numb.endswith("3"):
            return numb + "rd"
        else:
            return numb + "th"

    
class EmbedScript(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str):
        x = await EmbedBuilder.to_object(EmbedBuilder.embed_replacement(ctx.author, argument))
        if x[0] or x[1]:
            return {"content": x[0], "embed": x[1], "view": x[2]}
        return {"content": EmbedBuilder.embed_replacement(ctx.author, argument)}


class GoToModal(Modal, title="Change the Page"):
    page = TextInput(label="Page", placeholder="Enter page number", max_length=3)

    def __init__(self, embeds):
        super().__init__()
        self.embeds = embeds

    async def on_submit(self, interaction: Interaction) -> None:
        custom_interaction = CustomInteraction(interaction)
        try:
            page_number = int(self.page.value)
            if page_number > len(self.embeds) or page_number < 1:
                return await custom_interaction.warn(f"You can only select a page **between** 1 and {len(self.embeds)}", ephemeral=True)
            await interaction.response.edit_message(embed=self.embeds[page_number - 1])
        except ValueError:
            await custom_interaction.warn("Please enter a valid page number.", ephemeral=True)

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        custom_interaction = CustomInteraction(interaction)
        await custom_interaction.warn("Unable to change the page", ephemeral=True)


# Paginator Button Class
class PaginatorButton(Button):
    def __init__(self, emoji: str, style: ButtonStyle, paginator: 'Paginator'):
        super().__init__(emoji=emoji, style=style, custom_id=emoji)
        self.paginator = paginator

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.defer()

        if self.custom_id == emoji.previous:
            self.paginator.current_page = (self.paginator.current_page - 1) % len(self.paginator.pages)
        elif self.custom_id == emoji.next:
            self.paginator.current_page = (self.paginator.current_page + 1) % len(self.paginator.pages)
        elif self.custom_id == emoji.navigate:
            modal = GoToModal(self.paginator.pages)
            await interaction.response.send_modal(modal)
            await modal.wait()
            try:
                self.paginator.current_page = int(modal.page.value) - 1
            except ValueError:
                return
        elif self.custom_id == emoji.cancel:
            with suppress(HTTPException):
                await self.paginator.message.delete()
            return

        page = self.paginator.pages[self.paginator.current_page]
        if isinstance(page, Embed):
            await self.paginator.message.edit(embed=page, view=self.paginator)
        else:
            await self.paginator.message.edit(content=page, view=self.paginator)


# Paginator Class
class Paginator(View):
    def __init__(self, ctx: DefaultContext, pages: list[Union[Embed, str]]) -> None:
        super().__init__(timeout=30)  # Changed timeout to 20 seconds
        self.ctx = ctx
        self.pages = pages
        self.current_page = 0
        self.message = None
        self.add_initial_buttons()
        self.color = Colors.oxy

    def add_initial_buttons(self):
        self.add_item(PaginatorButton(emoji=emoji.previous, style=ButtonStyle.blurple, paginator=self))
        self.add_item(PaginatorButton(emoji=emoji.next, style=ButtonStyle.blurple, paginator=self))
        self.add_item(PaginatorButton(emoji=emoji.navigate, style=ButtonStyle.grey, paginator=self))
        self.add_item(PaginatorButton(emoji=emoji.cancel, style=ButtonStyle.red, paginator=self))

    @property
    def type(self) -> str:
        return "embed" if isinstance(self.pages[0], Embed) else "text"

    async def send(self, content: Union[Embed, str], **kwargs) -> Message:
        if self.type == "embed":
            return await self.ctx.reply(embed=content, **kwargs)
        else:
            return await self.ctx.reply(content=content, **kwargs)

    async def interaction_check(self, interaction: Interaction) -> bool:
        custom_interaction = CustomInteraction(interaction)
        if interaction.user != self.ctx.author:
            await custom_interaction.error("You are not authorized to use this **Interaction**.")
            return False
        return True

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=None)
            except discord.NotFound:
                # The message was deleted, so there's nothing to edit
                pass
            except Exception as e:
                # Log any other exceptions for debugging
                print(f"An error occurred in Paginator.on_timeout: {e}")

    async def start(self) -> Message:
        if len(self.pages) == 1:
            self.message = await self.send(self.pages[0])
        else:
            self.message = await self.send(self.pages[self.current_page], view=self)