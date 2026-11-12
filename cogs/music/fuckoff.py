import discord
from discord.ext import commands
from discord.commands import Option
import asyncio

import time as t

from .player import Player

class Fuck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='fuckoff')
    async def fuckoff(self, ctx) -> None:
        if not (player := ctx.voice_client):
            return await ctx.respond(
                "Nah fuck off, I ain't even in a channel!",
                delete_after=7,
            )

        await ctx.respond(
            'NO FUCK YOU! NOT GONNA FUCK OFF!',
            delete_after=69,
        )
        await asyncio.sleep(2)
        await ctx.respond('Nah just gonna leave, fuck all of you. :middle_finger: ', delete_after=69,)

        player: Player = ctx.voice_client

        await player.disconnect()
        await self.bot.change_presence(activity=None)

def setup(bot):
    bot.add_cog(Fuck(bot))
