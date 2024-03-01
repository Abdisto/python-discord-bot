#!/path/to/python3.10

import os
import sys
sys.path.append(sys.path[0]+"/cogs")
import subprocess
import time as t

import discord
from discord import option
from discord.ext import tasks

import asyncio

from errorHandler import print_text, TextColor, Ori, print_timestamp

discord_token = os.getenv('DISCORD_TOKEN')
bot = discord.Bot()

def load_cogs(directory):
    for foldername, subfolders, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.py') and filename != 'errorHandler.py':
                print_timestamp(filename, 'Trying to load in ')
                extension = os.path.join(foldername, filename).replace('.py', '').replace('/', '.')
                try:
                    bot.load_extension(extension)
                    print_timestamp(f'Successfully loaded extension: {extension}')
                except Exception as e:
                    print_timestamp(e, f'Failed to load extension {extension}. ', 1)

@tasks.loop(minutes=1)
async def check_bot_status():
    for vc in bot.voice_clients:
        if not vc.is_playing() and not vc.is_paused():
            if not hasattr(vc, 'inactive_since'):
                vc.inactive_since = t.time()
            elif t.time() - vc.inactive_since >= 300: # 5 minutes
                music_cog = bot.get_cog('Music')
                if music_cog:
                    music_cog.clear()
                await vc.disconnect()
        elif hasattr(vc, 'inactive_since'):
           del vc.inactive_since
        if len(vc.channel.members) == 1: # The bot is the only member in the channel
            music_cog = bot.get_cog('Music')
            if music_cog:
                music_cog.clear()
            await vc.disconnect()

# Event handler for bot ready
@bot.event
async def on_ready():
    print_text(Ori(), TextColor.CYAN)
    print_text(f'{bot.user.name}', TextColor.PURPLE) 
    print(' is ready! ^^')
    print('')
    global check_bot_status
    if not check_bot_status.is_running():
        check_bot_status.start()

load_cogs('cogs')
bot.run(discord_token)