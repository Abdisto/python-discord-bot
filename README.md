# python-discord-bot
A discord bot written in python with discord.py and pycord for more functionality.
Javascript file for fetching playlist URL's and .sh script to autostart the bot systemd.

We are using the os library from python to parse the DISCORD_TOKEN and API_KEY from the linux environment 
to add these u just need to add them inside the /etc/environment file, It should something like that:
´´´
$DISCORD_TOKEN="yourdiscordtoken"
$API_KEY="yourapikey"
´´´
