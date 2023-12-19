#!/path/to/python3.10

import os
import discord
from discord.ext import tasks, commands
from discord.commands import Option
import yt_dlp
import asyncio
import subprocess
import json
import random
from .errorHandler import print_timestamp

apikey = os.getenv('API_KEY')
first_play_ctx = None
song_queue = []
song_names = []
song_infos = {}
loop_mode = 0
ydlp_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extractaudio': True,
    'yes_playlist': True,
    'ignore_errors': True,
    'progress': True,
    'skip_download': True,
    'downloader_args': ['aria2c:-N10'],
    'buffer_size': 1024,
    'concurrent_fragments': 10,
    'max_download_rate': '50K',
}

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

async def fetch_songs(ctx, url):
    print_timestamp('Fetching songs')
    try:
        global song_queue, song_names
        result = subprocess.run(['node', f'{os.path.dirname(os.path.abspath(__file__))}/getVideoUrls.js', url, apikey], capture_output=True, text=True)
        if result.returncode == 0:
            try:
                videos = json.loads(result.stdout)
            except json.JSONDecodeError:
                print_timestamp('No videos found in the playlist.', 'Error: ', 1)
                await ctx.followup.send('Please provide a valid url (no youtube mix url).')
                return
            for video in videos:
                song_queue.append(video['url'])
                song_names.append(video['name']) 
                print_timestamp(f"{video['name']}", 'Added to queue: ', 2, f"{video['url']}")
            print_timestamp('Finished fetching song/s.')
            await ctx.followup.send('Added song/s to the queue.')
        else:
            print_timestamp(result.stderr, 'Error: ', 1)
    except Exception as e:
        print_timestamp(e, 'Exception: ', 1)

# Function to stream music
async def stream_music(ctx, url, self):
    global song_queue, song_names
    first_play_ctx = None
    if first_play_ctx is None:
        first_play_ctx = ctx
    try:
        with yt_dlp.YoutubeDL(ydlp_opts) as ydlp:
            print_timestamp('Getting Streamlink')
            info = ydlp.extract_info(url, download=False)
            # Store song info in cache for future use
            song_infos[url] = info

        voice_channel = await join_channel(ctx)
        print_timestamp(info['title'], 'Streaming audio from: ')

        options = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 60'
        voice_channel.play(discord.FFmpegPCMAudio(info['url'], before_options=options), after=lambda e: after_playing(ctx, e, self))
        await ctx.followup.send(f'Started Playing: {url}')
    except Exception as e:
        print_timestamp(e, 'An error occurred while streaming: ', 1)


async def join_channel(ctx):
    if ctx.voice_client is not None and ctx.voice_client.is_connected():
        return ctx.voice_client
    try: 
        channel = ctx.author.voice.channel
        if channel:
            voice_channel = await channel.connect()
            song_queue.clear()
            song_names.clear()
            return voice_channel
        else:
            await ctx.followup.send('Something went wrong.')
            print_timestamp('Something went wrong, when trying to join channel.', 'Error: ', 1)
    except:
        await ctx.followup.send('You are not in a voice channel.')
        print_timestamp('Person requesting music playback is not in a voice channel.', 'User-Error: ')
        return None


