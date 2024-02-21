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

from errorHandler import print_text, TextColor, Ori

discord_token = os.getenv('DISCORD_TOKEN')
bot = discord.Bot()

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
            

# i am using this to let me know wheter the bot is playing music with an onboard led
# @tasks.loop(seconds=2)
# async def check_playing_status():
#     for vc in bot.voice_clients:
#         if vc.is_playing():
#             process = subprocess.Popen('echo 1 > /sys/class/leds/working/brightness', stdout=subprocess.PIPE, shell=True)
#         else:
#             process = subprocess.Popen('echo 0 > /sys/class/leds/working/brightness', stdout=subprocess.PIPE, shell=True)

# Event handler for bot ready
@bot.event
async def on_ready():
# reseting the leds
    # process = subprocess.Popen('echo 0 > /sys/class/leds/auxiliary/brightness', stdout=subprocess.PIPE, shell=True)
    # process = subprocess.Popen('echo 0 > /sys/class/leds/working/brightness', stdout=subprocess.PIPE, shell=True)
    print_text(Ori(), TextColor.CYAN)
    print_text(f'{bot.user.name}', TextColor.PURPLE) 
    print(' is ready! ^^')
    print('')
    global check_bot_status
    if not check_bot_status.is_running():
        check_bot_status.start()
    # global check_playing_status
    # if not check_playing_status.is_running():
    #     check_playing_status.start()

bot.load_extension('cogs.music')
bot.load_extension('cogs.wichteln')
bot.load_extension('cogs.minecraft')
bot.run(discord_token)
