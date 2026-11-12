import asyncio
import base64
import fcntl
import os
import pickle
import re
from typing import Any, LiteralString

import anyio
import discord
import paramiko
from discord.commands import Option
from discord.commands.core import SlashCommandGroup
from discord.embeds import Embed
from discord.ext import commands
from discord.file import File
from mcstatus.responses._raw import RawJavaResponseMotd
from mcstatus.responses.java import JavaStatusResponse
from mcstatus.responses.query import QueryResponse
from mcstatus.server import JavaServer
from paramiko.client import SSHClient
from paramiko.transport import Transport
from scp import SCPClient

local_path = '/tmp/server_action'
remote_path = '/home/minecraft2/bot_server_handler/server_action'

directory: str = os.path.dirname(__file__)
file_path: str = os.path.join(directory, 'servers')

class Server:
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.ip: str
        self.port = 22
        self.user: str | None = None
        self.key_file: str | None = None
        self.identifier: str = ''
        self.server_type: None = None
        self.status: JavaStatusResponse
        self.timer: float = 0.0
        self.online: bool = False

    def __str__(self) -> str:
        return self.identifier

    def add_server(self, ip, port, user, key_file, identifier, server_type) -> None:
        self.ip = ip
        self.port: int = port
        self.user = user
        self.key_file = key_file
        self.identifier = identifier
        self.server_type = server_type

    def save_obj(self) -> None:
        servers: dict[Any, Any] = {}

        try:
            if os.path.exists(path = file_path) and os.path.getsize(filename = file_path) > 0:
                with open(file = file_path, mode = 'rb') as f:
                    fcntl.flock(f, fcntl.LOCK_SH)
                    servers = pickle.load(file = f)
                    fcntl.flock(f, fcntl.LOCK_UN)
        except FileNotFoundError:
            print('File not found')
        except pickle.PickleError as e:
            print(f'Pickle {e}')
        except OSError as error:
            print(f"Some other error occurred: {error}")

        servers[self.identifier] = self
        temp_file: str = f'{file_path}.tmp'

        try:
            with open(file = temp_file, mode = 'wb') as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                pickle.dump(obj = servers, file = f)
                f.flush()
                fcntl.flock(f, fcntl.LOCK_UN)
        except FileNotFoundError:
            print('File not found')
        except PermissionError:
            print('Operation not permitted.')
        except OSError as error:
            print(f'Some other error occurred: {error}')

        try:
            os.replace(src = temp_file, dst = file_path)
        except IsADirectoryError:
            print('Source is a file, but destination is a directory.')
        except NotADirectoryError:
            print('Source is a directory but destination is a file.')
        except PermissionError:
            print('Operation not permitted.')
        except OSError as error:
            print(f'Some other error occurred: {error}')

    def create_ssh_client(self) -> SSHClient:
        client: SSHClient = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(policy=paramiko.AutoAddPolicy())
        client.connect(
            hostname = self.ip,
            port = self.port,
            username = self.user,
            key_filename = self.key_file
        )
        return client

    def transfer_file(self, command) -> None:
        with open(file='/tmp/server_action', mode='w') as file:
            file.write(f'{command}:{self.identifier}')
        ssh_client:SSHClient = self.create_ssh_client()
        transport: Transport | None = ssh_client.get_transport()
        if transport is None:
            raise ConnectionError('SSH Transport is not available')
        with SCPClient(transport = transport) as scp:
            scp.put(files = local_path, remote_path = remote_path)
        ssh_client.close()

    def generate_embed(self, logger, format) -> tuple[Embed, File]:
        motd = 'n.A.'
        attrs: dict[str, Any] = self.get_attrs()

        embed: Embed = discord.Embed(
            title=f'{self.ip}',
            description=motd,
            color=discord.Color.red() if self.status is None else discord.Color.green()
        )

        for key, value in attrs.items():
            if key not in ['status', 'ip', 'timer', 'online', 'port']:
                value: str = str(value)
                embed.add_field(
                    name=key.replace('_', '').title(),
                    value=value[:1021] + '...' if len(value) > 1024 else value,
                    inline=True
                )
            if key == 'timer':
                embed.add_field(
                    name=key.replace('_', '').title(),
                    value=f'{value}/30.0',
                    inline=True
                )
            if key == 'port':
                embed.add_field(
                    name=f'{key.title()} <SSH>',
                    value=value,
                    inline=True
                )

        default_img: File = discord.File(fp='./src/default.png', filename='default.png')

        return embed, default_img

    async def get_status(self, mode) -> JavaStatusResponse | None:
        return None

    def get_attrs(self)  -> dict[str, Any]:
        return self.__dict__

