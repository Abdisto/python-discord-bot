import time as t

import discord
from discord.ext import commands, tasks
from discord.commands import Option
from discord.utils import basic_autocomplete

import pomice

from fuzzywuzzy import process, utils

from ..errorHandler import print_timestamp
from ..cache import Cache
from .player import Player

cache = Cache()

def autocomplete_query(ctx: discord.AutocompleteContext):
    user_input = ctx.value.lower()
    titles = cache.autocomplete()

    processed_input = utils.full_process(user_input)

    if not processed_input:
        return titles if titles else []

    try:
        matches = process.extract(user_input, titles, limit=5)
        filtered_titles = [match[0] for match in matches]
        return filtered_titles
    except Exception as e:
        print_timestamp(e, 'Error in autocomplete_query(): ', 1)
        return []

class Play(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.cache_reload_task.start()

    async def join_channel(self, ctx) -> None:
        channel = getattr(ctx.author.voice, 'channel', None)
        if not channel:
            await ctx.respond(
                'You must be in a voice channel in order for the bot to play music.',
                delete_after=7,
            )

        await ctx.author.voice.channel.connect(cls=Player)
        await ctx.respond(f'Joined the voice channel `{channel}`', delete_after=7,)

    @commands.slash_command(
        name='play',
        description='Playing music.')
    @discord.option(
        name='query',
        description='Either URL or song name.',
        autocomplete=autocomplete_query,
        required=True)
    # @discord.option(                                                   (not implemented yet)',
    #     name='attachment',
    #     description='Upload a file to play.
    #     required=False,
    #     type=discord.Attachment)
    async def play(self, ctx, query: str = None) -> None: # , attachment: discord.Attachment = None
        # if attachment:
        #     return await ctx.respond('Sorry not implemented yet. ;c')
        await ctx.defer()
        print_timestamp(f'{ctx.author.name} - {query}', f'Requested play command by: ')
        # add a check to see if the bot and node are already connected
        try:
            if not (player := ctx.voice_client):
                await ctx.invoke(self.join_channel)

            player: Player = ctx.voice_client
            await player.set_context(ctx=ctx)
            await player.set_volume(5)

            checked_query = cache.check_query(query)
            results = await player.get_tracks(query=f'{checked_query}')
            # results = await cache.data_parser(results, query)

            if not results:
                raise commands.CommandError('No results were found for that search term.')
                await ctx.respond('No results were found for that search term.', delete_after=7,)

            if isinstance(results, pomice.Playlist):
                i = 0
                msg = await ctx.send('Adding tracks to the queue.')
                max_tracks = 20
                for track in results.tracks:
                    if i >= max_tracks:
                        break
                    await ctx.respond(f'Added `{track}` to the queue.', delete_after=5,)
                    await msg.edit(content=f'Added `{i+1}/{max_tracks}` tracks to the queue.')
                    player.queue.put(track)
                    cache.data_parser(track.title, track.identifier)
                    i += 1
                await player.queue_update(player)
                await msg.delete()
            else:
                track = results[0]
                await ctx.respond(f'Added `{track}` to the queue.', delete_after=14,)
                player.queue.put(track)
                await player.queue_update(player)
                cache.data_parser(track.title, track.identifier)

            if not player.is_playing:
                await player.do_next(bot=self.bot)

        except Exception as e:
            print_timestamp(e, f'Error in play: ', 1)

    @commands.Cog.listener()
    async def on_pomice_track_end(self, player: Player, track, _):
        await player.do_next(bot=self.bot)
        await player.queue_update(player)

    @commands.Cog.listener()
    async def on_pomice_track_stuck(self, player: Player, track, _):
        await player.do_next(bot=self.bot)
        await player.queue_update(player)

    @commands.Cog.listener()
    async def on_pomice_track_exception(self, player: Player, track, _):
        await player.do_next(bot=self.bot)
        await player.queue_update(player)

    @tasks.loop(seconds=10)
    async def cache_reload_task(self):
        cache.reload_cache()

def setup(bot):
    bot.add_cog(Play(bot))
