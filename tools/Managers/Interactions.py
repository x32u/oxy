from discord import Embed, Interaction

from .Classes import Emojis, Colors as colors



class CustomInteraction:

    def __init__(self, interaction: Interaction):

        self.interaction = interaction


    async def error(self, message: str, ephemeral: bool = True) -> None:  # Changed default to True
        await self.interaction.response.send_message(
            embed=Embed(color=colors.red, description=f"{Emojis.deny} {self.interaction.user.mention}: {message}"), 
            ephemeral=ephemeral
        )

    async def warn(self, message: str, ephemeral: bool = True) -> None:  # Changed default to True
        await self.interaction.response.send_message(
            embed=Embed(color=colors.yellow, description=f"{Emojis.warning} {self.interaction.user.mention}: {message}"), 
            ephemeral=ephemeral
        )

    async def approve(self, message: str, ephemeral: bool = True) -> None:  # Changed default to True
        await self.interaction.response.send_message(
            embed=Embed(color=colors.green, description=f"{Emojis.approve} {self.interaction.user.mention}: {message}"), 
            ephemeral=ephemeral
        )
