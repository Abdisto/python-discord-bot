import discord
from discord.ext import commands, tasks
from discord.commands import Option

from rich import inspect

from pomice import Node, NodePool, exceptions

from urllib.parse import quote

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def generate_embed(self):
        embed = discord.Embed(
            title='',
            description='',
            color=''
        )

    @commands.slash_command(
        name='status',
        description='Status.'
    )
    async def status(self, ctx) -> None:
        # inspect(self.bot.cache.conn, methods=True)
        if self.bot.player == []:
            await ctx.respond('No player.')
            # return
        # for player in self.bot.player:
        #     if player:
        #         await ctx.respond(player.node.ping)
        #         inspect(player, methods=True)
        else:
            node = self.bot.player[0].node
            await ctx.respond(f'{node.ping}:{node.player_count}')

        # await ctx.respond()


        node = NodePool.get_node(identifier='MAIN')

        # GET /youtube -> refreshToken

        refreshToken = await node.send(
            include_version = False, 
            method="GET", 
            path="youtube"
        )

        refreshToken = quote(refreshToken['refreshToken'])

        self.bot.logger.info(refreshToken)

        # GET /youtube/oauth/{refreshToken} -> refreshTokenInfo

        data = await node.send(
            include_version = False,
            method="GET",
            path=f"youtube/oauth/{refreshToken}",
        )

        # print(data['text'])
        # print('\n')
        # print(JSON.from_data(data))
        self.bot.logger.info(data)

def setup(bot):
    bot.add_cog(Status(bot))
