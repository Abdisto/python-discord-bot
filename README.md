# Fix for current issues/refactoring may be pushed in the next couple of months. Just finishing my exams first.

# Most problems are already fixed but pushing them into the right branches may take a while. 

# python-discord-bot
[![MIT](https://img.shields.io/github/license/BlacklightYT/python-discord-bot?color=a3425d)](https://github.com/BlacklightYT/python-discord-bot/blob/main/LICENSE) ![Static Badge](https://img.shields.io/badge/python-3.10-brightgreen?style=flat&logo=python)

A discord bot written in python with pycord for more functionality.
I am using pomice for the music support and created a bash script 
to set the parameters and automate the bot's autostart with systems.

> Not completely ready yet:
>
> For Minecraft server start/restart/stop capabilities use branch: dev2
> 
> For any server start/restart/stop capabilities use branch: dev3

## Installing
``` 
git clone https://github.com/BlacklightYT/python-discord-bot/
```
```
cd python-discord-bot
```
```
python3.10 -m pip install -r requirements.txt
```
> Could take longer on low end devices
> [Was the case on my old tv box with linux]

## Using the setup-wizard
> We need sudo trust me bro
```
sudo python3.10 setup_wizard.py
```
> If you encounter problems using the setup-wizard you could of course contact me :)

## Usage
```
python3.10 bot_init.py
```

> [!IMPORTANT]
> lavalink is required and should be downloaded from the official GitHub repo:
> 
> https://github.com/lavalink-devs/Lavalink
> 
> Don't forget to set the correct port via the bash script
