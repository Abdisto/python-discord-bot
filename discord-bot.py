import os
import discord
from discord.ext import tasks
from discord import command 
from discord.commands import Option
from datetime import datetime
import yt_dlp
import asyncio
import subprocess
import json

def run_node_script(script_path, playlist_url):
    try:
        result = subprocess.run(['node', script_path, playlist_url], capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print('Error:', result.stderr)
            return []
    except Exception as e:
        print('Exception:', e)
        return []

class TextColor:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
# Function to print colored text
def print_colored_text(text, color):
    print(f"{color}{text}{TextColor.RESET}", end='')

def print_timestamp(text):
    date = datetime.now().strftime('%d.%m.%y')
    time = datetime.now().strftime('%H:%M')
    print(f"[{TextColor.RED}{date}{TextColor.RESET}| {TextColor.CYAN}{time}{TextColor.RESET}] {text}{TextColor.RESET}\n", end='')

def print_timestamp_ext(text, extend):
    date = datetime.now().strftime('%d.%m.%y')
    time = datetime.now().strftime('%H:%M')
    print(f"[{TextColor.RED}{date}{TextColor.RESET}| {TextColor.CYAN}{time}{TextColor.RESET}] {text}{TextColor.RESET}{TextColor.RED}{extend}{TextColor.RESET}\n", end='')

@tasks.loop(minutes=10)  # Run this task every 10 minutes
async def check_alone_status():
    for vc in bot.voice_clients:
        if len(vc.channel.members) == 1:  # The bot is the only member in the channel
            await vc.disconnect()

bot = discord.Bot()
song_queue = []
song_names = []
loop_mode = 0
ydlp_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extractaudio': True,
    'yes_playlist': True,
    'ignore_errors': True,
    'progress': True,
    'skip_download': True,
}

async def join_channel(ctx):
    if ctx.voice_client is not None and ctx.voice_client.is_connected():
        return ctx.voice_client
    channel = ctx.author.voice.channel
    if channel:
        voice_channel = await channel.connect()
        # Clear the queue and song names when joining a new channel
        song_queue.clear()
        song_names.clear()
        return voice_channel
    else:
        await ctx.send("You are not in a voice channel.")
        print_timestamp("Person requesting music playback is not in a voice channel.")
        return None

async def fetch_songs(ctx, url):
    print_timestamp("Fetching songs")
    try:
        result = subprocess.run(['node', 'discord-bot/getVideoUrls.js', url], capture_output=True, text=True)
        if result.returncode == 0:
            videos = json.loads(result.stdout)
            for video in videos:
                song_queue.append(video['url'])
                song_names.append(video['name'])  # Add the song name to the list
                print_timestamp(f"Added to queue: {TextColor.RED}{video['name']}{TextColor.RESET} - {video['url']}")
            print_timestamp("Finished fetching song/s.")
            await ctx.followup.send("Added song/s to the queue.")
        else:
            print_timestamp_ext('Error:', result.stderr)
    except Exception as e:
        print_timestamp_ext('Exception:', e)

def after_playing(ctx, error):
    if error:
        print_timestamp_ext("An error occurred while playing: ", error)
        loop = bot.loop
        loop.create_task(ctx.send(f"An error occurred while playing: {error}"))
                
    print_timestamp("Audio has finished playing.")
    loop = bot.loop
    if loop_mode == 1:
        # Loop the current song
        loop.create_task(stream_music(ctx, current_song))
    elif loop_mode == 2 and song_queue:
        # Loop the whole queue
        song_queue.append(current_song)
        loop.create_task(play_next(ctx))
    elif song_queue:
        # No loop, play the next song
        loop.create_task(play_next(ctx))

# Function to stream music
async def stream_music(ctx, url):
    try:    
        with yt_dlp.YoutubeDL(ydlp_opts) as ydlp:
            info = ydlp.extract_info(url, download=False)

        voice_channel = await join_channel(ctx)
        print_timestamp_ext("Streaming audio from: ", info['title'])

        options = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 60"
        voice_channel.play(discord.FFmpegPCMAudio(info['url'], before_options=options), after=lambda e: after_playing(ctx, e))
    except Exception as e:
        print_timestamp_ext("An error occurred while streaming: ", e)
        await ctx.send(f"An error occurred while streaming: {e}")

