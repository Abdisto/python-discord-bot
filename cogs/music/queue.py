from contextlib import suppress
import datetime

import discord
from discord.ext import commands

import pomice

from ..errorHandler import print_timestamp
from .player import Player

class Queue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = pomice.Queue()
        self.controller: discord.Message = None

    @commands.slash_command(name='queue', description='Returns the queue.')
    async def queue(self, ctx):
        await ctx.defer()
        print_timestamp(ctx.author.name, f'Requested queue command by: ')
        if not (player := ctx.voice_client):
            return await ctx.respond(
                'You must have the bot in a channel in order to use this command',
                delete_after=7,
            )

        q = player.queue.get_queue()

        if q == [] and not self.bot.voice_clients[0].is_playing:
            return await ctx.respond(                
                'Bot is not playing anything and the queue is empty.',
                delete_after=7,
            )

        try:
            player: Player = ctx.voice_client
            await player.set_queue_context(q_ctx=ctx)
            await player.queue_update()

        except Exception as e:
            print_timestamp(e, f'Error at queue command: ', 1)

    def convert(t):
        return str(datetime.timedelta(seconds=t))

def setup(bot):
    bot.add_cog(Queue(bot))
