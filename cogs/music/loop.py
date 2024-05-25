import discord
from discord.ext import commands
from discord.commands import Option

import pomice
from pomice import LoopMode

from ..errorHandler import print_timestamp
from .player import Player

loop_mode = 0

class Loop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = pomice.Queue()

    @commands.slash_command(
        name='loop',
        description='Control the loop mode.',
        options=[
            Option(
                name='mode',
                description='Loop mode',
                type=3,
                choices=[
                    'disable',
                    'track',
                    'queue',
                    '?'
                ]
            )
        ]
    )
    async def loop(self, ctx, mode: str) -> None:
        print_timestamp(ctx.author.name, 'Requested loop command by: ')
        await ctx.defer()
        if not (player := ctx.voice_client):
            await ctx.respond('Queue is empty', delete_after=5,)
        else:
            player: Player = ctx.voice_client

            print_timestamp(mode, 'Provided mode: ')

            if mode.lower() == 'disable':
                player.queue.disable_loop()
                await ctx.respond('Looping is now `disabled`.', delete_after=5,)
                await player.queue_update()
            elif mode.lower() == 'track':
                player.queue.set_loop_mode(mode=LoopMode.TRACK)
                await ctx.respond('Now looping the `current song`.', delete_after=7,)
                await player.queue_update()
            elif mode.lower() == 'queue':                                                    # add a check whether the queue is smaller than 2?
                player.queue.set_loop_mode(mode=LoopMode.QUEUE)
                await ctx.respond('Now looping the `whole queue`.', delete_after=7,)
                await player.queue_update()
            elif mode.lower() == '?':
                await ctx.respond(f'Current mode: `{"Disabled" if player.queue.loop_mode is None else player.queue.loop_mode}`', delete_after=7,)
            else:
                await ctx.respond('Invalid loop mode...', delete_after=5,)

def setup(bot):
    bot.add_cog(Loop(bot))

# def currentLoopMode() -> None:              # maybe using player.queue.loop_mode
#     global loop_mode
#     if loop_mode == 0:
#         return 'Disabled'
#     elif loop_mode == 1:
#         return 'Current Track'
#     elif loop_mode == 2:
#         return 'Whole queue'
