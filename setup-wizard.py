#!/path/to/python3.10

#Create .service file
import subprocess
import os

os.setuid(0)
service_file_path = "/etc/systemd/system/discord-bot-scirpt.service"
sh_file_path = f"{os.path.dirname(os.path.abspath(__file__))}/discord-bot.sh"
relative_path = f"{os.path.dirname(os.path.abspath(__file__))}"

def setTokens(apikey, variable_name):
	token = ""
	command = f'echo "{variable_name}=\\"{token}\\"" >> /etc/environment'
	command_list = ['bash', '-c', command]
	process = subprocess.Popen(command_list, stdout=subprocess.PIPE, shell=False)

# Generate the sh file
def genShFile():
	sh_file_content = f'''if screen -list | grep -q "discord_bot"; then
	echo "Discord bot is already running."
else
    # Start the Discord bot in a detached screen session
    /usr/bin/screen -dmS discord_bot /bin/bash -c "python3.10 {relative_path}/discord-bot.py; exec /bin/bash"
    echo "Discord bot started."
fi
	'''
	os.chdir(relative_path)

	with open(sh_file_path, "w") as file:
	   	file.write(sh_file_content)

# Generate the service file
def genServiceFile():
	service_file_content = f'''[Unit]
	Description=discord-bot-script

	[Service]
	Type=oneshot
	ExecStart=sh -c "{relative_path}/discord-bot.sh"

	[Install]
	WantedBy=multi-user.target
	'''

	os.chdir("/etc/systemd/system")

	with open(service_file_path, "w") as file:
   		file.write(service_file_content)

setTokens(apikey, "APIKEY")					# user input not defined yet
setTokens(discord_token, "DISCORD_TOKEN")	#
genServiceFile()
genShFile()

print('''\nTo enable the automatic startup of you Disocrd Bot please execute the following commands:

- $sudo systemctl start discord-bot-script.service  -
- $sudo systemctl enable discord-bot-script.service -
''')