class Minecraft(Server):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def get_status(self, mode: int = 0) -> JavaStatusResponse | None:
        server: JavaServer = await JavaServer.async_lookup(
            address=f'{self.ip}:25565'
        )

        try:
            query: QueryResponse = await server.async_query()

            if query.players.list:
                self.timer = 0.0
            else:
                self.status = await server.async_status()

                if not self.status.players.sample:
                    self.timer += 0.5
                else:
                    self.timer = 0.0

        except TimeoutError:
            self.status = await server.async_status()

            if not self.status.players.sample:
                self.timer += 0.5
            else:
                self.timer = 0.0

        if self.timer >= 30.0:
            await asyncio.to_thread(self.transfer_file, 'stop')
            self.timer = 0.0

        return self.status


        # Add a method that checks if this is the correct server through status infos
        # Hard if multiple servers reside on the same port and ip need to check info
        # of servers and save them to the appropriate one. CAN'T BE DONE AUTOMATICALLY
        # HAS TO BE SET MANUALLY UNFORTUNATELLY


    def generate_embed(self, logger, format) -> tuple[Embed, File]:
        motd = 'n.A.'
        output_path = f'{directory}/{self.identifier}.png'
        attrs = self.get_attrs()

        if self.status is not None:
            try:
                motd_raw: RawJavaResponseMotd = self.status.motd.raw

                if isinstance(motd_raw, dict):
                    motd = motd_raw.get('text', '')
                else:
                    motd = motd_raw
                if not isinstance(motd, str):
                    motd = str(motd)
                motd = re.sub(r'§.', '', motd)

            except Exception:
                # logger.exception('Failed to parse MOTD')
                print()

            try:
                picture: str | None = self.status.raw.get('favicon')
                if picture and picture.startswith('data:image'):
                    picture = picture.split(sep = ',')[1]
                    image_data: bytes = base64.b64decode(s = picture)
                    with open(file = output_path, mode = 'wb') as file:
                        file.write(image_data)
                    logger.info(format(f"Image saved as {output_path}"))
            except Exception:
                # logger.exception('')
                print()

        embed: Embed = discord.Embed(
            title=f'{self.ip}',
            description=motd,
            color=discord.Color.red() if self.status is None else discord.Color.green()
        )

        server_img: File
        if os.path.isfile(path = output_path):
            try:
                with open(file = output_path, mode = 'rb') as f:
                    server_img = discord.File(fp = f, filename=f'{self.identifier}.png')
                    embed.set_thumbnail(url=f'attachment://{self.identifier}.png')
            except Exception:
                # logger.exception('')
                server_img = discord.File(fp = f'{os.path.dirname(output_path)}/default.png', filename = 'default.png')
                embed.set_thumbnail(url='attachment://default.png')
        else:
            server_img = discord.File(fp = f'{os.path.dirname(output_path)}/default.png', filename = 'default.png')
            embed.set_thumbnail(url='attachment://default.png')

        for key, value in attrs.items():
            if key not in ['status', 'ip', 'timer', 'online', 'port']:
                value: str = str(value)
                embed.add_field(
                    name=key.replace('_', '').title(),
                    value=value[:1021] + '...' if len(value) > 1024 else value,
                    inline=True
                )
            if key == 'timer':
                embed.add_field(
                    name=key.replace('_', '').title(),
                    value=f'{value}/30.0',
                    inline=True
                )
            if key == 'port':
                embed.add_field(
                    name=f'{key.title()} <SSH>',
                    value=value,
                    inline=True
                )

        return embed, server_img

def load_servers(logger, format) -> Any | dict[Any, Any]:
    try:
        if os.path.exists(path = file_path) and os.path.getsize(filename = file_path) > 0:
            with open(file = file_path, mode = 'rb') as f:
                servers = pickle.load(file = f)
                return servers
        else:
            return {}
    except pickle.UnpicklingError as e:
        logger.error(format(title=e, mode=1))
        return {}
    except Exception:
        logger.exception('')
        return {}


