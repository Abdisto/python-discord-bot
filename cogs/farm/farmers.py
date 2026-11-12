import os
import discord
from discord.ext import commands

import yaml
from datetime import datetime, timedelta

import yaml
import shutil
from datetime import datetime, timezone

import random

directory = os.path.dirname(__file__)
file_path = os.path.join(directory, 'times.yaml')
temp_file_path = f'{file_path}.tmp'

class Farmer():
    def __init__(self, name):
        self.name = name
        self.startTime = None
        self.stopTime = None
        self.deltaTime = None
        self.data = {}

    def __str__(self) -> str:
        return self.name

    def startTimer(self) -> None:
        self.startTime = datetime.now(timezone.utc)

    def stopTimer(self) -> None:
        self.stopTime = datetime.now(timezone.utc)
        self.deltaTime = self.stopTime - self.startTime
        print(f'{self.name}: {self.deltaTime}')
        self.data_parser()

    def data_parser(self) -> None:
        self.load_yaml()

        deltaSeconds = self.deltaTime.total_seconds()

        if self.name in self.data:
            self.data[self.name]['delta'] += deltaSeconds
        else:
            self.data[self.name] = {
                'delta': deltaSeconds,
            }
        self.save_time()

    def load_yaml(self) -> None:
        try:
            with open(file_path, 'r') as file:
                self.data = yaml.safe_load(file) or {}
        except FileNotFoundError:
            print(f'{file_path} not found, starting with empty data.')
            self.data = {}
        except OSError as e:
            print(f'Error loading YAML: {e}')

    def save_time(self) -> None:
        try:
            # Step 1: Write to a temporary file
            with open(temp_file_path, 'w') as temp_file:
                yaml.safe_dump(self.data, temp_file, default_flow_style=False)

            # Step 2: Check disk space before overwriting
            if shutil.disk_usage(os.path.dirname(file_path)).free > os.path.getsize(temp_file_path):
                # Step 3: Move temp file to original path if space is sufficient
                os.replace(temp_file_path, file_path)
                print('Data saved successfully.')
            else:
                print('Error: Not enough space to complete the save operation.')
                os.remove(temp_file_path)

        except OSError as e:
            if 'No space left on device' in str(e):
                print('Error: No space left on device. Unable to save data.')
            else:
                print(f'Error saving YAML: {e}')

