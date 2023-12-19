# python-discord-bot
A discord bot written in python with discord.py and pycord for more functionality.
Javascript file for fetching playlist URL's and .sh script to autostart the bot systemd.

We are using the 'os' library to parse the DISCORD_TOKEN and API_KEY into and from the linux environment 
to add these u just need to add them inside the /etc/environment file, U can also use the setup-wizard:

```
sudo pip3.10 install inquirer    | we need to use sudo to install inquirer globally since we will use sudo 
sudo python3.10 setup-wizard.py  | we need sudo for the permissions 
```
