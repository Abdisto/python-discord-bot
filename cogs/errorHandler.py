#!/path/to/python3.10

from datetime import datetime
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

def print_text(text, color):
    print(f'{color}{text}{TextColor.RESET}', end='')

def print_timestamp(text='', title='', mode=0, url=''):
    date = datetime.now().strftime('%d.%m.%y')
    time = datetime.now().strftime('%H:%M:%S')
    if mode == 0: # plain text with possible title
        print(f'{TextColor.RESET}[{TextColor.RED}{date}{TextColor.RESET}| {TextColor.PURPLE}{time}{TextColor.RESET}] {TextColor.RESET}{title}{TextColor.YELLOW}{text}{TextColor.RESET}\n', end='')
        #process = subprocess.Popen('echo 0 > /sys/class/leds/working/brightness', stdout=subprocess.PIPE, shell=True)
    elif mode == 1: # error
        print(f'{TextColor.RESET}[{TextColor.RED}{date}{TextColor.RESET}| {TextColor.PURPLE}{time}{TextColor.RESET}] {TextColor.RED}{title}{TextColor.RESET}{text}\n', end='')
        #process = subprocess.Popen('echo 1 > /sys/class/leds/auxiliary/brightness', stdout=subprocess.PIPE, shell=True)
        t.sleep(2)
        #process = subprocess.Popen('echo 0 > /sys/class/leds/auxiliary/brightness', stdout=subprocess.PIPE, shell=True)
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
