import discord
from discord.ext import commands

import pomice

from .player import Player

class Leave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='leave', description='Leaving the current channel.')
    async def leave(self, ctx):
        if not (player := ctx.voice_client):
            return await ctx.respond(
                'You must have the bot in a channel in order to use this command',
                delete_after=7,
            )

        player: Player = ctx.voice_client

        await player.disconnect()
        await ctx.respond('Bot has left the channel.', delete_after=7,)
        await self.bot.change_presence(activity=None)

def setup(bot):
    bot.add_cog(Leave(bot))