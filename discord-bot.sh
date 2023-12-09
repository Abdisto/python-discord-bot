if screen -list | grep -q "discord_bot"; then
    echo "Discord bot is already running."
else
    # Start the Discord bot in a detached screen session
    /usr/bin/screen -dmS discord_bot /bin/bash -c 'python3.10 /home/abdist/discord-bot/discord-bot.py; exec /bin/bash'
    echo "Discord bot started."
fi
