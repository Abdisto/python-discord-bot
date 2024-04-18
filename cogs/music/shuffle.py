import discord
from discord.ext import commands
from discord.commands import Option

from ..errorHandler import print_timestamp
from .player import Player

class Shuffle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='shuffle', description='Shuffles the queue.')
    async def shuffle(self, ctx) -> None:
        await ctx.defer()
        print_timestamp(ctx.author.name, f'Requested shuffle command by: ')
        if not (player := ctx.voice_client):
            return await ctx.respond(
                'You must have the bot in a channel in order to use this command',
                delete_after=7,
            )

        player: Player = ctx.voice_client

        if not player.is_connected:
            await ctx.respond('Nothing to shuffle.', delete_after=7,)
            return

        if player.queue.size < 3:
            return await ctx.respond(
                'The queue is to small. Add some songs to shuffle the queue.',
                delete_after=15,
            )

        await ctx.respond('Shuffling the queue...', delete_after=7,)
        player.queue.shuffle()

def setup(bot):
    bot.add_cog(Shuffle(bot))
