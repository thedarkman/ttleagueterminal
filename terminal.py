#!/usr/bin/python

import json
import signal
import subprocess
from time import sleep

import RPi.GPIO as GPIO
from socketIO_client import SocketIO

import MFRC522

from TTLeague import Player, Match, Game

from Adafruit_CharLCD import Adafruit_CharLCD

from evdev import InputDevice, list_devices, categorize, ecodes, KeyEvent

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
                        lcd.message('Bye ...')
                        sleep(4)
                        lcd.clear()
                        subprocess.call("sudo shutdown -hP now", shell=True)
                    notFound = False
                    oldTag = uid
                    sleep(0.1)
                    return uid
    return None


def on_result_player(*args):
    print("received Player name: " + args[0]['name'] + " with tagId: " + args[0]['tagId'])
    lcd.clear()
    lcd.message('found player:\n{:16s}'.format(args[0]['name']))
    players.append(Player(args[0]['tagId'], args[0]['name']))


def on_ack_match():
    print('match was submitted successfully')


def search_player(nfcTag):
    socketIO = SocketIO(config['url'], verify=False)
    socketIO.on('resultPlayer', on_result_player)
    socketIO.on('error', on_error)
    socketIO.emit('requestPlayerByTagId', {'tagId': nfcTag})
    socketIO.wait(seconds=3)


def on_error(*args):
    print('Error received: ' + str(args[0]))


def on_refresh_data(*args):
    data = args[0]
    elo_changes = {}
    for player in data['players']:
        if player['name'] in last_players_names:
            print(player['name'] + ' '+ str(player['eloChange']))
            elo_changes.update({player['name']: player['eloChange']})

    if len(elo_changes.keys()) > 0:
        show_elo_change(elo_changes)


def add_match(match):
    socketIO = SocketIO(config['url'], verify=False)
    socketIO.on('ackMatch', on_ack_match)
    socketIO.on('error', on_error)
    socketIO.on('refreshData', on_refresh_data())
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
    lcd.set_cursor(int(_lcd_cols) - 4, 0)
    lcd.write8(ord('S'), True)
    lcd.set_cursor(int(_lcd_cols) - 4, 1)
    lcd.write8(ord(str(set)), True)
    # clear old points in this row
    lcd.set_cursor(int(_lcd_cols) - 2, row)
    lcd.write8(ord(' '), True)
    lcd.write8(ord(' '), True)
    # reposition
    lcd.set_cursor(int(_lcd_cols) - 2, row)
    lcd.blink(True)
    typed = 0
    points = 0
    # wait for keyboard input
    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            key = categorize(event)
            if key.keystate == KeyEvent.key_down:
                if key.keycode == 'KEY_KP1':
                    if typed == 0:
                        points += 10
                    else:
                        points += 1
                    typed += 1
                    print('writing 1 to row ' + str(row))
                    lcd.write8(ord('1'), True)
                elif key.keycode in keypad_map:
                    if typed == 0:
                        typed += 1
                        lcd.write8(ord(' '), True)
                    mapped = keypad_map[key.keycode]
                    print('mapped {:d} --> {:s}'.format(mapped, chr(mapped)))
                    typed += 1
                    lcd.write8(mapped, True)
                    points += int(chr(mapped))
            print('typed is now {:d} and points {:d}'.format(typed, points))
            if typed == 2:
                break
    lcd.blink(False)
    return points


def clear_players():
    global players
    players = []


def show_match_on_display(match):
    lcd.clear()
    player_str = '{:6s} - {:6s}'.format(match.player1.name, match.player2.name)
    lcd.message(player_str)


def show_elo_change(elo_changes):
    row = 0
    lcd.clear()
    for player, change in elo_changes.items():
        lcd.set_cursor(0, row)
        print('Elo change for player {:s} is {:d}'.format(player, change))
        msg = '{:11s} {:4d}'.format(player, change)
        for c in msg:
            lcd.write8(ord(c))
        row += 1

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

lcdConfig = config['lcd']
_lcd_rows = lcdConfig['lines']
_lcd_cols = lcdConfig['cols']

notFound = True

dev = InputDevice(config['keyboardDevice'])

# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

GPIO.setwarnings(False)

keypad_map = {'KEY_KP0': 48, 'KEY_KP2': 50, 'KEY_KP3': 51,
              'KEY_KP4': 52, 'KEY_KP5': 53, 'KEY_KP6': 54, 'KEY_KP7': 55,
              'KEY_KP8': 56, 'KEY_KP9': 57}

# Create an object of the class MFRC522
MIFAREReader = MFRC522.MFRC522()


lcd = Adafruit_CharLCD(lcdConfig['rs'], lcdConfig['en'], lcdConfig['d4'],
                       lcdConfig['d5'], lcdConfig['d6'], lcdConfig['d7'],
                       _lcd_cols, _lcd_rows)

lcd.clear()
lcd.message("Welcome to the\nTTLeagueTerminal")
print "Welcome to the TTLeagueTerminal"
sleep(5)

oldTag = ''

while True:
    lcd.clear()
    while (2 - len(players)) > 0:
        print('waiting for {:d} players to scan ...'.format((2 - len(players))))
        lcd.clear()
        lcd.message('waiting for {:d}\nplayers to scan'.format((2 - len(players))))
        rawTag = wait_for_tag()
        nfcTag = hex_string_from_nfc_tag(rawTag)
        print('player tagId scanned - {}'.format(nfcTag))
        lcd.clear()
        lcd.message('scan successful\nsearching player ...')
        search_player(nfcTag)

    print('seems we have both player: ' + str([p.name for p in players]))
    last_players_names = [players[0].name, players[1].name]
    sleep(1)
    lcd.clear()
    lcd.message('Players found\ncreating match')
    print('creating match')
    match = Match(players[0], players[1])
    sleep(3)
    lcd.clear()
    lcd.message('{}\n{}'.format(players[0].name, players[1].name))
    for x in range(1, 5):
        home = wait_for_points(x, 0)
        guest = wait_for_points(x, 1)
        sleep(2)
        clear_points_display()
        if home == 0 and guest == 0:
            break
        match.add_game(Game(int(home), int(guest)))
    print('Match finished: ' + str(match.get_match_data()))
    show_match_on_display(match)
    sleep(2)
    add_match(match)
    clear_players()