from contextlib import suppress
import asyncio
import datetime

import discord
from discord.ext import commands, tasks # maybe adding that every 10 seconds the queue embed will be updated

import pomice

from ..errorHandler import print_timestamp

def convert(t):
    return str(datetime.timedelta(seconds=t))

class Player(pomice.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.queue = pomice.Queue()
        self.controller: discord.Message = None
        self.context: commands.Context = None
        self.queue_controller: discord.Message = None
        self.queue_context: commands.Context = None
        self.current_track = None
        self.playback_start_time = None

    async def do_next(self, bot) -> None:
        if self.controller:
            with suppress(discord.HTTPException):
                await self.controller.delete()
        try:
            track: pomice.Track = self.queue.get()
        except pomice.QueueEmpty:
            await bot.change_presence(activity=None)
            return print_timestamp('Played every song in the queue.')

        self.current_track = track
        self.playback_start_time = asyncio.get_event_loop().time()

        await self.play(track)
        print_timestamp(track.title, f'Now Playing: ', 3, track.uri)

        embed = discord.Embed(
            title = f'Now playing',
            description = f'[{track.title}]({track.uri}) - [{track.author}]',
            image = track.thumbnail,
            colour = 0x00f6ff,
        )
        embed.set_footer(text=f'Requested by {self.context.author.name}')
        self.controller = await self.context.send(embed=embed)
        await bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=track.title)
        )

    async def teardown(self):
        with suppress((discord.HTTPException), (KeyError)):
            await self.destroy()
            if self.controller:
                await self.controller.delete()

    async def set_context(self, ctx: commands.Context):
        self.context = ctx

    async def set_queue_context(self, q_ctx: commands.Context):
        self.queue_context = q_ctx

    def get_current_playback_position(self):
        if self.current_track and self.playback_start_time:
            current_time = asyncio.get_event_loop().time()
            return current_time - self.playback_start_time
        return 0

    async def queue_update(self, player):
        if self.queue_controller:
            with suppress(discord.HTTPException):
                await self.queue_controller.delete()
        
        if (not pomice.QueueEmpty or player.current) and (self.queue_context):
            current_track: pomice.Track = player.current
            q = player.queue.get_queue()

            formatted_current_track = f'[{current_track.title}]({current_track.uri}) [{convert(round(player.get_current_playback_position()))} / {convert(current_track.length // 1000)}]'
            formatted_queue = '\n'.join([f'{i+1}. [{track.title}]({track.uri}) [{convert(track.length // 1000)}]' for i, track in enumerate(q)])

            embed = discord.Embed(
                title=f'Queue',
                description=f'**Current Track:**\n{formatted_current_track}\n\n**Next Tracks:**\n{formatted_queue}',
                colour=0xa3425d,
            )
            self.queue_controller = await self.queue_context.followup.send(embed=embed)