def after_playing(ctx, error, self):
    if error:
        print_timestamp(error, 'An error occurred while playing: ', 1)
        loop = self.bot.loop
        loop.create_task(ctx.send(f'An error occurred while playing: {error}'))
               
    print_timestamp('Finished current track.')
    loop = self.bot.loop
    if loop_mode == 1:
        # Loop the current song
        print_timestamp('Loop the current song', 'current mode: ')
        loop.create_task(stream_music(ctx, song_queue[0]))
    elif loop_mode == 2 and song_queue:
        # Loop the whole queue
        print_timestamp('Loop the whole queue', 'current mode: ')
        loop.create_task(stream_music(ctx, song_queue.pop(0)))
    elif song_queue:
        # No loop, play the next song
        print_timestamp('No loop', 'current mode: ')
        loop.create_task(stream_music(ctx, song_queue.pop(0)))


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Define the 'play' command
    @commands.slash_command(name='play', description='Playing music.')
    async def play(self, ctx, url: str):
        global song_queue, song_names
        print_timestamp(ctx.author.name, 'Requested play command by: ')
        await ctx.defer()

        voice_client = await join_channel(ctx)
        if voice_client is None:
            return


        await fetch_songs(ctx, url)
        if not voice_client.is_playing():
            while not song_queue:
                await asyncio.sleep(0.5)    
        await stream_music(ctx, song_queue.pop(0), self)
    
    @commands.slash_command(name='skip', description='Skips the current track')
    async def skip(self, ctx):
        print_timestamp(ctx.author.name, 'Requested skip command by: ')
        await ctx.defer()
        voice_client = ctx.voice_client
        if voice_client is None:
            await ctx.followup.send('The bot is not connected to a voice channel.')
        elif voice_client.is_playing():
            voice_client.stop()
            await ctx.followup.send('Skipping current track.')
            while voice_client.is_playing():
                await asyncio.sleep(0.1)
            if song_queue:  # Check if there are songs in the queue
                await stream_music(ctx, song_queue.pop(0))
            else:
                await ctx.followup.send('No more songs in the queue.')
        else:
            await ctx.followup.send('There is nothing to skip!')

    @commands.slash_command(name='join', description='Tells the bot to join the voice channel')
    async def join(self, ctx):
        print_timestamp(ctx.author.name, 'Requested join command by: ')
        await ctx.defer()
        if not ctx.author.voice:
            await ctx.followup.send(f'{ctx.author.name} is not connected to a voice channel')
            return
        else:
            channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.followup.send('Connected to Channel.')

    @commands.slash_command(name='leave', description='To make the bot leave the voice channel')
    async def leave(self, ctx):
        print_timestamp(ctx.author.name, 'Requested leave command by: ')
        await ctx.defer()
        voice_client = ctx.voice_client
        if voice_client is None:
            await ctx.followup.send('The bot is not connected to a voice channel.')
        elif voice_client.is_connected():
            await voice_client.disconnect()
            await ctx.followup.send('Leaving the voice channel.')
        else:
            await ctx.followup.send('The bot is not connected to a voice channel.')

    @commands.slash_command(name='pause', description='This command pauses the song')
    async def pause(self, ctx):
        print_timestamp(ctx.author.name, 'Requested pause command by: ')
        await ctx.defer()
        voice_client = ctx.voice_client
        if voice_client is None:
            await ctx.followup.send('The bot is not connected to a voice channel.')
        elif voice_client.is_playing():
            voice_client.pause()
            await ctx.followup.send('Paused the song.')
        else:
            await ctx.followup.send('The bot is not playing anything at the moment.')

    @commands.slash_command(name='resume', description='Resumes the song')
    async def resume(self, ctx):
        print_timestamp(ctx.author.name, 'Requested resume command by: ')
        await ctx.defer()
        voice_client = ctx.voice_client
        if voice_client is None:
            await ctx.followup.send('The bot is not connected to a voice channel.')
        elif voice_client.is_paused():
            voice_client.resume()
            await ctx.followup.send('Resumed the song.')
        else:
            await ctx.followup.send('The bot was not playing anything before this.')

    @commands.slash_command(name='stop', description='Stops the song')
    async def stop(self, ctx):
        print_timestamp(ctx.author.name, 'Requested stop command by: ')
        await ctx.defer()
        voice_client = ctx.voice_client
        if voice_client is None:
            await ctx.followup.send('The bot is not connected to a voice channel.')
        elif voice_client.is_playing():
            song_queue.clear()
            song_names.clear()
            voice_client.stop()
            await ctx.followup.send('Stopped the song.')
        else:
            await ctx.followup.send('The bot is not playing anything at the moment.')

    @commands.slash_command(name='queue', description='Display the current song queue.')
    async def queue(self, ctx):
        await ctx.defer()
        if not song_names:  # Use the song_names list to check if the queue is empty
            await ctx.followup.send('The song queue is currently empty.')
        else:
            queue_text = '\n'.join(song_names)  # Use the song_names list to display the queue
            await ctx.followup.send(f'Current song queue:\n{queue_text}')

    @commands.slash_command(
        name='loop',
        description='Control the loop mode.',
        options=[
            Option(
                name='mode',
                description='Loop mode',
                type=3,
                choices=[
                    'disable',
                    'current track',
                    'all',
                    '?'
                ]
            )
        ]
    )
    async def loop(self, ctx, mode: str):
        print_timestamp(ctx.author.name, 'Requested loop command by: ')
        global loop_mode
        await ctx.defer()
        print_timestamp(mode, 'Provided mode: ')
        if mode.lower() == 'disable':
            loop_mode = 0
            await ctx.followup.send('Looping is now disabled.')
        elif mode.lower() == 'current track':
            loop_mode = 1
            await ctx.followup.send('Now looping the current song.')
        elif mode.lower() == 'all':
            loop_mode = 2
            await ctx.followup.send('Now looping the whole queue.')
        elif mode.lower() == '?':
            await ctx.followup.send(f'Current mode: {currentLoopMode(loop_mode)}')
        else:
            await ctx.followup.send('Invalid loop mode...')

    def currentLoopMode(loop_mode):
        if loop_mode == 0:
            return 'Disabled'
        elif loop_mode == 1:
            return 'Current Track'
        elif loop_mode == 2:
            return 'Whole queue'

    @commands.slash_command(name='shuffle', description='Shuffling the queue.')
    async def shuffle(self, ctx):
        global song_queue, song_names
        await ctx.defer()
        combined = list(zip(song_queue, song_names))
        random.shuffle(combined)
        song_queue[:], song_names[:] = zip(*combined)
        await ctx.followup.send('shuffled the playlist.')

def setup(bot):
   bot.add_cog(Music(bot))