# Function to play the next song in the queue
async def play_next(ctx):
    # Wait for songs to be added to the queue
    while not song_queue:
        await asyncio.sleep(1)

    # Play the next song in the queue
    url = song_queue.pop(0)
    await stream_music(ctx, url)

# Define the "play" command
@bot.slash_command(name="play", description="Playing music.")
async def play(ctx, url: str):
    print_timestamp_ext("Requested play command by: ", ctx.author.name)
    if not ctx.author.voice:
        await ctx.send("You are not in a voice channel!")
        return

    await ctx.defer()

    voice_client = ctx.voice_client
    if voice_client is None:
        voice_client = await join_channel(ctx)

    await fetch_songs(ctx, url)

    if not voice_client.is_playing():
        while not song_queue:
            await asyncio.sleep(1)
        await play_next(ctx)

@bot.slash_command(name='skip', description='Skips the current track')
async def skip(ctx):
    print_timestamp_ext("Requested skip command by: ", ctx.author.name)
    await ctx.defer()
    voice_client = ctx.voice_client
    if voice_client is None:
        await ctx.followup.send("The bot is not connected to a voice channel.")
    elif voice_client.is_playing():
        voice_client.stop()
        await play_next(ctx)
        await ctx.followup.send("Skipping current track.")
    else:
        await ctx.followup.send("There's nothing to skip!")

@bot.slash_command(name='join', description='Tells the bot to join the voice channel')
async def join(ctx):
    print_timestamp_ext("Requested join command by: ", ctx.author.name)
    await ctx.defer()
    if not ctx.author.voice:
        await ctx.followup.send(f"{ctx.author.name} is not connected to a voice channel")
        return
    else:
        channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.followup.send("Connected to Channel.")

@bot.slash_command(name='leave', description='To make the bot leave the voice channel')
async def leave(ctx):
    print_timestamp_ext("Requested leave command by: ", ctx.author.name)
    await ctx.defer()
    voice_client = ctx.voice_client
    if voice_client is None:
        await ctx.followup.send("The bot is not connected to a voice channel.")
    elif voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.followup.send("Leaving the voice channel.")
    else:
        await ctx.followup.send("The bot is not connected to a voice channel.")

@bot.slash_command(name='pause', description='This command pauses the song')
async def pause(ctx):
    print_timestamp_ext("Requested pause command by: ", ctx.author.name)
    await ctx.defer()
    voice_client = ctx.voice_client
    if voice_client is None:
        await ctx.followup.send("The bot is not connected to a voice channel.")
    elif voice_client.is_playing():
        voice_client.pause()
        await ctx.followup.send("Paused the song.")
    else:
        await ctx.followup.send("The bot is not playing anything at the moment.")

@bot.slash_command(name='resume', description='Resumes the song')
async def resume(ctx):
    print_timestamp_ext("Requested resume command by: ", ctx.author.name)
    await ctx.defer()
    voice_client = ctx.voice_client
    if voice_client is None:
        await ctx.followup.send("The bot is not connected to a voice channel.")
    elif voice_client.is_paused():
        voice_client.resume()
        await ctx.followup.send("Resumed the song.")
    else:
        await ctx.followup.send("The bot was not playing anything before this.")

@bot.slash_command(name='stop', description='Stops the song')
async def stop(ctx):
    print_timestamp_ext("Requested stop command by: ", ctx.author.name)
    await ctx.defer()
    voice_client = ctx.voice_client
    if voice_client is None:
        await ctx.followup.send("The bot is not connected to a voice channel.")
    elif voice_client.is_playing():
        voice_client.stop()
        await ctx.followup.send("Stopped the song.")
    else:
        await ctx.followup.send("The bot is not playing anything at the moment.")

