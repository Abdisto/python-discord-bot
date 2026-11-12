from contextlib import suppress
import datetime

import discord
from discord.ext import commands

import pomice

from .player import Player

class Queue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = pomice.Queue()
        self.controller: discord.Message = None

    @commands.slash_command(name='queue', description='Returns the queue.')
    async def queue(self, ctx):
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
            await player.queue_update(qu_ctx=ctx)
            await ctx.respond('Queue updated ...', delete_after=5) # mach das schöner :c

        except Exception:
            self.bot.logger.exception('')

def setup(bot):
    bot.add_cog(Queue(bot))
