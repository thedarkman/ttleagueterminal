#!/usr/bin/python

import json
import signal
from time import sleep

import RPi.GPIO as GPIO
from socketIO_client import SocketIO

import MFRC522

from TTLeague import Player

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
                 notFound = False
                 oldTag = uid
                 sleep(0.1)
                 return uid


def on_result_player(*args):
    print("received Player name: " + args[0]['name'] + " with tagId: " + args[0]['tagId'])
    players.append(Player(args[0]['tagId'], args[0]['name']))


def search_player(nfcTag):
    socketIO = SocketIO(config['url'], verify=False)
    socketIO.on('resultPlayer', on_result_player)
    socketIO.emit('requestPlayerByTagId', {'tagId': nfcTag})
    socketIO.wait(3)



while True:
    while (2-len(players)) > 0:
        print('waiting for {:d} players to scan ...'.format((2-len(players))))
        rawTag = wait_for_tag()
        nfcTag = hex_string_from_nfc_tag(rawTag)
        print('player tagId scanned - {}'.format(nfcTag))
        search_player(nfcTag)


    print "seems we have both player: "+ str([p.name for p in players])

    # loop for games to play 
 
    exit()
