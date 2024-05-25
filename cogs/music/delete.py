import discord
from discord.ext import commands

import pomice

from ..errorHandler import print_timestamp
from .player import Player

class Delete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = pomice.Queue()

    @commands.slash_command(name='delete', description='Deletes a song from the queue by index.')
    async def delete(self, ctx, index: int):
        await ctx.defer()
        print_timestamp(ctx.author.name, f'Requested delete command by: ')
        player: Player = ctx.voice_client
        queue = player.queue.get_queue()

        if not player.queue:
            return await ctx.respond('The queue is empty.', delete_after=7,)
        
        try:
            track = queue[index-1]
            if not track == []:
                player.queue.remove(track)
                print_timestamp(track, f'Track deleted from the queue: ')
                await ctx.respond(f'The Song `{track}` has been removed from the queue.', delete_after=7,)
                await player.queue_update()
            else:
                await ctx.respond(f'Index `{index}` is out of range.', delete_after=7,)
        except IndexError:
            await ctx.respond(f'Index `{index}` is out of range..', delete_after=7,)

def setup(bot):
    bot.add_cog(Delete(bot))
