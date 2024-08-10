import asyncio
import aiohttp
import asyncpg
import os

from discord.ext import commands
from dotenv import load_dotenv
from tools.Managers.Classes import Colors, Emojis







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


load_dotenv()

class Lastfm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lastfm_api_key = os.getenv('LASTFM_API_KEY')
        self.base_url = 'http://ws.audioscrobbler.com/2.0/'
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    async def fetch_lastfm_data(self, params):
        if not self.lastfm_api_key:
            raise ValueError("Last.fm API key is not set.")

        async with self.session.get(self.base_url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None

    @group(name='lastfm', aliases=['lf'], invoke_without_command=True)
    async def lastfm(self, ctx):
        """
        Main commands for Last.fm.
        """
        await ctx.send_help(ctx.command)

    @lastfm.command(
            name='set',
            description="Set your Last.fm username.",
            usage="lf set <username>",
            aliases=['s']
    )
    async def set(self, ctx, username: str):
        """
        Set your Last.fm username.
        """
        async with self.bot.db.acquire() as conn:
            await conn.execute('''
                INSERT INTO lastfm_usernames (user_id, username)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE SET username = $2
            ''', ctx.author.id, username)
        await ctx.approve(f"Set your Last.fm username to `{username}`.", reference=ctx.message)

    @command(name='np')
    async def nowplaying(self, ctx, member: Member = None):
        """
        Shows the current track you're listening to.
        """
        member = member or ctx.author
        async with self.bot.db.acquire() as conn:
            result = await conn.fetchrow('''
                SELECT username FROM lastfm_usernames WHERE user_id = $1
            ''', member.id)
        
        if not result:
            await ctx.lastfm(f"{ctx.author.mention} You need to login to last.fm to use this command. Use\n `lf set <username>` to set your username.", reference=ctx.message)
            return
        
        username = result['username']
        params = {
            'method': 'user.getrecenttracks',
            'user': username,
            'api_key': self.lastfm_api_key,
            'format': 'json',
            'limit': 1
        }
    
        data = await self.fetch_lastfm_data(params)
        if not data or 'recenttracks' not in data or 'track' not in data['recenttracks']:
            await ctx.error("Couldn't retrieve the current track.")
            return
        
        track = data['recenttracks']['track'][0]
        track_name = track['name']
        artist_name = track['artist']['#text']
        artist_url = f"https://www.last.fm/music/{artist_name.replace(' ', '+')}"
        album_name = track['album']['#text'] if 'album' in track else "Unknown Album"
        track_url = track['url']
        album_art_url = track['image'][-1]['#text'] if 'image' in track and track['image'] else None

        user_params = {
            'method': 'user.getinfo',
            'user': username,
            'api_key': self.lastfm_api_key,
            'format': 'json'
        }
        track_params = {
            'method': 'track.getInfo',
            'api_key': self.lastfm_api_key,
            'artist': artist_name,
            'track': track_name,
            'username': username,
            'format': 'json'
        }

        user_data, track_data = await asyncio.gather(
            self.fetch_lastfm_data(user_params),
            self.fetch_lastfm_data(track_params)
        )

        if not user_data or 'user' not in user_data:
            await ctx.error("Couldn't retrieve user info.")
            return
        
        total_play_count = user_data['user'].get('playcount', 'N/A')
        lastfm_username = user_data['user'].get('name', username)

        if not track_data or 'track' not in track_data:
            await ctx.error("Couldn't retrieve track info.")
            return
        
        track_play_count = track_data['track'].get('userplaycount', 'N/A')
    
        embed = Embed(
            title=f"{lastfm_username}",
            color=0xd72228
        )
        embed.add_field(name="Track", value=f"[{track_name}]({track_url})", inline=True)
        embed.add_field(name="Artist", value=f"[{artist_name}]({artist_url})", inline=True)
        
        if album_art_url:
            embed.set_thumbnail(url=album_art_url)
        
        embed.set_footer(
            text=f"Plays: {track_play_count} ∙ Scrobbles: {total_play_count} ∙ Album: {album_name}",
            icon_url=self.bot.user.avatar.url
        )
        
        message = await ctx.reply(embed=embed)
        await message.add_reaction('👍')
        await message.add_reaction('👎')

async def setup(bot):
    await bot.add_cog(Lastfm(bot))
