# python-discord-bot
A discord bot written in python with pycord for more functionality.
I am using pomice for the music support and created a bash script 
to set the parameters and automate the bot's autostart with systemd.

| We need sudo for the permissions trust me bro 

```
python3.10 -m pip install -r  requirements.txt
```

```
sudo python3.10 setup-wizard.py
```
> If you encounter problems using the setup-wizard you could of course contact me :)

```
python3.10 bot_init.py
```
> [!IMPORTANT]
> lavalink is required and should be downloaded from the official GitHub repo
> Don't forget to set the correct ports via the bash script

compatibility:
python3.10
