#!/usr/bin/python

from TTLeague import Match, Game, Player
import RPi.GPIO as GPIO
import MFRC522
import signal
import json
import requests
from time import sleep

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

def getHexStringFromScannedTag(tag):
    return '{:x}{:x}{:x}{:x}'.format(tag[0], tag[1], tag[2], tag[3])



def getPlayer(nfcTag):
    params = {'clientToken': config['secretKey']}
    url = '{}/user/{}'.format(config['baseUrl'], nfcTag)
    #print("requesting "+ url)
    r = requests.get(url, params=params)
    if r.status_code == requests.codes.ok:
       obj = r.json()
       pObj = Player(obj['nfcTag'], obj['username'])
       return pObj
    else:
       print("server returned (status code: {:d}): {:s} ".format(r.status_code, r.text))
       
# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

GPIO.setwarnings(False)

# Create an object of the class MFRC522
MIFAREReader = MFRC522.MFRC522()

print "Welcome to the TT League Terminal"

oldTag = ''
def waitForTag():
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


print "waiting now for player 1 scan ..."
rawTag = waitForTag()
nfcTag = getHexStringFromScannedTag(rawTag)
print('player 1 - {}'.format(nfcTag))

p1 = getPlayer(nfcTag)
print(str(p1))
print('player 1 found, now waiting for player 2 scan ...')
print

rawTag = waitForTag()
nfcTag = getHexStringFromScannedTag(rawTag)
print('player 2 - {}'.format(nfcTag))

p2 = getPlayer(nfcTag)
print(str(p2))
print
print
print('(Hopefully) both found, let\'s play table tennis')
