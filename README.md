# python-discord-bot
A discord bot written in python with discord.py and pycord for more functionality.
Javascript file for fetching playlist URL's and .sh script to autostart the bot systemd.

We are using the 'os' library to parse the DISCORD_TOKEN and API_KEY into and from the linux environment 
to add these u just need to add them inside the /etc/environment file, U can also use the setup-wizard:

| we need to use sudo to install inquirer globally since we will use sudo    | we need sudo for the permissions 
```
sudo pip3.10 install inquirer
sudo python3.10 setup-wizard.py
```
