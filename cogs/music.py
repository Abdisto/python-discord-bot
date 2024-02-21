#!/path/to/python3.10

import os
import discord
from discord import option, PCMVolumeTransformer
from discord.ext import tasks, commands
from discord.commands import Option
import yt_dlp
import asyncio
import subprocess
import datetime
import json
import random
import magic
from .errorHandler import print_timestamp

apikey = os.getenv('API_KEY')

first_play_ctx = None # just in case of different channels 
current_song_index = 0
current_song_playing = None
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
    'downloader_args': ['aria2c:-N10'],
    'buffer_size': 1024,
    'concurrent_fragments': 10,
    'max_download_rate': '50K',
}

magic = magic.Magic(mime=True)
allowed_mime_types = ["audio/mpeg", "audio/x-ms-wma", "audio/vnd.wave", "video/mpeg", "video/mp4"]

async def join_channel(ctx):
    if ctx.voice_client is not None and ctx.voice_client.is_connected():
        return ctx.voice_client
    else:
        try: 
            channel = ctx.author.voice.channel
            if channel:
                voice_channel = await channel.connect()
                song_queue.clear() # redundant
                song_names.clear() 
                return voice_channel
            else:
                await ctx.followup.send('Something went wrong.')
                print_timestamp('Something went wrong, when trying to join channel.', 'Error: ', 1)
        except:
            await ctx.followup.send('You are not in a voice channel.')
            print_timestamp('Person requesting music playback is not in a voice channel.', 'User-Error: ')
            return None

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
async def stream_music(ctx, url, self, file=None, volume=0.1):
    global song_queue, song_names, first_play_ctx
    voice_channel = await join_channel(ctx)
    if first_play_ctx is None:
        first_play_ctx = ctx
    try:
        if file:
            audio_source = discord.FFmpegPCMAudio(executable="/usr/bin/ffmpeg", source=file)
            audio_source = PCMVolumeTransformer(audio_source, volume=volume)
            voice_channel.play(audio_source, after=lambda e: after_playing(ctx, e, self, file))
            await ctx.followup.send(f'Started Playing: {file}')
            print_timestamp(file, 'Streaming audio from: ')
        else:
            with yt_dlp.YoutubeDL(ydlp_opts) as ydlp:
                print_timestamp('Getting Streamlink')
                info = ydlp.extract_info(url, download=False)

            print_timestamp(info['title'], 'Streaming audio from: ')

            options = '-vn -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
            audio_source = discord.FFmpegPCMAudio(info['url'], before_options=options)
            audio_source = PCMVolumeTransformer(audio_source, volume=volume)
            voice_channel.play(audio_source, after=lambda e: after_playing(ctx, e, self))
            await ctx.followup.send(f'Started Playing: {url}')
    except Exception as e:
        print_timestamp(e, 'An error occurred while streaming: ', 1)

def after_playing(ctx, error, self, file=None):
    global current_song_index, current_song_playing, song_queue
    if error:
        print_timestamp(error, 'An error occurred while playing: ', 1)
        loop = self.bot.loop
        loop.create_task(ctx.send(f'An error occurred while playing: {error}'))

    print_timestamp('Finished current track.')
    loop = self.bot.loop

    if loop_mode == 0:
        try:
            current_song_index += 1
            # No loop, play the next song
            print_timestamp('No loop', 'Current mode: ')
            loop.create_task(stream_music(ctx, song_queue.pop(0), self))
            if file:
                os.remove(file)
                print_timestamp(f"Deleted file: {file}")
        except:
            print_timestamp('Queue empty.')
    elif loop_mode == 1:
        try:
            print(song_queue)
            print_timestamp('Loop the current song', 'Current mode: ')
            loop.create_task(stream_music(ctx, current_song_playing, self))
        except:
            print_timestamp('Queue empty.')
    elif loop_mode == 2 and song_queue:
        try:
            current_song_index += 1 % song_queue.len()
            # Loop the whole queue
            print_timestamp('Loop the whole queue', 'Current mode: ')
            loop.create_task(stream_music(ctx, song_queue.pop(0), self))
        except:
            print_timestamp('Queue empty.')

