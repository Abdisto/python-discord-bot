import asyncio
import logging
import os
import textwrap
from asyncio.locks import Lock
from datetime import datetime, timedelta
from typing import Any, LiteralString

import asyncpg
import discord
from asyncpg.pool import Pool
from rich.logging import RichHandler
from rich.panel import Panel

from cache import Cache
from cogs.music.player import Player

FORMAT = '%(message)s'
logging.basicConfig(
    level = 'INFO',
    format = FORMAT,
    datefmt = '[%X]',
    handlers = [RichHandler(rich_tracebacks = True, markup = True)],
    force = True
)

class BotClass(discord.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.current_activity: str | LiteralString | None = None
        self.track_title: str | None = None
        self.farmers = []
        self.servers = {}
        self.players: dict[int, Player] = {}
        self.player_locks: dict[int, asyncio.Lock] = {}

        self.logger = logging.getLogger(__name__)

        self.db: Pool | None = None
        self.cache: Cache | None = None

        self.node = None
        self.public_ip: str | None = None
        self.local_songs_path: str | None = None

        logging.getLogger(name = 'discord.gateway').setLevel(logging.CRITICAL)
        logging.getLogger(name = 'discord.client').setLevel(logging.CRITICAL)

    async def initialize(self):
        self.db = await asyncpg.create_pool(
            user="discordBot",
            database="discordQuery",
            min_size=1,
            max_size=10,
            command_timeout=1.0,
        )
        self.logger.info(msg = "PostgreSQL Database pool created")
        async with self.db.acquire() as conn:
            result: Any = await conn.execute('''
                CREATE TABLE IF NOT EXISTS tracks(
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    weight INTEGER
                )
            ''')
            if result == "CREATE TABLE":
                self.logger.info(msg = "PostgreSQL Table created")

        self.cache = Cache(self.db, self.logger)
        self.logger.info(msg = "Cache initialized")
        # inspect(self.cache)

    def get_player_lock(self, guild_id: int) -> asyncio.Lock:
        lock: Lock | None = self.player_locks.get(guild_id)

        if lock is None:
            lock = asyncio.Lock()
            self.player_locks[guild_id] = lock

        return lock

    def cleanup_logs(self, logs_dir) -> None:
        now: datetime = datetime.now()
        for filename in os.listdir(logs_dir):
            file_path: Any = os.path.join(logs_dir, filename)
            if os.path.isfile(path = file_path):
                file_mod_time: datetime = datetime.fromtimestamp(timestamp = os.path.getmtime(filename = file_path))
                if now - file_mod_time > timedelta(days=10):
                    os.remove(path = file_path)
                    print(f'Deleted old log file: {filename}')

    def log_error(self, error_message) -> None:
        logs_dir: str = os.path.join(os.getcwd(), 'logs')
        if not os.path.exists(path = logs_dir):
            os.makedirs(name = logs_dir)

        today: str = datetime.now().strftime(format = '%d.%m.%Y')
        log_filename: str = f'error_{today}.log'
        log_filepath: str = os.path.join(logs_dir, log_filename)

        with open(file = log_filepath, mode = 'a') as log_file:
            log_file.write(f'[{datetime.now().strftime(format = "%H:%M:%S")}] - {error_message}\n')

        self.cleanup_logs(logs_dir)

    async def status_light(self, mode) -> None:
        if mode == 1:
            for _ in range(3):
                await asyncio.create_subprocess_shell('echo 1 > /sys/class/leds/auxiliary/brightness')
                await asyncio.sleep(1)
                await asyncio.create_subprocess_shell('echo 0 > /sys/class/leds/auxiliary/brightness')
                await asyncio.sleep(1)
        if mode == 2:
            await asyncio.create_subprocess_shell('echo 1 > /sys/class/leds/working/brightness')
            await asyncio.sleep(1)
            await asyncio.create_subprocess_shell('echo 0 > /sys/class/leds/working/brightness')

    def format(self, text='', title='', mode=0, uri='') -> str:
        if mode == 0: # plain text with possible title
            return f'{title}[yellow]{text}[/yellow]'
        elif mode == 1: # error
            self.log_error(error_message = str(text))
            # asyncio.create_task(self.status_light(mode))
            return f'[red]{title}[/red]{text}'
        elif mode == 2: # success
            #asyncio.create_task(self.status_light(mode))
            return f'[green]{title}[/green]{text}'
        elif mode == 3:
            hypertext: str = f'[link={uri}]{text}[/link]'
            return f'{title}[yellow]{hypertext}[/yellow]'
        else:
            return ''

    async def presence(self, track_title='NO_CHANGE') -> None:
        if track_title != 'NO_CHANGE':
            self.track_title = track_title

        status_strings: list[Any] = []
        for identifier, server in self.servers.items():
            if not server:
                continue
            status: Any = await server.get_status()
            if status and getattr(status, "players", None) and getattr(status.players, "online", None) is not None:
                status_strings.append(f"{identifier}: {status.players.online}")

        joined_statuses: LiteralString = ', '.join(status_strings)
        new_activity: str | LiteralString | None
        if self.track_title and joined_statuses:
            new_activity = f"{self.track_title} - {joined_statuses}"
        elif self.track_title:
            new_activity = f"{self.track_title}"
        else:
            new_activity = joined_statuses  # may be "" if no statuses

        if new_activity != self.current_activity:
            self.current_activity = new_activity
            if not self.current_activity:
                await self.change_presence(activity=None)
            else:
                await self.change_presence(activity=discord.Activity(
                    type=discord.ActivityType.playing,
                    name=self.current_activity))


    def filtered_cogs(self, mode) -> None:
        for foldername, subfolders, filenames in os.walk(top = 'cogs'):
            for filename in filenames:
                if filename.endswith('.py') and filename not in [
                    'errorHandler.py',
                    'player.py',
                    'cache.py',
                    'mojang_api.py',
                    'emoji.py'
                ]:
                    self.logger.info(msg = self.format(text = filename, title = f'Trying to {mode} '))
                    extension: str = os.path.join(foldername, filename).replace('.py', '').replace('/', '.')
                    try:
                        if mode == 'load':
                            self.load_extension(name = extension)
                        elif mode == 'unload':
                            self.unload_extension(name = extension)
                        else:
                            self.logger.error(msg = self.format(text = 'Incorrect mode parsed.'))
                            return
                        self.logger.info(msg = self.format(text = extension, title = f'Successfully {mode}ed extension: ', mode = 2))
                    except Exception:
                        self.logger.exception(msg = '')
        print()

    def updateTimes(self) -> None:
        for farmer in self.farmers:
            farmer.stopTimer()
            # t.sleep(2)
            farmer.startTimer()

    def stopTimes(self) -> None:
        for farmer in self.farmers:
            print(f'{[farmer.name for farmer in self.farmers]}')
            farmer.stopTimer()
            # Farmers.remove(farmer)

    def helptext(self) -> Panel | None:
        mappings: list[list[str]] = [["DEBUG", "green"], ["INFO", "blue"], ["WARNING", "red"]]
        logLevel: str | None = None
        for mapping in mappings:
            if str(logging.getLevelName(self.logger.level)) == mapping[0]:
                logLevel = (f"[{mapping[1]}]{mapping[0]}[/{mapping[1]}]")
        if not logLevel:
            logLevel = (f"[bright_black]{logging.getLevelName(self.logger.level)}[/bright_black]")

        if logLevel:
            message: str = textwrap.dedent(text = rf'''
                [medium_violet_red]q[/medium_violet_red] = Quit
                [medium_violet_red]r[/medium_violet_red] = soft restart
                [medium_violet_red]R[/medium_violet_red] = Hard restart

                [medium_violet_red]i[/medium_violet_red] = Set logger to [blue]INFO[/blue]                            >> \[logger: [blue]{logLevel}[/blue]]
                [medium_violet_red]d[/medium_violet_red] = Set logger to [green]DEBUG[/green]                           >>
                [medium_violet_red]w[/medium_violet_red] = Set logger to [red]WARNING[/red]                         >>
                [medium_violet_red]c[/medium_violet_red] = cache<toggle> (Don't/append changes to cache) >> \[cache: {'[green]active[/green]' if self.cache and self.cache.cache_isactive else '[red]inactive[/red]'}]
            ''')

            return Panel(renderable = f'{message}', title = 'Help', border_style = 'medium_violet_red', expand = True, subtitle = 'Help', highlight = True)