@bot.slash_command(name="queue", description="Display the current song queue.")
async def queue(ctx):
    await ctx.defer()
    if not song_names:  # Use the song_names list to check if the queue is empty
        await ctx.followup.send("The song queue is currently empty.")
    else:
        queue_text = "\n".join(song_names)  # Use the song_names list to display the queue
        await ctx.followup.send(f"Current song queue:\n{queue_text}")

@bot.slash_command(
    name="loop",
    description="Control the loop mode.",
    options=[
        Option(
            name="mode",
            description="Loop mode",
            type=3,  # Type 3 corresponds to string
            choices=[
                "disable",
                "current track",
                "all"
            ]
        )
    ]
)
async def loop(ctx, mode: str):
    print_timestamp_ext("Requested loop command by: ", ctx.author.name)
    global loop_mode
    await ctx.defer()
    print_timestamp_ext("Provided mode: ", mode)
    if mode.lower() == "disable":
        loop_mode = 0
        await ctx.followup.send("Looping is now disabled.")
    elif mode.lower() == "current track":
        loop_mode = 1
        await ctx.followup.send("Now looping the current song.")
    elif mode.lower() == "all":
        loop_mode = 2
        await ctx.followup.send("Now looping the whole queue.")
    else:
        await ctx.followup.send("Invalid loop mode...")


# Event handler for bot ready
@bot.event
async def on_ready():
    print_colored_text("""⠀⠀
    :  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣷⣀⠀⠀⠀⠀⠀⣤⡀⠲⣤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢻⣿⣿⣤⡀⠀⠀⠀⣛⣿⣾⣿⣿⣶⣶⣦⣤⠀⠀⠀⠀⠀⠀⠀⠀🤍
⠀⠀⠀⠀⠀⠀⢿⣿⣿⣿⣿⣿⣇⢇⢀⣴⣿⣿⣿⣿⣤⠊⣿⣦⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠙⢿⣯⣧⣷⢷⣶⣶⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣤⣿⣧⣿⣿⣿⣿⣿⣿⡿⣿⣿⣿⣿⡿⠉⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣤⣿⣿⣿⣿⣿⣿⡿⠋⠁⠀⣤⣿⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠒⠿⢿⣿⣿⠿⠿⠛⠉⢀⣤⣤⣶⣿⣿⣿⣿⣯⠁⠀⠀⢀⣾⣿⣷⢆⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⣤⣿⣿⣿⣿⣿⣿⣯⣾⠋⠿⣷⣤⣤⣿⣿⣷⣷⣧⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⣿⣿⢏⣿⣿⣿⣿⣦⢄⢈⢻⣿⣿⣿⡿⠁⠀⠀
⠀⠀⠀⠀⠀⠀⢠⢔⠸⣿⣿⣿⣿⣿⡀⢫⣿⣿⣿⣿⣎⣇⠇⠛⠋⠁⠀⠀⠀⠀
⠀⠀⠀⢀⢆⠃⠀⠀⠀⠻⣟⣿⣿⠛⠁⢀⣠⣾⣿⣿⣟⣧⢀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⢠⣏⠀⠀⠀⠀⠀⠀⠀⠈⠀⢀⣤⣾⣿⠟⠋⢀⣯⠓⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⢸⣗⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⣿⠁⠀⠀⠀⢻⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠻⣷⣦⣆⣦⣦⣦⣦⣶⣶⣮⣯⠀⠀⠀⠀ ⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠉⠉⠉⠉⠉⠉⠉⢹⡿⣿⣶⠀⠀ ⢀⣾⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⠟⠀⢈⣿⣿⠀ ⠻⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠁⠀⣠⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⠛⠀

""", TextColor.CYAN)
    print_colored_text(f'       {bot.user.name}', TextColor.PURPLE) 
    print(' is ready! ^^')
    print('')
    global check_alone_status
    if not check_alone_status.is_running():
        check_alone_status.start()

bot.run(os.getenv('DISCORD_TOKEN'))