#!/usr/bin/python

import json
import signal
import subprocess
import socket
from time import sleep
from datetime import datetime

import RPi.GPIO as GPIO
from socketIO_client import SocketIO

import MFRC522

from TTLeague import Player, Match, Game

from Adafruit_CharLCD import Adafruit_CharLCD

from evdev import InputDevice, list_devices, categorize, ecodes, KeyEvent

ATT_LEAGUE_TERMINAL = 'ATTLeague Terminal'


# Capture SIGINT for cleanup when the script is aborted
def end_read(signal, frame):
    global notFound
    print "Ctrl+C captured, ending read."
    notFound = False
    lcd.clear()
    GPIO.cleanup()


def hex_string_from_nfc_tag(tag):
    return '{:x}{:x}{:x}{:x}'.format(tag[0], tag[1], tag[2], tag[3])


def wait_for_tag():
    global notFound
    global oldTag
    notFound = True
    while notFound:

        # Scan for cards
        (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

        # If a card is found
        if status == MIFAREReader.MI_OK:
            # print "tag detected"

            # Get the UID of the card
            (status, uid) = MIFAREReader.MFRC522_Anticoll()

            # If we have the UID, continue
            if status == MIFAREReader.MI_OK:
                # print "tag id read"
                if oldTag != uid:
                    if hex_string_from_nfc_tag(uid) == config['endTagId']:
                        print('Exit tag scanned, shutting down in 2 seconds ...')
                        lcd.clear()
                        lcd.message('Time to say\n\n      goodbye')
                        sleep(4)
                        lcd.clear()
                        subprocess.call("sudo shutdown -hP now", shell=True)
                    notFound = False
                    oldTag = uid
                    sleep(0.1)
                    return uid
    return None


def on_result_player(*args):
    _player_data = args[0]
    print("received Player name: " + _player_data['name'] + " with tagId: " + _player_data['tagId'])
    lcd.clear()
    fStr = '{:^' + str(_lcd_cols) + 's}\n{:^' + str(_lcd_cols) + 's}\n{:^' + str(_lcd_cols) + 's}\n{:>' + str(
        _lcd_cols) + 's}'
    lcd.message(fStr.format(ATT_LEAGUE_TERMINAL, 'found player:', _player_data['name'],
                            'Elo: {:d}'.format(_player_data['elo'])))
    players.append(Player(_player_data['tagId'], _player_data['name']))


def on_ack_match(*args):
    print('match was submitted successfully; lastEloChange {}'.format(str(args[0])))


def search_player(nfcTag):
    socketIO = SocketIO(config['url'], verify=False)
    socketIO.on('resultPlayer', on_result_player)
    socketIO.on('error', on_error)
    socketIO.emit('requestPlayerByTagId', {'tagId': nfcTag})
    socketIO.wait(seconds=3)


def on_error(*args):
    print('Error received: ' + str(args[0]))
    lcd.clear()
    lcd.message('Error received:\n' + str(args[0]))
    sleep(2)


def refresh_data():
    socketIO = SocketIO(config['url'], verify=False)
    socketIO.on('error', on_error)
    socketIO.on('refreshedData', on_refreshed_data)
    socketIO.emit('refreshData')
    socketIO.wait(seconds=3)


def on_refreshed_data(*args):
    global dataFun
    data = args[0]
    print('got refreshed data')
    dataFun = data
    elo_changes = {}
    for player in data['players']:
        if player['name'] in last_players_names:
            elo_changes.update({player['name']: player['eloChange']})

    if len(elo_changes.keys()) > 0:
        show_elo_change(elo_changes)


def add_match(match):
    if _log_matches:
        with open("match.log", "a") as log_file:
            log_line = '{:%Y-%m-%d %H:%M:%S} {}\n'.format(datetime.now(), match.match_data_for_log())
            log_file.write(log_line)
    socketIO = SocketIO(config['url'], verify=False)
    socketIO.on('ackMatch', on_ack_match)
    socketIO.on('error', on_error)
    socketIO.on('refreshedData', on_refreshed_data)
    socketIO.emit('addMatch', match.get_match_data())
    socketIO.wait(seconds=5)


def clear_points_display():
    # clear old points
    for row in [1, 2]:
        lcd.set_cursor(int(_lcd_cols) - 2, row)
        lcd.write8(ord(' '), True)
        lcd.write8(ord(' '), True)


def wait_for_points(set, row):
    # print current set
    init_position = int(_lcd_cols) - 2
    lcd.set_cursor(init_position - 2, 0)
    lcd.write8(ord('S'), True)
    lcd.set_cursor(init_position - 2, 1)
    lcd.write8(ord(str(set)), True)
    # clear old points in this row
    lcd.set_cursor(init_position, row)
    lcd.write8(ord(' '), True)
    lcd.write8(ord(' '), True)
    # reposition
    lcd.set_cursor(init_position, row)
    lcd.blink(True)
    typed = 0
    points = 0
    digits = []
    # wait for keyboard input
    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            key = categorize(event)
            if key.keystate == KeyEvent.key_down:
                if key.keycode == 'KEY_KPENTER':
                    if len(digits) > 0:
                        points = int(digits.pop())
                        if len(digits) > 0:
                            points += int(digits.pop()) * 10
                    break
                elif key.keycode == 'KEY_DELETE' or key.keycode == 'KEY_BACKSPACE':
                    if len(digits) > 0:
                        digits.pop()
                        new_position = init_position + (typed - 1)
                        lcd.set_cursor(new_position, row)
                        lcd.write8(ord(' '), True)
                        lcd.set_cursor(new_position, row)
                        typed -= 1
                elif key.keycode in keypad_map and typed < 2:
                    typed += 1
                    mapped = keypad_map[key.keycode]
                    digits.append(chr(mapped))
                    lcd.write8(mapped, True)
                    if typed == 2:
                        # set cursor on last digit to wait for enter
                        lcd.set_cursor(init_position + 1, row)
    lcd.blink(False)
    return points


def wait_for_enter():
    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            key = categorize(event)
            if key.keystate == KeyEvent.key_down:
                if key.keycode == 'KEY_KPENTER':
                    break


def clear_players():
    global players
    players = []


def show_sets_on_display(games):
    # called after a set was added to the game
    home = ''
    guest = ''
    for game in games:
        home += '{:2d} '.format(game.home)
        guest += '{:2d} '.format(game.guest)

    lcd.set_cursor(0, 2)
    for c in home:
        lcd.write8(ord(c), True)
    lcd.set_cursor(0, 3)
    for c in guest:
        lcd.write8(ord(c), True)


def show_match_on_display(match):
    lcd.clear()
    player_str = '{:6s} - {:6s}\n'.format(match.player1.name, match.player2.name)

    for game in match.games:
        # home points
        player_str += "{:2d} ".format(game.home)
    player_str += "\n"
    for game in match.games:
        # guest points
        player_str += "{:2d} ".format(game.guest)
    lcd.message(player_str)


def show_elo_change(elo_changes):
    row = 2
    lcd.clear()
    lcd.message('Elo changes:')
    for player, change in elo_changes.items():
        lcd.set_cursor(0, row)
        fStr = '{:' + str(_lcd_cols - 5) + 's} {:+4d}'
        msg = fStr.format(player, change)
        print(msg)
        for c in msg:
            lcd.write8(ord(c), True)
        row += 1


def show_admin_screen():
    if 'players' in dataFun:
        lcd.clear()
        for i in range(0, 4):
            p = dataFun['players'][i]
            lcd.set_cursor(0, i)
            lcd.message('  {}'.format(p['name']))
        lcd.set_cursor(0, 0)
        lcd.write8(ord('\x00'), True)
        sleep(3)


def get_ip_address():
    return [
        (s.connect(('8.8.8.8', 53)),
         s.getsockname()[0],
         s.close()) for s in
        [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]
    ][0][1]


########################################################################
#  Script start here
########################################################################

socketIO = None
players = []
last_players_names = []

# init empty configuration
config = {}

try:
    # try to load config from file
    config = json.load(open('config.json'))
except Exception, e:
    print("Error while getting config: " + str(e))
    exit()

if 'url' not in config.keys() or \
                'keyboardDevice' not in config.keys() or \
                'lcd' not in config.keys():
    error = 'Missing configuration key. Please check config.default.json file for configuration'
    raise KeyError(error)

lcdConfig = config['lcd']
_lcd_rows = lcdConfig['lines']
_lcd_cols = lcdConfig['cols']

_log_matches = False
if 'logMatches' in config.keys():
    _log_matches = bool(config['logMatches'])

notFound = True

dev = InputDevice(config['keyboardDevice'])

# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

GPIO.setwarnings(False)

keypad_map = {'KEY_KP0': 48, 'KEY_KP1': 49, 'KEY_KP2': 50, 'KEY_KP3': 51,
              'KEY_KP4': 52, 'KEY_KP5': 53, 'KEY_KP6': 54, 'KEY_KP7': 55,
              'KEY_KP8': 56, 'KEY_KP9': 57}

# Create an object of the class MFRC522
MIFAREReader = MFRC522.MFRC522()

# some special char for the cld
_arrow_right = [16, 24, 20, 18, 20, 24, 16, 0]
_arrow_right_filled = [16, 24, 28, 30, 28, 24, 16, 0]

lcd = Adafruit_CharLCD(lcdConfig['rs'], lcdConfig['en'], lcdConfig['d4'],
                       lcdConfig['d5'], lcdConfig['d6'], lcdConfig['d7'],
                       _lcd_cols, _lcd_rows)

# up to 8 user defined chars are allowed on location 0..7
lcd.create_char(0, _arrow_right)
lcd.create_char(1, _arrow_right_filled)

ip = get_ip_address()
# welcome = "Welcome to the\nTTLeagueTerminal\n\nIP: {}".format(ip)
welcome = '{:^' + str(_lcd_cols) + 's}\n{:^' + str(_lcd_cols) + 's}\n{:^' + str(_lcd_cols) + 's}\nIP: {}'
welcome = welcome.format(ATT_LEAGUE_TERMINAL, 'Welcome to the', 'terminal', ip)
lcd.clear()
lcd.message(welcome)
print(welcome)
sleep(3)

startMessage = '{:^' + str(_lcd_cols) + 's}\n\n{:^' + str(_lcd_cols) + 's}\n{:^' + str(_lcd_cols) + 's}'
lcd.clear()
lcd.message(startMessage.format(ATT_LEAGUE_TERMINAL, 'Press enter', 'to start ...'))
wait_for_enter()

# get actual data from server
lcd.clear()
secondMessage = '{:^' + str(_lcd_cols) + 's}\n\n{:^' + str(_lcd_cols) + 's}'
lcd.message(secondMessage.format(ATT_LEAGUE_TERMINAL, 'connecting ...'))
refresh_data()

dataFun = {}
oldTag = ''
while True:
    lcd.clear()
    while (2 - len(players)) > 0:
        print('waiting for {:d} players to scan ...'.format((2 - len(players))))
        lcd.clear()
        waitMessage = '{:^' + str(_lcd_cols) + 's}\n\n{:^' + str(_lcd_cols) + 's}\n{:^' + str(_lcd_cols) + 's}'
        waitMessage = waitMessage.format(ATT_LEAGUE_TERMINAL, 'waiting for {:d}'.format((2 - len(players))),
                                         'players to scan')
        lcd.message(waitMessage)
        rawTag = wait_for_tag()
        nfcTag = hex_string_from_nfc_tag(rawTag)
        if nfcTag == config['adminTag']:
            show_admin_screen()
            continue
        print('player tagId scanned - {}'.format(nfcTag))
        lcd.clear()
        scanMessage = '{:^' + str(_lcd_cols) + 's}\n\n{:^' + str(_lcd_cols) + 's}\n{:^' + str(_lcd_cols) + 's}'
        scanMessage = scanMessage.format(ATT_LEAGUE_TERMINAL, 'scan successful', 'searching player ...')
        lcd.message(scanMessage)
        search_player(nfcTag)

    print('seems we have both player: ' + str([p.name for p in players]))
    last_players_names = [players[0].name, players[1].name]
    lcd.clear()
    foundMessage = '{:^' + str(_lcd_cols) + 's}\n{:<' + str(_lcd_cols - 2) + 's}\n{:>' + str(
        _lcd_cols) + 's}\n{:^' + str(_lcd_cols) + 's}'
    foundMessage = foundMessage.format('Players found', players[0].name + ' -', players[1].name, 'creating match ...')
    # 'Players found\n{:s}\n{:s}\ncreating match ...'.format(players[0].name, players[1].name)
    lcd.message(foundMessage)
    print('creating match')
    match = Match(players[0], players[1])
    sleep(2)
    lcd.clear()
    lcd.message('{}\n{}'.format(players[0].name, players[1].name))
    for x in range(1, 6):
        home = wait_for_points(x, 0)
        guest = wait_for_points(x, 1)
        clear_points_display()
        if home == 0 and guest == 0:
            break
        match.add_game(Game(int(home), int(guest)))
        show_sets_on_display(match.games)
    print('Match finished: ' + str(match.get_match_data()))
    if len(match.games) > 0:
        show_match_on_display(match)
        sleep(2)
        add_match(match)
    clear_players()
