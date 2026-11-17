import asyncio
import mimetypes
import os

# import magic
import time
from asyncio.subprocess import Process
from typing import Any
from urllib.parse import parse_qs, urlparse

import discord
import pomice
from discord import ApplicationContext
from discord.commands import Option
from discord.commands.core import SlashCommandGroup
from discord.ext import commands
from discord.interactions import Interaction
from discord.webhook.async_ import WebhookMessage
from pomice.objects import Playlist

from cache import Cache
from .player import Player

AUDIO_EXTS = Cache.AUDIO_EXTS


def _audio_files_in(path: str) -> list[str]:
    """Audio files in the (flat) library, newest first. Hidden files and *.png thumbnails are skipped."""
    if not path or not os.path.isdir(path):
        return []
    files = [
        os.path.join(path, name)
        for name in os.listdir(path)
        if not name.startswith('.') and name.lower().endswith(AUDIO_EXTS)
    ]
    files.sort(key=os.path.getmtime, reverse=True)
    return files


class Play(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.deleting_files: set[str] = set()
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

            # Discord allows at most 25 autocomplete choices,
            # each with a non-empty name of at most 100 characters.
            valid_matches = []
            for match in matches:
                name = match.name if hasattr(match, "name") else str(match)
                if name and name.strip() and len(name) <= 100:
                    valid_matches.append(match)
                if len(valid_matches) == 25:
                    break

            return valid_matches

        except Exception:
            self.bot.logger.exception("Autocomplete failed")
            return [ctx.value] if ctx.value else []

    play: SlashCommandGroup = discord.SlashCommandGroup(name = 'play', description = 'playing music')

    @staticmethod
    def _normalize_query(query: str) -> str:
        """Turn youtube.com/results?search_query=X URLs into ytsearch: queries Lavalink understands; pass everything else through."""
        if query.startswith(('ytsearch:', 'search:', 'local:', 'http')):
            return query

        parsed = urlparse(query)
        if parsed.scheme in ('http', 'https') and 'youtube.com' in (parsed.netloc or ''):
            path = parsed.path
            if path == '/results':
                q = parse_qs(parsed.query).get('search_query', [''])[0]
                if q:
                    return f'ytsearch:{q}'
            elif path == '/playlist':
                list_id = parse_qs(parsed.query).get('list', [''])[0]
                if list_id:
                    return f'ytsearch:{list_id}'

        return query

    @staticmethod
    def _is_audio_type(mime: str | None, filename: str | None) -> bool:
        """Permissive upload check: Discord often sends no MIME or application/octet-stream, so only clearly non-audio types (text/image) are blocked; Lavalink does the real decode."""
        if not mime:
            mime = mimetypes.guess_type(filename or "")[0]
            if not mime:
                return True

        if mime.split("/", 1)[0].lower() in {"audio", "video"}:
            return True

        if mime.lower() in {"application/octet-stream", "application/binary", "application/unknown"}:
            return True

        return mime.split("/", 1)[0].lower() not in {"text", "image", "message", "multipart", "model"}

    async def join_channel(self, ctx) -> Player | None:
        voice_state = getattr(ctx.author, "voice", None)
        channel = getattr(voice_state, "channel", None)

        if channel is None:
            await ctx.respond(
                "You must be in a voice channel in order for the bot to play music.",
                delete_after=7,
            )
            return None

        try:
            player = await channel.connect(cls=Player)
            await ctx.send(f"Joined the voice channel `{channel}`", delete_after=7)
            return player
        except Exception:
            self.bot.logger.exception("Failed to connect to voice channel")
            await ctx.respond(
                "Could not connect to the voice channel. Check the bot's permissions."
            )
            return None


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
                player = await self.join_channel(ctx)
            if player is None:
                await ctx.respond("Failed to connect to the voice channel.")
                return
            self.bot.players[guild_id] = player

        if not query:
            await ctx.respond('Please use the query handle.')
            return

        else:
            checked_query: Any = await self.bot.cache.check_query(query)
            checked_query = self._normalize_query(checked_query)
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

    async def _play_local_file(self, ctx, file_path: str, song_name: str | None = None) -> None:
        """Resolve an existing local audio file to a track and queue + play it.

        Shared by ``/play file`` (pick from the library) and the attachment
        path. Lavalink decodes the file; pomice routes the path as a local
        track when the file's directory exists on disk.
        """
        guild_id: int | None = ctx.guild_id
        lock: Any = self.bot.get_player_lock(guild_id)

        async with lock:
            player: Any = self.bot.players.get(guild_id)
            if player is None:
                player = await self.join_channel(ctx)
            if player is None:
                await ctx.respond("Failed to connect to the voice channel.")
                return
            self.bot.players[guild_id] = player

        display_name: str = song_name if song_name else os.path.splitext(os.path.basename(file_path))[0]

        results: Any = await player.get_tracks(query=file_path)
        if not results:
            await ctx.respond(f'Could not load `{os.path.basename(file_path)}` as a track.', delete_after=7,)
            return

        track: Any = results[0]
        track.requester = ctx.author
        track.identifier = file_path
        track.title = display_name
        track.uri = 'local'

        async with lock:
            await ctx.respond(f'Added `{track}` to the queue.', delete_after=7,)
            player.queue.put(track)
            await player.queue_update(qu_ctx=None)

        try:
            await self.bot.cache.data_parser(track.title, track.identifier)
        except Exception:
            self.bot.logger.exception('')

        async with lock:
            if not player.is_playing:
                await player.do_next(bot=self.bot)

            await player.embed_send(ctx=ctx, embed_list=player.np_embed_msg, embed=player.npEmbed())

    @play.command(
        name='file',
        description='play a song from the bot\'s local library (SONG_PATH)',
        options=[
            Option(name='name', description='Part of the song filename to search for', required=True),
        ]
    )
    async def file(self, ctx: ApplicationContext, name: str) -> None:
        await ctx.defer()

        songs = _audio_files_in(self.bot.local_songs_path or '')
        if not songs:
            await ctx.respond(
                'The bot has no local songs to play yet. Upload one with `/play attachment`.',
                delete_after=7,
            )
            return

        needle = name.lower()
        matches = [f for f in songs if needle in os.path.basename(f).lower()]
        if not matches:
            sample = ', '.join(os.path.splitext(os.path.basename(f))[0] for f in songs[:8])
            suffix = '' if len(songs) <= 8 else f' … (+{len(songs)-8} more, use `/songs` to list)'
            await ctx.respond(
                f'No song matching `{name}`. In the library: {sample}{suffix}',
                delete_after=10,
            )
            return

        if len(matches) > 1:
            listing = '\n'.join(f'  • {os.path.splitext(os.path.basename(f))[0]}' for f in matches[:25])
            more = f'\n  … and {len(matches)-25} more' if len(matches) > 25 else ''
            await ctx.respond(f'Multiple matches — be more specific:\n{listing}{more}', delete_after=15,)
            return

        await self._play_local_file(ctx, matches[0])

    @commands.slash_command(name='songs', description='List the songs in the bot\'s local library.')
    async def songs(self, ctx: ApplicationContext) -> None:
        await ctx.defer()

        songs = _audio_files_in(self.bot.local_songs_path or '')
        if not songs:
            await ctx.respond('The library is empty.', delete_after=7,)
            return

        embed = discord.Embed(
            title=f'Local library ({len(songs)} songs)',
            description='Most recent first. Play one with `/play file <name>`.',
            colour=0x264971,
        )
        for i, f in enumerate(songs[:25], start=1):
            title = os.path.splitext(os.path.basename(f))[0]
            embed.add_field(name=str(i), value=f'`{title}`', inline=False)
        if len(songs) > 25:
            embed.set_footer(text=f'Showing {25} of {len(songs)} — search with `/play file <name>`.')
        await ctx.respond(embed=embed, delete_after=None)

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
                player = await self.join_channel(ctx)
            if player is None:
                await ctx.respond("Failed to connect to the voice channel.")
                return
            self.bot.players[guild_id] = player

        if attachment:
            # A given song_name earns a permanent spot in the library; without one the file
            # goes to /tmp, plays, and is deleted after the track ends (deleting_files).
            if song_name:
                if not self.bot.local_songs_path:
                    await ctx.respond('The bot has no configured song path (SONG_PATH).', delete_after=7,)
                    return
                os.makedirs(name = self.bot.local_songs_path, exist_ok = True)
                file_name = song_name
            else:
                os.makedirs('/tmp', exist_ok=True)
                base: str = os.path.splitext(attachment.filename or 'song')[0]
                file_name = f'song_{int(time.time())}_{base[-40:]}'

            file_path = os.path.join(
                self.bot.local_songs_path if song_name else '/tmp',
                file_name,
            )
            thumbnail_file_path: str = f'{file_path}.png'

            # mime_type = self.magic.from_buffer(await attachment.read())
            mime_type: str | None = attachment.content_type or mimetypes.guess_type(attachment.filename or "")[0]
            if not self._is_audio_type(mime_type, attachment.filename):
                await ctx.respond(f'Unsupported file type: {mime_type}', delete_after=7,)
                return

            await attachment.save(fp = file_path)  # pyright: ignore[reportArgumentType]
            self.bot.logger.info(self.bot.format(f'Saved upload to {file_path}'))

            if not os.path.isfile(path = thumbnail_file_path):
                try:
                    process: Process = await asyncio.create_subprocess_exec(
                        "ffmpeg",
                        "-i", file_path,
                        "-y",                       # overwrite any stale thumbnail
                        "-an",                      # drop audio, keep the picture
                        "-vframes", "1",             # exactly one frame
                        thumbnail_file_path,
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL,
                    )
                    returncode: int = await process.wait()
                    if returncode != 0:
                        self.bot.logger.info("Could not extract thumbnail.")
                except Exception:
                    self.bot.logger.info('Could not extract thumbnail.')

            results: Any = await player.get_tracks(query=file_path)
            if not results:
                await ctx.respond("Could not load that audio file.", delete_after=7,)
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
                try:
                    await self.bot.cache.data_parser(track.title, track.identifier)
                except Exception:
                    self.bot.logger.exception('')
            else:
                self.deleting_files.add(track.identifier)

        async with lock:
            if not player.is_playing:
                await player.do_next(bot=self.bot)

            await player.embed_send(ctx=ctx, embed_list=player.np_embed_msg, embed=player.npEmbed())


    def _purge_local_file(self, track) -> None:
        """Delete an unnamed uploaded file from disk once its track is done."""
        if track.identifier not in self.deleting_files:
            return
        try:
            os.remove(track.identifier)
            self.bot.logger.info(
                self.bot.format(f'Deleted {track.identifier} since song_name not set.')
            )
        except OSError:
            self.bot.logger.exception('')
        finally:
            self.deleting_files.discard(track.identifier)

    @commands.Cog.listener()
    async def on_pomice_track_end(self, player: Player, track, _) -> None:
        self._purge_local_file(track)
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
        self._purge_local_file(track)
        if player.progress:
            player.progress.stop()
        await player.do_next(bot=self.bot)
        await player.queue_update(qu_ctx=None)

    @commands.Cog.listener()
    async def on_pomice_track_exception(self, player: Player, track, _) -> None:
        self._purge_local_file(track)
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
