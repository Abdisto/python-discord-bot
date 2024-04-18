import discord
from discord.ext import commands
from discord.commands import Option

from ..errorHandler import print_timestamp
from .player import Player

class Resume(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='resume', description='Resuming the paused track.')
    async def resume(self, ctx) -> None:
        await ctx.defer()
        print_timestamp(ctx.author.name, f'Requested resume command by: ')
        if not (player := ctx.voice_client):
            return await ctx.respond(
                'You must have the bot in a channel in order to use this command',
                delete_after=7,
            )

        player: Player = ctx.voice_client

        if not player.is_paused or not player.is_connected:
            await ctx.respond('Nothing to resume...', delete_after=7,)
            return

        await ctx.respond('Resuming Bot.', delete_after=7,)
        await player.set_pause(False)

def setup(bot):
    bot.add_cog(Resume(bot))
