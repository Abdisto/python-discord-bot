import discord
from discord.ext import commands

import pomice

from .player import Player

class Stop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = pomice.Queue()

    @commands.slash_command(name='stop', description='Deletes the queue.')
    async def stop(self, ctx):
        if not (player := ctx.voice_client):
            return await ctx.respond(
                'You must have the bot in a channel in order to use this command.',
                delete_after=7,
            )

        player: Player = ctx.voice_client

        if not player.is_connected or not player.is_playing:
            return await ctx.respond('Nothing to delete.', delete_after=3,)

        if player.queue.is_looping:
            player.queue.disable_loop()
        player.queue.clear()
        player.progress.stop()
        await self.bot.voice_clients[0].stop()
        await ctx.respond('Queue was deleted and potential loop disabled.', delete_after=3,)
        await self.bot.change_presence(activity=None)

def setup(bot):
    bot.add_cog(Stop(bot))