class ServerClass(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.servers = load_servers(self.bot.logger, self.bot.format)

    async def serverList(self, ctx: discord.AutocompleteContext):
        if ctx.interaction.response.is_done():
            return

        server_data: Any | None = None

        try:
            async with await anyio.open_file(file = file_path, mode = 'rb') as f:
                contents = await f.read()
                server_data = pickle.loads(contents)
        except FileNotFoundError as e:
            self.bot.logger.error(self.bot.format(title=e, mode=1))
        except pickle.UnpicklingError as e:
            self.bot.logger.error(self.bot.format(title=e, mode=1))
        except Exception:
            self.bot.logger.exception('')

        if server_data:
            server_identifiers = server_data.keys()

            user_input: str = ctx.value.lower()
            matches: list[Any] = [identifier for identifier in server_identifiers if user_input in identifier.lower()]

            return matches


    server: SlashCommandGroup = discord.SlashCommandGroup(name = 'server', description = 'Controlling multiple servers')

    @server.command(
        name='command',
        description='Commanding the specified server',
    )
    @commands.check_any(
        commands.is_owner(), # pyright: ignore[reportArgumentType]
        commands.has_any_role(541986455619239938, 753661263195668591)  # pyright: ignore[reportArgumentType]
    )
    async def server_command(
        self,
        ctx,
        specifiedserver: Option(str, autocomplete = serverList),  # pyright: ignore[reportInvalidTypeForm]
        action: Option(  # pyright: ignore[reportInvalidTypeForm]
            name='action',
            description='action',
            type=3,
            choices=[
                'start',
                'stop',
                'restart',
                '?',
                'fallback'
            ]
        ),
    ) -> None:
        server_instance: Any
        # self.bot.logger.info(self.bot.format(action, 'Provided action: ')
        if action.lower() in ['start', 'restart', 'stop', 'fallback']:
            try:
                server_instance = self.bot.servers.get(specifiedserver.lower())
                if not server_instance:
                    await ctx.respond(f"Server '{specifiedserver}' not found.", delete_after=7)
                    return
                if server_instance:
                    server_instance.transfer_file(action)
                if action == 'stop':
                    await ctx.respond('Server is stopping.', delete_after=7,)
                else:
                    await ctx.respond(f'Server is {action}ing.', delete_after=7,)

                self.bot.logger.info(self.bot.format(f'{action.capitalize()} script is being run.'))

            except Exception:
                await ctx.respond(f'Failed {action}ing server.', delete_after=7,)
                self.bot.logger.exception('')

        elif action.lower() == '?':
            server_instance = self.bot.servers.get(specifiedserver.lower())
            status: Any = server_instance.get_status()
            if status is None:
                await ctx.respond('Status: offline')
            else:
                await ctx.respond(f'Status: The server has {status.players.online} player(s) online and replied in {status.latency} ms. \
                                    Shutting down in {30.0 - server_instance.timer} minutes.', delete_after=25)
                try:
                    if status.players.sample:
                        player_list: LiteralString = ', '.join([player.name for player in status.players.sample])
                        await ctx.send(f'Players online: {player_list}', delete_after=25)
                except Exception:
                    self.bot.logger.exception('')
            # status = server_instance.get_status(1)
            # print(status)
        else:
            await ctx.respond('Invalid action...', delete_after=7,)

    @server.command(
        name='add',
        description='Adding servers to the list of servers.',
        options=[
            Option(name='ip', description='IP address', type=str),
            Option(name='port', description='Port number', type=int),
            Option(name='user', description='User', type=str),
            Option(name='key_file', description='Path to key file', type=str),
            Option(name='identifier', description='Identifier', type=str),
            Option(name='server_type', description='Server type', type=str, default='minecraft'),
        ]
    )
    @commands.check_any(
        commands.is_owner(),  # pyright: ignore[reportArgumentType]
        commands.has_any_role(541986455619239938, 753661263195668591)  # pyright: ignore[reportArgumentType]
    )
    async def server_create(self, ctx, ip, port, user, key_file, identifier, server_type):
        try:
            if server_type == 'minecraft':
                server = Minecraft()
            else:
                server = Server()
            server.add_server(ip, port, user, key_file, identifier, server_type)
            server.save_obj()
            await ctx.respond('Server created successfully.', delete_after=5)
        except Exception:
            # self.bot.logger.exception('')
            print()


    @server.command(
        name='get',
        description='Get all the attributes of specified server.',
    )
    @commands.check_any(
        commands.is_owner(),  # pyright: ignore[reportArgumentType]
        commands.has_any_role(541986455619239938, 753661263195668591)  # pyright: ignore[reportArgumentType]
    )
    async def server_get(self, ctx, specifiedserver: discord.Option(str, autocomplete = serverList)) -> None:  # pyright: ignore[reportInvalidTypeForm]
        server_instance: Any = self.bot.servers.get(specifiedserver.lower())

        embed, server_img = server_instance.generate_embed(self.bot.logger, self.bot.format)

        await ctx.respond(embed=embed, file=server_img, delete_after=120)

def setup(bot) -> None:
    bot.add_cog(ServerClass(bot))
