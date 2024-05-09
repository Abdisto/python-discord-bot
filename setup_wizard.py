#!/usr/bin/env python3.10

import subprocess
import os
import sys
sys.path.append(os.path.realpath('.'))
import inquirer
import argparse
import xml.etree.ElementTree as ET

def main():
    try:
        os.setuid(0)
        service_file_path = '/etc/systemd/system/discord_bot_script.service'
        sh_file_path = f'{os.path.dirname(os.path.abspath(__file__))}/discord_bot.sh'
        relative_path = f'{os.path.dirname(os.path.abspath(__file__))}'

        global sequence
        discord_token, lavalink_host, lavalink_port, lavalink_pass = config()

        if sequence == 0 or sequence == 2:
            configure_service(sh_file_path, relative_path, service_file_path)
            print('Finished successfully, please reboot your system.')
        else:
            print('Finished successfully.')

    except Exception as e:
        print(f'Error occurred in main(), please consult the maintainer: {e}')

def configure_service(sh_file_path, relative_path, service_file_path):
    genShFile(sh_file_path, relative_path)
    genServiceFile(service_file_path, relative_path)

    subprocess.run(['chmod', '+x', sh_file_path])
    subprocess.run(['chown', 'root', sh_file_path])
    subprocess.run(['chmod', '+x', service_file_path])

    subprocess.run(['systemctl', 'daemon-reload'])
    subprocess.run(['systemctl', 'start', 'discord_bot_script.service'])
    subprocess.run(['systemctl', 'enable', 'discord_bot_script.service'])

def genShFile(sh_file_path, relative_path):
    sh_file_content = f'''#!/bin/bash
set -x
if screen -list | grep -qw \'discord_bot\'; then
    echo \'Discord bot is already running.\'
else
    cd {relative_path}
    # Start the Discord bot in a detached screen session
    /usr/bin/screen -dmS discord_bot /bin/bash -c \'python3.10 ./bot_init.py; exec /bin/bash\'
    echo \'Discord bot started.\'
fi'''
    os.chdir(relative_path)

    with open(sh_file_path, 'w') as file:
        file.write(sh_file_content)

def genServiceFile(service_file_path, relative_path):
    service_file_content = f'''[Unit]
Description=discord-bot-script
[Unit]

Description=Lavalink Service
After=lavalink.target

[Service]
Type=oneshot
ExecStart=/bin/su - {os.getlogin()} -c \'{relative_path}/discord_bot.sh\'

Restart=on-failure

RestartSec=5s

[Install]
WantedBy=multi-user.target'''

    os.chdir('/etc/systemd/system')

    with open(service_file_path, 'w') as file:
        file.write(service_file_content)



def get_config():
    try:
        tree = ET.parse('config.xml')
        root = tree.getroot()

        discord_token = root.find('.//discord_token').text
        lavalink_host = root.find('.//lavalink_host').text
        lavalink_port = root.find('.//lavalink_port').text
        lavalink_pass = root.find('.//lavalink_pass').text

        return discord_token, lavalink_host, lavalink_port, lavalink_pass
    except Exception as e:
        print(f'Error while trying to read the config file: {e}')

def config():
    global sequence

    setup_choice = [
        inquirer.List(
            'choice',
            message='What should be setup??',
            choices=[('Setup discord token, lavalink and startup.', 0),
            ('Setup token and lavalink.', 1),
            ('Setup startup.', 2)],
        ),
    ]
    setup = inquirer.prompt(setup_choice)
    sequence = setup['choice']

    if sequence == 2:
        return None, None, None, None

    elif sequence != 2 :
        try:
            returner = [
                inquirer.Text('discord_token', message='Input your discord token'),
                inquirer.Text('lavalink_host', message='Input your lavalink host <default is localhost>'),
                inquirer.Text('lavalink_port', message='Input your lavalink port <default is 2333>'),
                inquirer.Text('lavalink_pass', message='Input your lavalink password <default is youshallnotpass>'),
            ]
            setup = inquirer.prompt(returner)

            root = ET.Element('Config')
            cl = ET.Element('Configurations')

            ET.SubElement(cl, 'discord_token').text = str(setup['discord_token'])
            ET.SubElement(cl, 'lavalink_host').text = str(setup['lavalink_host']) if str(setup['lavalink_host']) != '' else 'localhost'
            ET.SubElement(cl, 'lavalink_port').text = str(setup['lavalink_port']) if str(setup['lavalink_port']) != '' else '2333'
            ET.SubElement(cl, 'lavalink_pass').text = str(setup['lavalink_pass']) if str(setup['lavalink_pass']) != '' else 'youshallnotpass'

            root.append(cl)
            tree = ET.ElementTree(root)
            with open('config.xml', 'wb') as files:
                tree.write(files)

            return setup['discord_token'], setup['lavalink_host'], setup['lavalink_port'], setup['lavalink_pass']
        except Exception as e:
            print(f'Error occurred in config(), please consult the maintainer: {e}')
    else:
        print(f'How did we get here?')

if __name__ == '__main__':
    main()
