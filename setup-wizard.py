#!/path/to/python3.10

#Create .service file
import subprocess
import os
import inquirer

def main():
	os.setuid(0)
	service_file_path = "/etc/systemd/system/discord-bot-script.service"
	sh_file_path = f"{os.path.dirname(os.path.abspath(__file__))}/discord-bot.sh"
	relative_path = f"{os.path.dirname(os.path.abspath(__file__))}"

	sequence = config()

	if sequence == 2:
		genShFile(sh_file_path, relative_path)
		genServiceFile(service_file_path, relative_path)
	else:
		if sequence == 0:
			genShFile(sh_file_path, relative_path)
			genServiceFile(service_file_path, relative_path)
			subprocess.run(["chmod", "+x", sh_file_path])
			subprocess.run(["chown", "root", sh_file_path])
			subprocess.run(["chmod", "+x", service_file_path])

		apikey, discord_token = setup(sequence)

		setTokens(apikey, "APIKEY")
		setTokens(discord_token, "DISCORD_TOKEN")

	print('''\nTo enable the automatic startup of you Disocrd Bot please execute the following commands:

	- $sudo systemctl daemon-reload -
	- $sudo systemctl start discord-bot-script.service -
	- $sudo systemctl enable discord-bot-script.service -
	- $sudo reboot -
	''')

def setTokens(token, variable_name):
	if not token.strip():
		return
	command = f'echo "{variable_name}=\\"{token}\\"" >> /etc/environment'
	command_list = ['bash', '-c', command]
	process = subprocess.Popen(command_list, stdout=subprocess.PIPE, shell=False)

# Generate the sh file
def genShFile(sh_file_path, relative_path):
	sh_file_content = f'''#!/bin/bash
set -x
if screen -list | grep -qw \"discord_bot\"; then
	echo \"Discord bot is already running.\"
else
	# Start the Discord bot in a detached screen session
	/usr/bin/screen -dmS discord_bot /bin/bash -c \'python3.10 {relative_path}/bot-init.py; exec /bin/bash\'
	echo \"Discord bot started.\"
fi'''
	os.chdir(relative_path)

	with open(sh_file_path, "w") as file:
		file.write(sh_file_content)


# Generate the service file
def genServiceFile(service_file_path, relative_path):
	service_file_content = f'''[Unit]
Description=discord-bot-script

[Service]
Type=oneshot
ExecStart=/bin/su - {os.getlogin()} -c \'{relative_path}/discord-bot.sh\'

[Install]
WantedBy=multi-user.target'''

	os.chdir("/etc/systemd/system")

	with open(service_file_path, "w") as file:
   		file.write(service_file_content)

def config():
    setup_choice = [
        inquirer.List(
            "choice",
            message="What should be setup??",
            choices=[("Setup token, apikey and startup", 0), 
            ("Setup token and apikey", 1), 
            ("Setup startup", 2)],
        ),
    ]
    sequence = inquirer.prompt(setup_choice)
    return sequence["choice"]

def setup(sequence):
	if sequence == 0:
		returner = [
			inquirer.Text('token', message='Input your discord token'),
			inquirer.Text('key', message='Input your api key')
		]

		setup = inquirer.prompt(returner)
		return setup["token"], setup["key"]
	elif sequence == 1:
		returner = [
			inquirer.Text('token', message='Input your discord token'),
			inquirer.Text('key', message='Input your api key')
		]

		setup = inquirer.prompt(returner)
		return setup["token"], setup["key"]
	else:
		print("An error occurred. Please consult the maintainer!")


if __name__ == "__main__":
    main()