#!/path/to/python3.10

import os
from datetime import datetime, timedelta
import subprocess
import time as t

class TextColor:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'

def log_error(error_message):
    logs_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    today = datetime.now().strftime('%d.%m.%Y')
    log_filename = f'error_{today}.log'
    log_filepath = os.path.join(logs_dir, log_filename)

    with open(log_filepath, 'a') as log_file:
        log_file.write(f'{datetime.now().strftime("%H:%M:%S")} - {error_message}\n')

    cleanup_logs(logs_dir)

def cleanup_logs(logs_dir):
    now = datetime.now()
    for filename in os.listdir(logs_dir):
        file_path = os.path.join(logs_dir, filename)
        if os.path.isfile(file_path):
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if now - file_mod_time > timedelta(days=10):
                os.remove(file_path)
                print(f'Deleted old log file: {filename}')

def print_text(text, color):
    print(f'{color}{text}{TextColor.RESET}', end='')

def print_timestamp(text='', title='', mode=0, url=''):
    date = datetime.now().strftime('%d.%m.%y')
    time = datetime.now().strftime('%H:%M:%S')
    if mode == 0: # plain text with possible title
        print(f'{TextColor.RESET}[{TextColor.RED}{date}{TextColor.RESET}| {TextColor.PURPLE}{time}{TextColor.RESET}] {TextColor.RESET}{title}{TextColor.YELLOW}{text}{TextColor.RESET}\n', end='')
        process = subprocess.Popen('echo 0 > /sys/class/leds/working/brightness', stdout=subprocess.PIPE, shell=True)
    elif mode == 1: # error
        print(f'{TextColor.RESET}[{TextColor.RED}{date}{TextColor.RESET}| {TextColor.PURPLE}{time}{TextColor.RESET}] {TextColor.RED}{title}{TextColor.RESET}{text}\n', end='')
        process = subprocess.Popen('echo 1 > /sys/class/leds/auxiliary/brightness', stdout=subprocess.PIPE, shell=True)
        t.sleep(2)
        log_error(str(text))
        process = subprocess.Popen('echo 0 > /sys/class/leds/auxiliary/brightness', stdout=subprocess.PIPE, shell=True)
    elif mode == 2: # hyperlink
        #hyperlink = f"\x1b]8;;{url}\x1b\\{text}\x1b]8;;\x1b\\"
        hyperlink = f"{text} - {url}"
        print(f'{TextColor.RESET}[{TextColor.RED}{date}{TextColor.RESET}| {TextColor.PURPLE}{time}{TextColor.RESET}] {TextColor.RESET}{title}{TextColor.YELLOW}{hyperlink}\n', end='')

def Ori():
	return '''
	    :  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣷⣀⠀⠀⠀⠀⠀⣤⡀⠲⣤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢻⣿⣿⣤⡀⠀⠀⠀⣛⣿⣾⣿⣿⣶⣶⣦⣤⠀⠀⠀⠀⠀⠀⠀⠀🤍
⠀⠀⠀⠀⠀⠀⢿⣿⣿⣿⣿⣿⣇⢇⢀⣴⣿⣿⣿⣿⣤⠊⣿⣦⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠙⢿⣯⣧⣷⢷⣶⣶⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣤⣿⣧⣿⣿⣿⣿⣿⣿⡿⣿⣿⣿⣿⡿⠉⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣤⣿⣿⣿⣿⣿⣿⡿⠋⠁⠀⣤⣿⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠒⠿⢿⣿⣿⠿⠿⠛⠉⢀⣤⣤⣶⣿⣿⣿⣿⣯⠁⠀⠀⢀⣾⣿⣷⢆⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⣤⣿⣿⣿⣿⣿⣿⣯⣾⠋⠿⣷⣤⣤⣿⣿⣷⣷⣧⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⣿⣿⢏⣿⣿⣿⣿⣦⢄⢈⢻⣿⣿⣿⡿⠁⠀⠀
⠀⠀⠀⠀⠀⠀⢠⢔⠸⣿⣿⣿⣿⣿⡀⢫⣿⣿⣿⣿⣎⣇⠇⠛⠋⠁⠀⠀⠀⠀
⠀⠀⠀⢀⢆⠃⠀⠀⠀⠻⣟⣿⣿⠛⠁⢀⣠⣾⣿⣿⣟⣧⢀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⢠⣏⠀⠀⠀⠀⠀⠀⠀⠈⠀⢀⣤⣾⣿⠟⠋⢀⣯⠓⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⢸⣗⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⣿⠁⠀⠀⠀⢻⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠻⣷⣦⣆⣦⣦⣦⣦⣶⣶⣮⣯⠀⠀⠀⠀ ⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠉⠉⠉⠉⠉⠉⠉⢹⡿⣿⣶⠀⠀ ⢀⣾⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⠟⠀⢈⣿⣿⠀ ⠻⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠁⠀⣠⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⠛⠀

	'''