def clear_queue(self):
    global song_queue, song_names
    try:
        song_queue.clear()
        song_names.clear()
        print_timestamp('Playlist cleared!')
    except:
        print_timestamp('Queue either empty or having problems clearing queue!')

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def clear(self):
        print_timestamp('Leaving due to inactivity!')
        clear_queue(self)

    # Define the 'play' command
    @commands.slash_command(
        name='play',
        description='Playing music.')
    @discord.option(
        name='url',
        description='Play Music by url',
        required=False)
    @discord.option(
        name='attachment',
        description='Upload a file to play',
        required=False,
        type=discord.Attachment)
    @discord.option(
        name='search',
        description='Search by song name',
        required=False
    )
    async def play(self, ctx, url: str = None, attachment: discord.Attachment = None, search: str = None):
        global current_song_playing, song_queue, song_names
        await ctx.defer()
        print_timestamp(ctx.author.name, f'Requested play command by: ')
        inputs_provided = sum([url is not None, search is not None, attachment is not None])
        if inputs_provided > 1:
            await ctx.respond('Please provide only a URL, search terms, or an attachment, not multiple.', ephemeral=True)
            return

        if url or attachment or search != None:
            voice_client = await join_channel(ctx)
            if voice_client is None:
                return

        if url:
            await fetch_songs(ctx, url)
            if not voice_client.is_playing() and song_queue:
                current_song_playing = song_queue.pop(0)
                await stream_music(ctx, current_song_playing, self)
        elif attachment:
            file_path = f'./{attachment.filename}'
            try:
                mime_type = magic.from_buffer(await attachment.read())
                if mime_type not in allowed_mime_types:
                    await ctx.followup.send(f'Unsupported file type: {mime_type}')
                    return
                await attachment.save(file_path)
                # Check if the file exists before attempting to play it
                if not os.path.exists(file_path):
                    print_timestamp(f'File not found: {file_path}')
                    return
                # Append the file path to the song_queue and a descriptive name to song_names
                song_queue.append(file_path)
                song_names.append(f'File: {attachment.filename}')
                # Play the local file using the stream_music function if nothing is currently playing
                if not voice_client.is_playing():
                    current_song_playing = song_queue.pop(0)
                    await stream_music(ctx, None, self, file=current_song_playing)
            except Exception as e:
                await ctx.followup.send(f'An error occurred while saving the file: {e}')
        elif search:
            with yt_dlp.YoutubeDL(ydlp_opts) as ydlp:
                info = ydlp.extract_info(f'ytsearch:{search}', download=False)
                url = info['entries'][0]['webpage_url']
                song_queue.append(url)
                song_names.append(info['entries'][0]['title'])
            if not voice_client.is_playing() and song_queue:
                current_song_playing = song_queue.pop(0)
                await stream_music(ctx, current_song_playing, self)
        else:
            await ctx.followup.send('Provide an input please.')
            print_timestamp('User did not provide an input.')


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
            if song_queue:
                await stream_music(ctx, song_queue.pop(0), self)
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
            clear_queue(self)
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
            clear_queue(self)
            voice_client.stop()
            await ctx.followup.send('Stopped the song.')
        else:
            await ctx.followup.send('The bot is not playing anything at the moment.')

    @commands.slash_command(name='queue', description='Display the current song queue.')
    async def queue(self, ctx):
        global song_queue, song_names
        await ctx.defer()
        if not song_names:
            await ctx.followup.send('The song queue is currently empty.')
        else:
            queue_text = "\n".join(f"**{i+1}.** {name} {'  **- currently playing** ' if i == current_song_index else ''}" for i, name in enumerate(song_names))
            embed = discord.Embed(
                title="Current song queue",
                description=queue_text,
                color=discord.Color.blue()
            )
            await ctx.followup.send(embed=embed)

    # @commands.slash_command(name='nowplaying', description='Display the currently playing song.')
    # async def now_playing(self, ctx):
    #     global song_queue, song_names
    #     await ctx.defer()
    #     if not song_queue and song_names:  # Check if the song queue is empty
    #         await ctx.followup.send('No song is currently playing.')
    #     else:
    #         # Use yt_dlp to get information about the song
    #         with yt_dlp.YoutubeDL(ydlp_opts) as ydlp:
    #             info = ydlp.extract_info(song_queue[0], download=False)
    #         voice_channel = ctx.author.voice.channel

    #         # Get the voice client
    #         voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

    #         # Calculate the current time elapsed
    #         current_time = voice_client.source.duration if voice_client.source else 0

    #         # Create an embed message
    #         embed = discord.Embed(
    #             title="Now Playing",
    #             description=f"[{info['title']}]({info['webpage_url']})",
    #             color=discord.Color.blue()
    #         )

    #         # Add fields to the embed message
    #         embed.add_field(name="Duration", value=str(datetime.timedelta(seconds=info['duration'])))
    #         embed.add_field(name="Current Time", value=str(datetime.timedelta(seconds=current_time)))
    #         embed.set_thumbnail(url=info['thumbnail'])

    #         # Send the embed message
    #         await ctx.followup.send(embed=embed)

    @commands.slash_command(name='delete', description='Delete a song from the queue.')
    async def delete(self, ctx, index: int):
        global song_queue, song_names, current_song_index
        await ctx.defer()
        if index > 0 and index <= len(song_queue):
            if index == current_song_index + 1: # If the song to be deleted is the next song to be played
                current_song_index -= 1 # Move the current song index back by one
            removed_song = song_names.pop(index - 1) # Adjust for 0-indexing
            removed_url = song_queue.pop(index - 1) # Adjust for 0-indexing
            await ctx.followup.send(f'Removed {removed_song} from the queue.')
        else:
            await ctx.followup.send('Invalid index.')

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

    # @commands.slash_command(name='shuffle', description='Shuffling the queue.')
    # async def shuffle(self, ctx):
    #     global song_queue, song_names, current_song_index
    #     await ctx.defer()
    #     if len(song_queue) > 1:  # Check if there are songs to shuffle
    #         # Exclude the currently playing song and remove duplicates
    #         unique_queue = list(set(song_queue[current_song_index + 1:]))
    #         random.shuffle(unique_queue)
            
    #         # Update the song queue and names with the shuffled list
    #         song_queue[current_song_index + 1:] = unique_queue
    #         shuffled_names = [song_names[song_queue.index(song)] for song in unique_queue]
    #         song_names[current_song_index + 1:] = shuffled_names
            
    #         await ctx.followup.send('Shuffled the playlist.')
    #     else:
    #         await ctx.followup.send('Not enough songs in the queue to shuffle.')

def setup(bot):
   bot.add_cog(Music(bot))
