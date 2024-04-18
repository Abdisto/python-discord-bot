import discord
from discord.ext import commands
from discord.commands import Option

from ..errorHandler import print_timestamp
from .player import Player

class Skip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='skip', description='Skipping the currently playing song.')
    async def pause(self, ctx) -> None:
        await ctx.defer()
        print_timestamp(ctx.author.name, f'Requested skip command by: ')
        if not (player := ctx.voice_client):
            return await ctx.respond(
                'You must have the bot in a channel in order to use this command',
                delete_after=7,
            )

        player: Player = ctx.voice_client

        if not player.is_connected:
            await ctx.respond('Nothing to skip.', delete_after=7,)
            return

        await ctx.respond('Skipping the track...', delete_after=7,)
        await player.stop()

def setup(bot):
    bot.add_cog(Skip(bot))
