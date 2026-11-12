import discord
from discord.ext import commands

from .play import Play

class Join(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='join', description='Joining the current channel.')
    async def join(self, ctx) -> None:
        try:
            await Play.join_channel(self, ctx)
        except Exception as e:
            self.bot.logger.info(self.bot.format(e, 'Error occurred at "join.py": ', 1))
            await ctx.respond(
                'You must be in a voice channel in order for the bot to join.',
                delete_after=7,
            )

def setup(bot):
    bot.add_cog(Join(bot))