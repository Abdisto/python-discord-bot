# python-discord-bot
[![MIT](https://img.shields.io/github/license/BlacklightYT/python-discord-bot?color=2f2f2f)](https://github.com/BlacklightYT/python-discord-bot/blob/main/LICENSE) ![3.10](https://img.shields.io/pypi/pyversions/python-discord-bot?color=2f2f2f)

A discord bot written in python with pycord for more functionality.
I am using pomice for the music support and created a bash script 
to set the parameters and automate the bot's autostart with systemd.

```
python3.10 -m pip install -r  requirements.txt
```
> We need sudo for the permissions trust me bro

```
sudo python3.10 setup-wizard.py
```
> If you encounter problems using the setup-wizard you could of course contact me :)

```
python3.10 bot_init.py
```
> [!IMPORTANT]
> lavalink is required and should be downloaded from the official GitHub repo: https://github.com/lavalink-devs/Lavalink
> 
> Don't forget to set the correct ports via the bash script