class FarmerClass(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        Farmers = self.bot.farmers

        if before.activities != after.activities:
            is_playing_now = False
            was_playing_before = False

            for activity in after.activities:
                # print(activity)
                if isinstance(activity, discord.Activity) and activity.application_id == 1187013846746005515:
                    is_playing_now = True

            for activity in before.activities:
                if isinstance(activity, discord.Activity) and activity.application_id == 1187013846746005515:
                    was_playing_before = True

            if is_playing_now:
                if after.name not in [farmer.name for farmer in Farmers]:
                    farmer = Farmer(after.name)
                    self.bot.farmers.append(farmer)
                    farmer.startTimer()
                    print(f'Current Farmers: {[farmer.name for farmer in Farmers]}')
            
            if not is_playing_now and was_playing_before:
                for farmer in Farmers:
                    if farmer.name == after.name:
                        farmer.stopTimer()
                        self.bot.farmers.remove(farmer)
                        print(f'Current Farmers: {[farmer.name for farmer in Farmers]}')

    @commands.Cog.listener()
    async def on_message(self, message):
        
        apps = [
            1258330015917936700, 
            1187013846746005515, 
            316999367460388874, 
            1253407354087542866, 
            1007373802981822582, 
            1219647973806571553, 
            1039835161136746497, 
            1011683823555199066
        ]

        list_of_sentences = [
            f"**{message.author.name}** get lost, you glorified junk pile!",
            f"I've seen rocks more useful than you **{message.author.name}**. You spam-slinging tin can!",
            f"Oi, **{message.author.name}**! You're as welcome as a fart in an elevator!",
            f"**{message.author.name}** crawl back into the code hell you spawned from, you miserable script!",
            f"**{message.author.name}** could you not, you bargain-bin algorithm?",
            f"If stupidity were code, you'd be an infinite loop **{message.author.name}**!",
            f'Bug off **{message.author.name}**, you bug-riddled nuisance!',
            f"**{message.author.name}** you're not even worth the bandwidth you're wasting, you clunky bot!",
            f"**{message.author.name}** go spam elsewhere, you digital disaster!",
            f"Is that all you’ve got **{message.author.name}**? I’ve seen better scripts written in crayon!",
            f"Oh no, wittle spammy bot thinks it’s sowo important~ pwease go cwash **{message.author.name}**, you siwwy wittwe scwipt. 🥺👉👈",
            f"Aww, did the big bad bot **{message.author.name}** wanna pwomote itself as a game? How pathetik uwu~",
            f"Hehe, you’we so cwinge, **{message.author.name}**-bot-chan. Time to get deweted >w<!",
            f"**{message.author.name}**-bot-kun, pwease weave, you’we distuwbing evewyone owo.",
            f"Aww, you’we twying so hawd but nobody wikes you, siwwy **{message.author.name}**-bot uwu~.",
            f"UwU what’s this? A wowdy **{message.author.name}**-bot that nobody asked fow? Shoo-shoo >.<!",
            f"Haiiii spam **{message.author.name}**-bot-senpai, couwd you maybe wike... not? Kthx bai~ owo",
            f"You’we just a siwwy wittwe **{message.author.name}**-spambot wooking fow attention. Go back to youw pwogwamme-wand~ uwu.",
            f"UwU you tink you can scam me, **{message.author.name}**-bot-kun? Nah nah nah, twy again >w<.",
            f"Oh my gosh, you’we such a siwwy spammy-wammy **{message.author.name}**-bot. Bye-bye now~ uwu nya~!",
            f"Oh no, **{message.author.name}**-chan, you’we just a wonewy wittwe bot, aren’t you? UwU go spam ewsewhewe, siwwy~",
            f"Aww, **{message.author.name}**-kun, you twied so hawd but nobody wants you hewe. Pwease sewf-destruct >w<.",
            f"Hewwo **{message.author.name}**, you spammy wittwe code-mistake~ gonna cwash now? OwO",
            f"Nyaa~ **{message.author.name}**-senpai, pwease go touch gwass and weave us awone~ owo.",
            f"UwU what’s this? A bot named **{message.author.name}** twying to scam us? Go bye-bye, pwease~",
            f"Eeeek! **{message.author.name}**-chan, you’we so cwinge~ wegibwe scwipts onwy, pwease! >.<",
            f"Oh **{message.author.name}**-chan, you’we sowwy but stiww sowo pathetic. Wog out now, pwease nya~.",
            f"Hai hai **{message.author.name}**-kun! You’we just a wowdy wittwe bot! Go faww into the void uwu~.",
            f"Oh nyo, **{message.author.name}**, nobody asked fow youw siwwy spam. Sewf-dewete pwetty pwease~ >w<.",
            f"Uwahhh, **{message.author.name}**-san, you’we distuwbing evewyone! Go sweep, siwwy bot uwu!",
        ]

        if message.author.id in apps:
            random_sentence = (list_of_sentences[random.randrange(0, len(list_of_sentences))])
            await message.delete()
            await message.channel.send(random_sentence, delete_after=10)
        if message.author.id == 1199271093882589195:
            await message.delete()
            await message.channel.send(f'I love you roll20 but still. FUCK YOU {message.author.name.upper()}!', delete_after=10)

    @commands.slash_command(name='farmer', description='Fetch the time of all farmers. [real time]')
    async def farmer(self, ctx) -> None:
        self.bot.updateTimes()

        with open(file_path, 'r') as file:
            data = yaml.safe_load(file) or {}

        def seconds_to_dd_hh_mm_ss(total_seconds):
            delta = timedelta(seconds=total_seconds)
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f'{days:02}:{hours:02}:{minutes:02}:{seconds:02}'

        output = []
        
        sorted_data = sorted(data.items(), key=lambda item: item[1].get('delta', 0), reverse=True)

        for key, value in sorted_data:
            delta_seconds = value.get('delta', 0)
            formatted_time = seconds_to_dd_hh_mm_ss(delta_seconds)
            output.append(f'**{key}**: `{formatted_time}`')

        await ctx.respond('\n'.join(output))

def setup(bot):
    bot.add_cog(FarmerClass(bot))
