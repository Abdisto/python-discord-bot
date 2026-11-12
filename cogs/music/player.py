from contextlib import suppress
import asyncio
import datetime
import os

import discord
from discord.ext import commands
from urllib.parse import quote

import pomice

from rich.text import Text
from rich.style import Style
from rich.table import Column
from rich.color import Color
from rich.progress import Progress, SpinnerColumn, TextColumn, \
                          BarColumn, RenderableColumn, Task

from rich import inspect

class PlaybackTimerColumn(RenderableColumn):
    def render(self, task: Task) -> Text:
        elapsed = int(task.completed)
        minutes, seconds = divmod(elapsed, 60)
        text = Text(f"{minutes:02}:{seconds:02}")
        text.stylize("yellow", 0, len(text))
        return text

class Player(pomice.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.queue = pomice.Queue()
        self.queue_ctx: commands.context = None
        self.queue_message: discord.Message = None
        self.np_embed_msg = []
        self.qu_embed_msg = []
        self.track = None
        self.progress = None

    async def progressBar(self) -> None:
        if self.progress:
            self.progress.stop()

        track = self.current

        if track is None:
            return

        text_column = TextColumn(f'{track.title}', table_column=Column(ratio=2), style='#9F1D35')
        bar_column = BarColumn(bar_width=None, table_column=Column(ratio=5))
        spinner_column = SpinnerColumn(spinner_name='arrow3')
        time_elapsed = PlaybackTimerColumn()
        self.progress = Progress(
            text_column,
            spinner_column,
            bar_column,
            time_elapsed,
            transient=True,
            expand=True
        )

        duration = track.length // 1000
        elapsed = 0

        with self.progress:
            task = self.progress.add_task("Playback", total=duration)

            async def update_progress():
                nonlocal elapsed
                while elapsed < duration:
                    if self.is_playing:
                        elapsed = self.adjusted_position // 1000
                        self.progress.update(task, completed=elapsed)
                    await asyncio.sleep(0.2)

            await asyncio.create_task(update_progress())

    async def set_queue_context(self, q_ctx: commands.context) -> None:
        self.queue_ctx = q_ctx

    async def convert(self, time, milliseconds = True) -> str:
        if milliseconds is True:
            return str(datetime.timedelta(milliseconds=time)).split('.')[0]
        else:
            return str(datetime.timedelta(seconds=time))

    def npEmbed(self):
        track: pomice.Track = self.current
        if track and track.identifier and os.path.isfile(f'{track.identifier}') and self.bot.public_ip:
            # track.uri = f'https://abdist.serveo.net/{quote(track.title)}'
            # track.thumbnail = f'https://abdist.serveo.net/{quote(track.title)}.png'
            track.uri = f'{self.bot.public_ip}/bot-songs/{quote(track.title)}'
            track.thumbnail = f'{self.bot.public_ip}/bot-songs/{quote(track.title)}.png'
            # track.uri = f'https://perfect-pig-99.telebit.io/{quote(track.title)}'
            # track.thumbnail = f'https://perfect-pig-99.telebit.io/{quote(track.title)}.png'

        if track.info.get('artworkUrl'):
            track.thumbnail = track.info['artworkUrl']

        embed = discord.Embed(
            title = f'Currently Playing',
            description = f'[{track.title}]({track.uri}) - [{track.author}]',
            image = track.thumbnail,
            # colour = 0x00f6ff,
            colour = 0x264971,
        )
        embed.set_footer(text=f'Requested by {track.requester.name}', icon_url=track.requester.display_avatar)
        return embed

    def quEmbed(self, formatted_current_track, formatted_queue, loop_mode):
        embed = discord.Embed(
            title=f'Queue',
            description=f'**Current Track:**\n{formatted_current_track}\n\n**Next Tracks:**\n{formatted_queue}\n\nloop mode: {loop_mode}',
            colour=0xa3425d,
        )
        return embed

    async def embed_send(self, ctx, embed_list, embed) -> None:
        if not embed_list:
            message = await ctx.send(embed=embed)
            embed_list.append((message.channel, message.id))
        else:
            for channel, msg_id in embed_list:
                if ctx.channel == channel:
                    break
            else:
                message = await ctx.send(embed=embed)
                embed_list.append((message.channel, message.id))

    async def embed_edit(self, embed_list, embed) -> None:
        for i, (channel, msg_id) in enumerate(embed_list):
            try:
                message = await channel.fetch_message(msg_id)
                await message.edit(embed=embed)
            except discord.NotFound:
                message = await channel.send(embed=embed)
                embed_list[i] = (channel, message.id)

    async def iter_delete(self, embed_list) -> None:
        for channel, msg_id in embed_list:
            try:
                message = await channel.fetch_message(msg_id)
                await message.delete()
                self.bot.logger.info(self.bot.format(f'Destroyed "Currently playing" embed in "{channel.name}" successfully.'))
            except discord.errors.NotFound:
                self.bot.logger.exception('')
        embed_list.clear()

    async def embed_delete(self) -> None:
        if self.np_embed_msg:
            await self.iter_delete(self.np_embed_msg)
        if self.qu_embed_msg:
            await self.iter_delete(self.qu_embed_msg)

    async def do_next(self, bot) -> None:
        await self.set_volume(5)

        if self.queue.is_empty:
            await bot.presence(track_title=None)
            await self.embed_delete()
            return

        try:
            track: pomice.Track = self.queue.get()

            await self.play(track)

            self.bot.logger.info(
                self.bot.format(
                    track.title,
                    'Now Playing: ',
                    3,
                    track.uri,
                )
            )

            await bot.presence(track_title=track.title)
            await self.embed_edit(
                embed_list=self.np_embed_msg,
                embed=self.npEmbed(),
            )

            asyncio.create_task(self.progressBar())

        except pomice.QueueEmpty:
            # Race protection: another coroutine may have consumed the queue
            await bot.presence(track_title=None)
            await self.embed_delete()

        except pomice.TrackLoadError as e:
            self.bot.logger.error(
                self.bot.format(
                    e,
                    'Could not play track: ',
                    1,
                )
            )

    async def teardown(self) -> None:
        with suppress((discord.HTTPException), (KeyError)):
            try:
                await self.destroy()
                await self.queue_update(qu_ctx=None)
                # await self.embed_delete() # See if bot deletes embed after stopping the bot appr. in console
            except Exception as e:
                if isinstance(e, KeyError) and e.args and e.args[0] == 506063264895991808:
                    pass
                else:
                    self.bot.logger.exception('')

    async def queue_update(self, qu_ctx) -> None:
        try:
            queue_copy = self.queue.copy()
            queue: list[pomice.Track] = queue_copy.get_queue()
            current_track: pomice.Track = self.current
        except pomice.QueueEmpty:
            #self.bot.logger.exception('')
            queue = []
            current_track = None

        # print(f'reached queue_update {queue} {current_track}')

        if current_track or queue:
            # print('entered if statement')
            if current_track and current_track.identifier and os.path.isfile(f'{current_track.identifier}') and self.bot.public_ip:
                # current_track.uri = f'https://abdist.serveo.net/{quote(current_track.title)}'
                current_track.uri = f'{self.bot.public_ip}/{quote(current_track.title)}'
                # current_track.uri = f'https://perfect-pig-99.telebit.io/{quote(current_track.title)}'

            formatted_current_track = (
                f'[{current_track.title}]({current_track.uri}) '
                f'[{await self.convert(time=self.adjusted_position)} / {await self.convert(time=self.adjusted_length)}]'
            ) if current_track else 'No current track.'

            loop_mode = 'Disabled' if self.queue.loop_mode is None else self.queue.loop_mode

            rearranged_queue = queue

            if self.queue.loop_mode and self.queue.loop_mode.name == 'QUEUE':
                current_track_index = next((i for i, track in enumerate(queue) if track == current_track), -1)
                if current_track_index != -1:
                    before_current = queue[:current_track_index]
                    after_current = queue[current_track_index:]
                    rearranged_queue = after_current + before_current

            loop_mode_check = self.queue.loop_mode.name if self.queue.loop_mode else None

            if loop_mode_check == 'QUEUE':
                start = 1
                loop_mode_adjustment = 0
            else:
                start = 0
                loop_mode_adjustment = 1

            end = len(queue)

            formatted_queue = ''
            for i, track in enumerate(rearranged_queue[start:end], start=start):
                try:
                    length = await self.convert(time=(track.length // 1000), milliseconds=False)
                    if track.identifier and os.path.isfile(f'{track.identifier}') and self.bot.public_ip:
                        # track.uri = f'https://abdist.serveo.net/{quote(track.title)}'
                        track.uri = f'{self.bot.public_ip}/{quote(track.title)}'
                        # track.uri = f'https://perfect-pig-99.telebit.io/{quote(track.title)}'

                    formatted_queue += f'{i + loop_mode_adjustment}. [{track.title}]({track.uri}) - {track.requester} [{length}]\n'
                except Exception:
                    self.bot.logger.exception('')

            embed = self.quEmbed(formatted_current_track, formatted_queue, loop_mode)

            if qu_ctx:
                await self.embed_send(ctx=qu_ctx, embed_list=self.qu_embed_msg, embed=embed)

            await self.embed_edit(embed_list=self.qu_embed_msg, embed=embed)
