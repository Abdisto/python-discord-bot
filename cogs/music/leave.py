import discord
from discord.ext import commands

import pomice

from ..errorHandler import print_timestamp
from .player import Player

class Leave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='leave', description='Leaving the current channel.')
    async def leave(self, ctx):
        await ctx.defer()
        print_timestamp(ctx.author.name, f'Requested leave command by: ')
        if not (player := ctx.voice_client):
            return await ctx.respond(
                'You must have the bot in a channel in order to use this command',
                delete_after=7,
            )

        player: Player = ctx.voice_client

        await player.destroy()
        await ctx.respond('Bot has left the channel.')
        await self.bot.change_presence(activity=None)

def setup(bot):
    bot.add_cog(Leave(bot))