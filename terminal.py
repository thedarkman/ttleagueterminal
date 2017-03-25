#!/usr/bin/python

import json
import signal
import subprocess
from time import sleep

import RPi.GPIO as GPIO
from socketIO_client import SocketIO

import MFRC522

from TTLeague import Player, Match, Game

socketIO = None
players = []

# init empty configuration
config = {}

try:
   # try to load config from file
   config = json.load(open('config.json'))
except Exception, e:
   print("Error while getting config: "+ str(e))
   exit()

notFound = True

# Capture SIGINT for cleanup when the script is aborted
def end_read(signal, frame):
    global notFound
    print "Ctrl+C captured, ending read."
    notFound = False
    GPIO.cleanup()


def hex_string_from_nfc_tag(tag):
    return '{:x}{:x}{:x}{:x}'.format(tag[0], tag[1], tag[2], tag[3])

# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

GPIO.setwarnings(False)

# Create an object of the class MFRC522
MIFAREReader = MFRC522.MFRC522()

print "Welcome to the TT League Terminal"

oldTag = ''


def wait_for_tag():
    global notFound
    global oldTag
    notFound = True
    while notFound:

       # Scan for cards
       (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

       # If a card is found
       if status == MIFAREReader.MI_OK:
           #print "tag detected"

           # Get the UID of the card
           (status,uid) = MIFAREReader.MFRC522_Anticoll()

           # If we have the UID, continue
           if status == MIFAREReader.MI_OK:
              #print "tag id read"
              if oldTag != uid:
                 if hex_string_from_nfc_tag(uid) == config['endTagId']:
                    print('Exit tag scanned, shutting down in 2 seconds ...')
                    sleep(2)
                    subprocess.call("sudo shutdown -hP now", shell=True)
                 notFound = False
                 oldTag = uid
                 sleep(0.1)
                 return uid


def on_result_player(*args):
    print("received Player name: " + args[0]['name'] + " with tagId: " + args[0]['tagId'])
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
    print('Error received: '+ str(args[0]))


def add_match(match):
    socketIO = SocketIO(config['url'], verify=False)
    socketIO.on('ackMatch', on_ack_match)
    socketIO.on('error', on_error)
    socketIO.emit('addMatch', match.get_match_data())
    socketIO.wait(seconds=5)


def clear_players():
    global players
    players = []


while True:
    while (2-len(players)) > 0:
        print('waiting for {:d} players to scan ...'.format((2-len(players))))
        rawTag = wait_for_tag()
        nfcTag = hex_string_from_nfc_tag(rawTag)
        print('player tagId scanned - {}'.format(nfcTag))
        search_player(nfcTag)

    print('seems we have both player: '+ str([p.name for p in players]))
    print('creating match')
    match = Match(players[0], players[1])
    for x in (1, 2, 3):
        # loop for games to play
        s = raw_input('Enter values for set {:d} (or X for end): '.format(x))
        if s == 'X':
            break
        points = s.split(':')
        match.add_game(Game(int(points[0]), int(points[1])))

    print('Match finished: '+ str(match.get_match_data()))
    add_match(match)
    clear_players()
