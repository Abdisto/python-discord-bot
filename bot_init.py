#!/usr/bin/env python3.10

import os
import sys
sys.path.append(sys.path[0]+'/cogs')
import asyncio
import subprocess
import time as t

import discord
from discord.ext import commands, tasks

from pomice import Node, NodePool

from errorHandler import print_text, TextColor, Ori, print_timestamp
from setup_wizard import get_config
from minecraft.minecraft import get_status, transfer_file

bot = discord.Bot()
first_connect = True
node = None
node_symbol = print_text('\U0000E0A0' , TextColor.CYAN)
inactivity_timer = 0
online_empty = 0

def load_cogs():
    for foldername, subfolders, filenames in os.walk('cogs'):
        for filename in filenames:
            if filename.endswith('.py') and filename not in ['errorHandler.py', 'player.py', 'cache.py']:
                print_timestamp(filename, 'Trying to load in ')
                extension = os.path.join(foldername, filename).replace('.py', '').replace('/', '.')
                try:
                    bot.load_extension(extension)
                    print_timestamp(extension, f'Successfully loaded extension: ', 2)
                except Exception as e:
                    print_timestamp(e, f'Failed to load extension {extension}: ', 1)

def load_config() -> None:
    try:
        global discord_token, lavalink_host, lavalink_port, lavalink_pass
        print_timestamp('Reading from config file...')
        discord_token, lavalink_host, lavalink_port, lavalink_pass = get_config()
        if discord_token == None:
            return print_timestamp('', 'No discord token set, please use setup_wizard.py', 1)
        print_timestamp('Successful\n')
    except Exception as e:
        return print_timestamp(e, 'Error occurred while reading the config:', 1)

@tasks.loop(minutes=1)
async def check_node_status():
    global first_connect
    global node
    try:
        if first_connect or not node.is_connected:
            if node == None:
                node = await NodePool.create_node(bot=bot, host=lavalink_host, port=int(lavalink_port), password=lavalink_pass, identifier='MAIN') # Da muss ich mir noch was überlegen (I mean it's working außer der message)
            else:
                await NodePool.get_node(identifier='MAIN')
            message = f"{node_symbol} Node {'is connected!' if first_connect else 'reconnected!'}".center(38)
            print(f'{message}\n')
            first_connect = False
    except Exception as e:
        print_timestamp(e, f'Error in check_node_status: ', 1)

@tasks.loop(seconds=10)
async def check_inactivity():
    global inactivity_timer
    voice_client = bot.voice_clients[0] if bot.voice_clients else None
    if voice_client is not None:
        if voice_client.is_playing:
            inactivity_timer = 0
        else:
            inactivity_timer += 10
            if inactivity_timer >= 300:
                await voice_client.disconnect()
                await bot.change_presence(activity=discord.Activity(
                    type=discord.ActivityType.playing,
                    name=f'Server-status: {self.bot.mcstatus}')
                )
                print_timestamp('Disconnected due to inactivity.')
    else:
        inactivity_timer = 0

@tasks.loop(minutes=1)
async def check_minecraft_status():
    global online_empty
    status = get_status()
    if status.online == False:
        bot.mcstatus = 'offline'
        print('offline')

    elif status.online == True:
        bot.mcstatus = status.players.online 
        print(status.players.online)
        if status.players.online > 0:
            online_empty = 0
        else:
            online_empty += 1
            if online_empty >= 60:
                try:
                    with open('/tmp/server_action', 'w') as file:
                        file.write('stop')
                    transfer_file()

                except Exception as e:
                    print(e)

    else:
        print('something went wrong')

@bot.event
async def on_ready() -> None:
    Ori()
    read_message = print_text(f'{bot.user.name}', TextColor.PURPLE) + ' is ready! ^^'
    print(f'{read_message.center(38)}\n')

    if not check_node_status.is_running():
        await bot.wait_until_ready()
        check_node_status.start()

    if not check_inactivity.is_running():
        check_inactivity.start()

    if not check_minecraft_status.is_running():
        check_minecraft_status.start()

def main():
    load_config()
    load_cogs()
    bot.run(discord_token)
    # except KeyboardInterrupt:
    #     pass
    # except Exception as e:
    #     print_timestamp(e, f'An error occurred: ', 1)

if __name__ == '__main__':
    main()