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
        try:
            track: pomice.Track = self.queue.get()
        except pomice.QueueEmpty:
            await bot.change_presence(activity=discord.Activity(
                type=discord.ActivityType.playing,
                name=f'Server-status: {self.bot.mcstatus}')
            )
            if self.controller:
                with suppress(discord.HTTPException):
                    await self.controller.delete()
                    self.controller: discord.Message = None

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

        if self.controller:
            await self.controller.edit(embed=embed)
        else:
            self.controller = await self.context.send(embed=embed)


        await bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.playing,
            name=f'{track.title}')
        )
            
    async def teardown(self):
        with suppress((discord.HTTPException), (KeyError)):
            try:
                await self.destroy()
                if self.controller:
                    await self.controller.delete()
                if self.queue_controller:
                    await self.queue_controller.delete()
                print_timestamp('Destoryed the bot successfully')
            except Exception as e:
                print_timestamp(e, 'Error while trying to destroy the bot: ', 1)


    async def set_context(self, ctx: commands.Context):
        self.context = ctx

    async def set_queue_context(self, q_ctx: commands.Context):
        self.queue_context = q_ctx

    def get_current_playback_position(self):
        if self.current_track and self.playback_start_time:
            current_time = asyncio.get_event_loop().time()
            return current_time - self.playback_start_time
        return 0

    async def queue_update(self):
        if self.current and self.queue_context:
            current_track: pomice.Track = self.current
            q = self.queue.get_queue()

            print(f"Current Track: {current_track.title}")
            print(f"Queue: {q}")

            formatted_current_track = f'[**{current_track.title}**]({current_track.uri}) [{convert(round(self.get_current_playback_position()))} / {convert(current_track.length // 1000)}]'
            loop_mode = 'Disabled' if self.queue.loop_mode is None else self.queue.loop_mode

            rearranged_queue = q

            if self.queue.loop_mode is not None:    
                if self.queue.loop_mode.name == 'QUEUE':
                    current_track_index = next((i for i, track in enumerate(q) if track == current_track), -1)
                    
                    print(f"Current Track Index: {current_track_index}")
                    
                    if current_track_index!= -1:
                        before_current = q[:current_track_index]
                        after_current = q[current_track_index:]

                        rearranged_queue = after_current + before_current

                        print(f"Rearranged Queue: {rearranged_queue}")

            if self.queue.loop_mode is not None:
                loop_mode_check = self.queue.loop_mode.name
            else:
                loop_mode_check = None

            if loop_mode_check == 'QUEUE':
                start = 1
                loop_mode_adjustment = 0
            else:
                start = 0
                loop_mode_adjustment = 1

            end = len(self.queue)

            formatted_queue = ''
            for i, track in enumerate(rearranged_queue[start:end], start=start):
                try:
                    formatted_queue += (f'{i + loop_mode_adjustment}. [**{track.title}**]({track.uri}) [{convert(track.length // 1000)}]\n')
                except Exception as e:
                    print(f"Error converting length for song {song.title}: {e}")

            embed = discord.Embed(
                title=f'Queue',
                description=f'**Current Track:**\n{formatted_current_track}\n\n**Next Tracks:**\n{formatted_queue}\n\nloop mode: {loop_mode}',
                colour=0xa3425d,
            )

            if self.queue_controller:
                await self.queue_controller.edit(embed=embed)
                return await self.queue_context.respond(            
                    'Queue updated',
                    delete_after=2,
                )
            else:
                self.queue_controller = await self.queue_context.respond(embed=embed)
        else:
            if self.queue_controller:
                with suppress(discord.HTTPException):
                    await self.queue_controller.delete()
                    self.queue_controller: discord.Message = None
