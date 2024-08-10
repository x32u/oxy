from .Classes import Emojis
from discord import Embed, Message
from discord.ext.commands import Context as BaseContext
from .Classes import Colors as colors
from typing import List, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from tools.oxy import oxy

class CustomContext(BaseContext):
    bot: "oxy"

    async def send(self: "CustomContext", *args, **kwargs) -> Message:
        embeds: List[Embed] = kwargs.get("embeds", [])
        if embed := kwargs.get("embed"):
            embeds.append(embed)

        for embed in embeds:
            self.style(embed)

        if patch := kwargs.pop("patch", None):
            kwargs.pop("reference", None)

            if args:
                kwargs["content"] = args[0]

            self.response = await patch.edit(**kwargs)
        else:
            self.response = await super().send(*args, **kwargs)

        return self.response

    async def neutral(
        self: "CustomContext", 
        value: str, 
        color: int = colors.white, 
        reference: Optional[Message] = None,  # Add a parameter to pass the message to reply to
        **kwargs
    ) -> Message:
        return await self.send(
            embed=Embed(
                color=color,
                description=f"" + value if not "" in value else value,
            ),
            reference=reference,  # Pass the reference to the send method
            **kwargs,
        )

    async def utility(
        self: "CustomContext", 
        value: str, 
        color: int = colors.white, 
        reference: Optional[Message] = None,  # Add a parameter to pass the message to reply to
        **kwargs
    ) -> Message:
        return await self.send(
            embed=Embed(
                color=color,
                description=f"" + value if not "" in value else value,
            ),
            reference=reference,  # Pass the reference to the send method
            **kwargs,
        )

    async def approve(
        self: "CustomContext", 
        value: str, 
        reference: Optional[Message] = None,  # Add a parameter to pass the message to reply to
        **kwargs
    ) -> Message:
        # Always prepend the emoji and ensure it's formatted correctly
        description = f"{Emojis.approve} {value}" if not value.startswith(f"{Emojis.approve} ") else value
        return await self.send(
            embed=Embed(
                color=colors.green,
                description=description,
            ),
            reference=reference,  # Pass the reference to the send method
            **kwargs,
        )

    async def warn(
        self: "CustomContext", 
        value: str, 
        reference: Optional[Message] = None,  # Add a parameter to pass the message to reply to
        **kwargs
    ) -> Message:
        # Always prepend the emoji and ensure it's formatted correctly
        description = f"{Emojis.warning} {value}" if not value.startswith(f"{Emojis.warning} ") else value
        return await self.send(
            embed=Embed(
                color=colors.yellow,
                description=description,
            ),
            reference=reference,  # Pass the reference to the send method
            **kwargs,
        )

    async def error(
        self: "CustomContext", 
        value: str, 
        reference: Optional[Message] = None,  # Add a parameter to pass the message to reply to
        **kwargs
    ) -> Message:
        # Always prepend the emoji and ensure it's formatted correctly
        description = f"{Emojis.deny} {value}" if not value.startswith(f"{Emojis.deny} ") else value
        return await self.send(
            embed=Embed(
                color=colors.red,
                description=description,
            ),
            reference=reference,  # Pass the reference to the send method
            **kwargs,
        )

    async def cooldown(
        self: "CustomContext", 
        value: str, 
        **kwargs
    ) -> Message:
        # Always prepend the emoji and ensure it's formatted correctly
        description = f"{Emojis.cooldown} {value}" if not value.startswith(f"{Emojis.cooldown} ") else value
        return await self.send(
            embed=Embed(
                color=colors.yellow,
                description=description,
            ),
            **kwargs,
        )

    async def lastfm(
        self: "CustomContext", 
        value: str, 
        **kwargs
    ) -> Message:
        # Always prepend the emoji and ensure it's formatted correctly
        description = f"{Emojis.lastfm} {value}" if not value.startswith(f"{Emojis.lastfm} ") else value
        return await self.send(
            embed=Embed(
                color=0xd72228,
                description=description,
            ),
            **kwargs,
        )



    def style(self, embed: Embed) -> Embed:
        if not embed.color:
            embed.color = 0xFFFFFF  # ffffff  #2b2d31 old Color Hex
        return embed

