import asyncio
import os

# import magic
import subprocess
import time
from asyncio.subprocess import Process
from typing import Any

import discord
import pomice
from discord import ApplicationContext
from discord.commands import Option
from discord.commands.core import SlashCommandGroup
from discord.ext import commands
from discord.interactions import Interaction
from discord.webhook.async_ import WebhookMessage
from pomice.objects import Playlist, Track

from .player import Player


class Play(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.allowed_mime_types = ['audio/mpeg', 'audio/x-ms-wma', 'audio/vnd.wave', 'video/mpeg', 'audio/flac', 'video/mp4', 'video/webm', 'audio/mpeg3']
        self.deleting_files = set()
        # self.magic = magic.Magic(mime=True)
        # self.cache_reload_task.start()

    async def autocomplete_query(self, ctx: discord.AutocompleteContext) -> list[str] | Any:
        start: float = time.perf_counter()

        try:
            query: str = ctx.value.strip()

            if self.bot.cache is None:
                return [query] if query else []

            matches: Any = await self.bot.cache.match(query)

            elapsed: float = (time.perf_counter() - start) * 1000
            self.bot.logger.debug(
                f"Autocomplete {query!r}: {elapsed:.2f} ms"
            )

            return matches

        except Exception:
            self.bot.logger.exception("Autocomplete failed")
            return [ctx.value] if ctx.value else []

    play: SlashCommandGroup = discord.SlashCommandGroup(name = 'play', description = 'playing music')

    async def join_channel(self, ctx) -> None:
        channel: Any | None = getattr(ctx.author.voice, 'channel', None)
        if not channel:
            await ctx.respond(
                'You must be in a voice channel in order for the bot to play music.',
                delete_after=7,
            )
            return

        await ctx.author.voice.channel.connect(cls=Player)
        await ctx.send(f'Joined the voice channel `{channel}`', delete_after=7,)


    @play.command(
        name='query',
        description='playing a song with a url or a searchterm',
        options=[
            Option(name='query', description='Your url or searchterm', autocomplete=autocomplete_query, required=True),
            Option(name='playlist_from', description='If only, will play from x→x+20', type=int, required=False, default=1),
            Option(name='playlist_to', description='If only will play from 1→x', type=int, required=False, default=None),
        ]
    )
    async def query(
        self,
        ctx: ApplicationContext,
        query: str,
        playlist_from: int,
        playlist_to: int,
    ) -> None:
        await ctx.defer()
        guild_id: int | None = ctx.guild_id
        lock = self.bot.get_player_lock(guild_id)

        player: Player | Any

        async with lock:
            player = self.bot.players.get(guild_id)
            if player is None:
                await self.join_channel(ctx)
                player = ctx.voice_client
            if player is None:
                await ctx.respond("Failed to connect to the voice channel.")
                return
            self.bot.players[guild_id] = player

        if not query:
            await ctx.respond('Please use the query handle.')
            return

        else:
            checked_query: Any = await self.bot.cache.check_query(query)
            results: list[Track] | Playlist | None = await player.get_tracks(query=checked_query)

            if not results:
                await ctx.respond('No results were found for that search term.', delete_after=7,)
                return

        async with lock:
            if isinstance(results, pomice.Playlist):
                tracks_delta: int = (int(playlist_to) - int(playlist_from)) - 1 if playlist_to else 20
                if tracks_delta < 1 or int(playlist_from) < 1 or int(playlist_to) < 1:
                    await ctx.send('Invalid track-range. Will impose the default of first 20 tracks.', delete_after=7,)
                    playlist_from = 1
                    tracks_delta = 20

                i, j = 0, 0
                msg: Interaction | WebhookMessage = await ctx.respond('Adding tracks to the queue.')
                already_added = '\n'
                for track in results.tracks:
                    if j < (int(playlist_from)-1):
                        j += 1
                        continue
                    if i >= tracks_delta:
                        break
                    track.requester = ctx.author
                    player.queue.put(item = track)
                    # self.bot.cache.data_parser(track.title, track.identifier)
                    if not player.is_playing:
                        await player.do_next(bot=self.bot)
                    # progress: str = f'{i+1}/{tracks_delta}'
                    already_added += f' ▸ Added `{track}` to the queue.\n'
                    await msg.edit(content=f'Added `{i+1}/{tracks_delta}` tracks to the queue. {already_added}')
                    i += 1
                await player.queue_update(qu_ctx = None)
            else:
                track: Track | Any = results[0]
                track.requester = ctx.author
                await ctx.respond(f'Added `{track}` to the queue.', delete_after = 7,)
                player.queue.put(item = track)
                await player.queue_update(qu_ctx = None)
                try:
                    # self.bot.cache.data_parser(track.title, track.identifier)
                    await self.bot.cache.data_parser(track.title, track.uri)
                except Exception:
                    self.bot.logger.exception('')
            if not player.is_playing:
                await player.do_next(bot = self.bot)

            await player.embed_send(ctx = ctx, embed_list = player.np_embed_msg, embed = player.npEmbed())

    @play.command(
        name='attachment',
        description='playing a song with you uploading an attachment',)
    @discord.option(
        name='attachment',
        description='Upload a file to play',
        type=discord.Attachment,
        required=True,)
    @discord.option(
        name='song_name',
        description='If not supplied. Song will not be saved.',
        type=str,
        required=False,)
    async def attachment(
        self,
        ctx: ApplicationContext,
        attachment: discord.Attachment,
        song_name: str,
    ) -> None:
        await ctx.defer()
        guild_id: int | None = ctx.guild_id
        lock: Any = self.bot.get_player_lock(guild_id)

        async with lock:
            player: Any = self.bot.players.get(guild_id)
            if player is None:
                await self.join_channel(ctx)
                player = ctx.voice_client
            if player is None:
                await ctx.respond("Failed to connect to the voice channel.")
                return
            self.bot.players[guild_id] = player

        if attachment:
            file_name: str
            if song_name:
                file_name = song_name
            else:
                file_name = (attachment.filename.strip('.' + attachment.filename.split(sep = '.')[-1]))

            file_path = os.path.join(self.bot.local_songs_path, file_name)
            thumbnail_file_path: str = f'{file_path}.png'

            # mime_type = self.magic.from_buffer(await attachment.read())
            mime_type: str | None = attachment.content_type
            if mime_type not in self.allowed_mime_types:
                await ctx.respond(f'Unsupported file type: {mime_type}', delete_after=7,)
                return

            await attachment.save(fp = file_path)  # pyright: ignore[reportArgumentType]
            self.bot.logger.info(self.bot.format(f'Saved song to {file_path}'))

            if not os.path.isfile(path = thumbnail_file_path):
                try:
                    process: Process = await asyncio.create_subprocess_exec(
                        "ffmpeg",
                        "-i", file_path,
                        "-compression_level", "9",
                        thumbnail_file_path,
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL,
                    )
                    returncode: int = await process.wait()
                    if returncode != 0:
                        self.bot.logger.info("Could not extract thumbnail.")
                except subprocess.CalledProcessError:
                    self.bot.logger.info('Could not extract thumbnail.')

            results: Any = await player.get_tracks(query=file_path)
            if not results:
                await ctx.respond("Could not load that audio file.")
                return
            track: Any = results[0]
            track.requester = ctx.author
            track.identifier = file_path
            track.title = file_name
            track.uri = 'local'

            async with lock:
                await ctx.respond(f'Added `{track}` to the queue.', delete_after=7,)
                player.queue.put(track)
                await player.queue_update(qu_ctx=None)

            if song_name:
                await self.bot.cache.data_parser(track.title, track.identifier)
            else:
                self.deleting_files.add(track.identifier)

        async with lock:
            if not player.is_playing:
                await player.do_next(bot=self.bot)

            await player.embed_send(ctx=ctx, embed_list=player.np_embed_msg, embed=player.npEmbed())


    @commands.Cog.listener()
    async def on_pomice_track_end(self, player: Player, track, _) -> None:
        if track.identifier in self.deleting_files:
            try:
                os.remove(path = track.identifier)
                self.bot.logger.info(
                    self.bot.format(f'Deleted {track.identifier} since song_name not set.')
                )
            except OSError:
                self.bot.logger.exception('')
            finally:
                self.deleting_files.discard(track.identifier)
        try:
            if player.progress:
                player.progress.stop()
            await player.do_next(bot = self.bot)
            await player.queue_update(qu_ctx = None)
        except discord.errors.HTTPException as e:
            if e.status == 401 and e.code == 50027:
                await player.queue_update(qu_ctx = None)
            else:
                raise

    @commands.Cog.listener()
    async def on_pomice_track_stuck(self, player: Player, track, _) -> None:
        if track.identifier in self.deleting_files:
            try:
                os.remove(path = track.identifier)
                self.bot.logger.info(
                    self.bot.format(f'Deleted {track.identifier} since song_name not set.')
                )
            except OSError:
                self.bot.logger.exception('')
            finally:
                self.deleting_files.discard(track.identifier)
        if player.progress:
            player.progress.stop()
        await player.do_next(bot=self.bot)
        await player.queue_update(qu_ctx=None)

    @commands.Cog.listener()
    async def on_pomice_track_exception(self, player: Player, track, _) -> None:
        if track.identifier in self.deleting_files:
            try:
                os.remove(track.identifier)
                self.bot.logger.info(
                    self.bot.format(f'Deleted {track.identifier} since song_name not set.')
                )
            except OSError:
                self.bot.logger.exception('')
            finally:
                self.deleting_files.discard(track.identifier)
        if player.progress:
            player.progress.stop()
        await player.do_next(bot=self.bot)
        await player.queue_update(qu_ctx=None)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after) -> None:
        if member.id != self.bot.user.id:
            return

        # Bot disconnected from a voice channel
        if before.channel is not None and after.channel is None:
            for player in self.bot.players.values():
                if player.progress:
                    player.progress.stop()

                await player.embed_delete()

            self.bot.logger.info(
                self.bot.format('The bot has been disconnected from the voice channel.')
            )

            # Check whether there is still a voice client in the channel
            current_channels: list[Any] = [
                vc for vc in self.bot.voice_clients
                if vc.channel.id == before.channel.id
            ]

            if current_channels:
                self.bot.logger.info(
                    self.bot.format('Bot is still in another channel, no action needed.')
                )
                return

            # No longer connected to that channel, tear down its Player
            guild_id: Any = member.guild.id
            player: Any = self.bot.players.get(guild_id)

            if player is not None:
                await player.teardown()

                if player.is_dead:
                    self.bot.players.pop(guild_id, None)

            voice_client: Any | None = discord.utils.get(
                iterable = self.bot.voice_clients,
                guild=member.guild,
            )

            if voice_client is not None:
                await voice_client.disconnect()

    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        if message.author.bot:
            return

        if message:
            return

    # @tasks.loop(seconds=10)
    # async def cache_reload_task(self):
    #     self.bot.cache.reload_cache()

def setup(bot) -> None:
    bot.add_cog(Play(bot))
