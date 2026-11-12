#!/usr/bin/env python3.14

from discord.flags import Intents


import argparse
import os
import sys

sys.path.append(sys.path[0]+'/cogs')

import asyncio
import logging
import signal
import subprocess
import termios
import threading
import time as t

import discord

# from discord.errors import HTTPException, InteractionResponded, NotFound
from discord.ext import commands, tasks
from pomice import Node, NodePool, exceptions
from rich import print

# from helper.setupWizard import get_config
from BotClass import BotClass

intents: Intents = discord.Intents.default()
intents.presences = True
intents.members = True

first_connect = True
node_symbol = '[cyan]\U0000E0A0[/]'
inactivity_timer = 0
online_empty = 0
# logger = logging.getLogger('discord')
# logger.setLevel(logging.DEBUG)
bot = BotClass(intents=discord.Intents.all(), application_id=858821713122164787) # inject application ID
bot.logger.setLevel('INFO')
discord_token, lavalink_host, lavalink_port, lavalink_pass = os.getenv("DISCORD_BOT_TOKEN", None), os.getenv("LAVALINK_HOST", 'localhost'), int(os.getenv("LAVALINK_PORT", "2333")), os.getenv("LAVALINK_PASS", 'youshallnotpass')
bot.local_songs_path = os.getenv("SONG_PATH", None)
bot.public_ip = os.getenv("PUBLIC_IP", None)
shutting_down = False
fd = sys.stdin.fileno()
orig_attrs = termios.tcgetattr(fd)

async def connect_node():
    global first_connect
    if first_connect or not bot.node.is_connected:
        try:
            if bot.node is not None:
                first_connect = False
                bot.node = NodePool.get_node(identifier='MAIN')
            else:
                bot.node = await NodePool.create_node(
                    bot=bot,
                    host=lavalink_host,
                    port=int(lavalink_port),
                    password=lavalink_pass,
                    identifier='MAIN'
                )
        except Exception:
            bot.logger.exception('')

    message = f'{node_symbol} Node {"is connected!" if first_connect else "reconnected!"}'
    print(f'\n{message.center(38 if first_connect else 35)}\n')

@tasks.loop(seconds=10)
async def check_player_status():
    global inactivity_timer
    voice_client = bot.voice_clients[0] if bot.voice_clients else None
    if voice_client and not voice_client.is_playing:
        inactivity_timer += 10
        if inactivity_timer >= 300:
            bot.logger.info(bot.format('Bot already inactive for 5 minutes.'))
            await voice_client.disconnect()
    else:
        inactivity_timer = 0

@tasks.loop(seconds=30)
async def check_minecraft_status():
    for server_identifier, server in bot.servers.items():
        try:
            await server.get_status()
            await bot.presence()
        except Exception:
            # bot.logger.exception('')
            print()

@bot.event
async def on_ready() -> None:
    subprocess.run(['cat', './helper/Ori'])
    read_message = f'[medium_violet_red]{bot.user.name}[/]' + ' is ready! ^.^'
    print(f'{read_message.center(50)}')

    await bot.wait_until_ready()
    try:
        await bot.sync_commands()
#        bot.logger.info("Commands synced (on_ready).")
    except Exception:
        bot.logger.exception("Command sync failed on_ready")

    await connect_node()
    if not check_player_status.is_running():
        check_player_status.start()
    if not check_minecraft_status.is_running():
        check_minecraft_status.start()

@bot.event
async def on_resumed() -> None:
    if not check_player_status.is_running():
        check_player_status.start()
    if not check_minecraft_status.is_running():
        check_minecraft_status.start()

@bot.event
async def on_application_command(ctx: discord.ApplicationContext):
    global disabled_cogs
    try:
        #if disabled_cogs and str(ctx.command.module) or str(ctx.command.name)  in disabled_cogs:
        #    await ctx.respond('Cog is under maintenance.', delete_after=7,)
        #    return
        bot.logger.info(bot.format(ctx.author.name + '\n>> ' + ' '.join(map(str, ctx.selected_options)) if ctx.selected_options else ctx.author.name, f'Requested {ctx.command} command by: '))
        # if not ctx.interaction.response.is_done():
        #     await ctx.defer()
    except discord.InteractionResponded as e:
        bot.logger.info(bot.format(title=e))
    except discord.NotFound as e:
        bot.logger.error(bot.format(title=e, mode=1))
    except discord.HTTPException as e:
        bot.logger.error(bot.format(title=e, mode=1))
    except discord.InvalidData as e:
        bot.logger.error(bot.format(title=e, mode=1))

@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.ApplicationCommandInvokeError):
    bot.logger.error(bot.format(title=f'Exception thrown at {ctx.command}:\n', text=error, mode=1))
    # Removed since mishandling can cause leakage of sensitive information.
    # Especially since unloading a cog will not prevent this issue.
    # Unloaded cogs won't be saved after a reboot of the system. Might add
    # await ctx.respond(f'Exception thrown at {ctx.command}: {error}.', delete_after=7,)
    if isinstance(error.__cause__, discord.InteractionResponded):
        return
    bot_info = await bot.application_info()
    await bot_info.owner.send(f'Exception thrown at {ctx.command}: {error}')
    await ctx.respond(f'Error occured during {ctx.command} command.')

