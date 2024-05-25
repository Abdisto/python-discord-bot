# python-discord-bot
[![MIT](https://img.shields.io/github/license/BlacklightYT/python-discord-bot?color=a3425d)](https://github.com/BlacklightYT/python-discord-bot/blob/main/LICENSE) ![Static Badge](https://img.shields.io/badge/python-3.10-brightgreen?style=flat&logo=python)

A discord bot written in python with pycord for more functionality.
I am using pomice for the music support and created a bash script 
to set the parameters and automate the bot's autostart with systems.

This branch also adds the command /server in which someone can start/restart/stop 
a minecraft server. The state of the server will be displayed on the bot account
at all times.

How does it work?
We write to a local file '/tmp/server_action' that we will then send to a server
with scp. In this file the state of the server is defined. 
Server-side handling (read file -> do things) files are not public yet.

Can I use it for different kinds of servers?
Yes, since this should be server-side handled. 
One Problem: when doing so, you should use dev3, because we target 
minecraft servers with the server status in the bot profile 

> [!IMPORTANT]
> In cogs/minecraft/minecraft.py u have to set the variables

## Installing
``` 
git clone -b dev2 https://github.com/BlacklightYT/python-discord-bot/
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
> Don't forget to set the correct ports via the bash script
