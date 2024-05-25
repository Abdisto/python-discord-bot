import os
import discord
from discord.ext import commands
from discord.ext.commands import CheckFailure
from discord.commands import Option
import asyncio
from errorHandler import print_timestamp
import paramiko
from scp import SCPClient

from python_mcstatus import JavaStatusResponse, statusJava


local_path = '/tmp/server_action'
remote_path = 'server_path'

def get_status():
    host = 'server_ip'
    port = <port>
    query = True

    return statusJava(host, port, query)

def create_ssh_client():
    server = 'server_ip'
    port = <port>
    user = 'user'
    key_file = 'path to id_rsa'
    password = 'optional when not pub/priv key'

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, username=user, key_filename=key_file)
    return client

def transfer_file():
    ssh_client = create_ssh_client()
    with SCPClient(ssh_client.get_transport()) as scp:
        scp.put(local_path, remote_path)
    ssh_client.close()

class Minecraft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name='server',
        description='Controlling the minecraft server',
        options=[
            Option(
                name='action',
                description='action',
                type=3,
                choices=[
                    'start',
                    'stop',
                    'restart',
                    '?'
                ]
            )
        ]
    )
    @commands.has_any_role('Roles that', 'can execute command')
    async def server(self, ctx, action: str):
        print_timestamp(ctx.author.name, 'Requested to start the minecraft server: ')
        await ctx.defer()
        print_timestamp(action, 'Provided action: ')

        if action.lower() in ['start', 'restart', 'stop']:
            try:
                with open(local_path, 'w') as file:
                    file.write(action)

                transfer_file()

                await ctx.respond(f'Server is {action}ing.', delete_after=7,)
                print_timestamp(f'{action.capitalize()} script is being run.')

            except Exception as e:
                await ctx.respond(f'Failed {action}ing server.', delete_after=7,)
                print_timestamp(e, 'An error occurred:', 1)

        elif action.lower() == '?':            
            await ctx.respond(f'Status: {get_status()}.', delete_after=7,)
        else:
            await ctx.respond('Invalid action...', delete_after=7,)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, CheckFailure):
            await ctx.respond('Sorry, you do not have permission to use this command.', delete_after=7,)
        elif isinstance(error, commands.MissingRole):
            await ctx.respond('You do not have the required role to perform this action.', delete_after=7,)
        else:
            print(f"Unhandled error: {error}")
            await ctx.respond('An unexpected error occurred. Please try again later.', delete_after=7,)

def setup(bot):
    bot.add_cog(Minecraft(bot))