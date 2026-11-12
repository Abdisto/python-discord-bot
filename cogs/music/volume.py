import discord
from discord.ext import commands
from discord.commands import Option

from .player import Player

class Volume(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name='volume', 
        description='Change the volumen of the bot.',)
    @commands.check_any(
        commands.is_owner(),
        commands.has_any_role(541986455619239938, 753661263195668591)
    )
    @discord.option(
        name='volume',
        type=int,
        description='Number between 1-25 (default. 5)',)
    async def volume(self, ctx, volume: int) -> None:
        if not (player := ctx.voice_client):
            return await ctx.respond(
                'You must have the bot in a channel in order to use this command',
                delete_after=7,
            )

        player: Player = ctx.voice_client

        if volume > 25 or volume < 1:
            return await ctx.respond('Volume set is not applicable.')

        await player.set_volume(volume)
        await ctx.respond(f'Volume set to {volume}.', delete_after=7,)

def setup(bot):
    bot.add_cog(Volume(bot))
