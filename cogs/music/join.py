import discord
from discord.ext import commands

from ..errorHandler import print_timestamp
from .play import Play

class Join(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='join', description='Joining the current channel.')
    async def join(self, ctx) -> None:
        await ctx.defer()
        print_timestamp(ctx.author.name, f'Requested join command by: ')
        try:
            await Play.join_channel(self, ctx)
        except Exception as e:
            print_timestamp(e, 'Error occurred at "join.py": ', 1)
            await ctx.respond(
                'You must be in a voice channel in order for the bot to join.',
                delete_after=7,
            )

def setup(bot):
    bot.add_cog(Join(bot))