@bot.before_invoke
async def before_any_command(ctx: discord.ApplicationContext):
   if await bot.is_owner(ctx.author):
       return

   if(str(ctx.command.module) in disabled_cogs):
       await ctx.respond(f'The module **{ctx.command.module}** is under maintenance.', delete_after=7,)
       raise commands.CheckFailure(f'{ctx.command.module} is under maintenance.')
       return

   if(str(ctx.command.name) in disabled_cogs):
       await ctx.respond(f'The **{ctx.command.name}** command is under maintenance.', delete_after=7,)
       raise commands.CheckFailure(f'{ctx.command.name} is under maintenance.')
       return

   async def traverse_command(cur):
       if(cur != None):
           if str(cur) in disabled_cogs:
               if cur.parent:
                   await ctx.respond(f'The **{cur}** module is under maintenance.', delete_after=7,)
                   raise commands.CheckFailure(f'{cur} is under maintenance.')
           else:
               await traverse_command(cur.parent)
   await traverse_command(ctx.command)


# @bot.event
# async def on_interaction(interaction: discord.Interaction):
#     bot.logger.info(f"minimal: RAW INTERACTION id={interaction.id} type={interaction.type} data={interaction.data}")
#     await bot.process_application_commands(interaction)


async def cleanup():
    try:
        bot.stopTimes()
        voice_client = bot.voice_clients[0] if bot.voice_clients else None
        if voice_client is not None:
            await voice_client.disconnect()
    except Exception:
        bot.logger.exception('')

async def shutdown_bot():
    bot.logger.info('Cleaning up resources...')
    loop = asyncio.get_event_loop()
    task = loop.create_task(cleanup())
    await asyncio.wait_for(task, None)
    bot.logger.info('Cleanup done. Exiting...')
    asyncio.get_event_loop().stop()
    os._exit(0)
    # await bot.close()

def signal_handler(sig, frame):
    global shutting_down
    if not shutting_down:
        shutting_down = True
        termios.tcsetattr(fd, termios.TCSAFLUSH, orig_attrs)
        bot.logger.info('KeyboardInterrupt detected. Shutting down...')
        loop = asyncio.get_event_loop()
        loop.create_task(shutdown_bot())

def cache_toggle():
    bot.cache.cache_isactive = not bot.cache.cache_isactive
    bot.logger.info(f'Cache active: {bot.cache.cache_isactive}')

def get_char():
    try:
        new_attrs = orig_attrs[:]
        new_attrs[3] &= ~(termios.ECHO | termios.ICANON)
        termios.tcsetattr(fd, termios.TCSANOW, new_attrs)

        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSAFLUSH, orig_attrs)

    return ch

async def input_handler():
    while True:
        # text = input()
        text = get_char()
        braille = ['⠒','⠰','⠤','⠆']
        wait = 3
        match text:
            case 'q':
                await cleanup()

                message = "Exiting the program "
                print(message, end="\r")
                for i in range(wait*4):
                    # message += "."
                    timeLeft = (wait*4-i)//4
                    # zeros = str(len(str(wait)))
                    print(f'{message}{braille[i%len(braille)]} {"0" + str(timeLeft) if timeLeft < 10 else timeLeft}', end="\r")
                    # print(f'{message}', end="\r")
                    t.sleep(0.25)
                print('\nBot ded!')

                asyncio.get_event_loop().stop()
                os._exit(0)

            case 'R':
                await cleanup()

                message = 'Restarting the program '
                print(message, end="\r")
                for i in range(wait*4):
                    # message += '.'
                    timeLeft = (wait*4-i)//4
                    # zeros = str(len(str(wait)))
                    print(f'{message}{braille[i%len(braille)]} {"0" + str(timeLeft) if timeLeft < 10 else timeLeft}', end="\r")
                    t.sleep(0.25)

                print(sys.argv)
                os.execv(sys.executable, [sys.executable] + sys.argv)

            case 'r':
                await cleanup()
                bot.filtered_cogs('unload')
                bot.filtered_cogs('load')
                bot.logger.info('Finished soft restart.')
                continue

            case 'd':
                logging.getLogger('discord').setLevel('DEBUG')
                bot.logger.setLevel('DEBUG')
                bot.logger.info('Set logger to DEBUG')

            case 'i':
                logging.getLogger('discord').setLevel('INFO')
                bot.logger.setLevel('INFO')
                bot.logger.info('Set logger to INFO')

            case 'w':
                logging.getLogger('discord').setLevel('WARN')
                bot.logger.setLevel('WARN')
                bot.logger.info('Set logger to WARN')

            case 'c':
                cache_toggle()

            case 'h':
                print(bot.helptext())
                await input_handler()

def run_input_handler():
    asyncio.run(input_handler())

async def run_bot():
    await bot.initialize()
    bot.filtered_cogs('load')
    await bot.start(discord_token)

def main():
    global disabled_cogs
    parser = argparse.ArgumentParser(description ='Starting the bot')

    parser.add_argument('-c', action='store_true', help='disable the cache writes')
    parser.add_argument('-cogs', metavar='I', type=str, nargs='+', help='disables the defined cogs')
    args = parser.parse_args()

    if args.c:
        cache_toggle()
    disabled_cogs = args.cogs

    os.system('clear')

    bot.logger.info(bot.format('Getting Env Vars for Bot...'))
    try:
        if discord_token == None:
            raise Exception('No discord token set, please use secretspec')
            return
        bot.logger.info(bot.format('Success\n', 'Getting Env Vars: ', mode=2))
    except Exception:
        bot.logger.exception('')

    threading.Thread(target=run_input_handler, daemon=True).start()

    loop = asyncio.get_event_loop()

    signal.signal(signal.SIGINT, signal_handler)

    try:
        loop.run_until_complete(run_bot())
    # except KeyboardInterrupt:
    #     loop.run_until_complete(shutdown_bot())
    finally:
        bot.logger.info('Cleaning up tasks and closing the loop.')
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
#    bot.run(discord_token)

if __name__ == '__main__':
    main()

#discord_token, lavalink_host, lavalink_port, lavalink_pass, public_ip, local_songs_path = get_config()
#bot.filtered_cogs('load')
#bot.run(discord_token)
