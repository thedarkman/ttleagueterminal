import RPi.GPIO as GPIO
import MFRC522
import signal
from time import sleep


notFound = True

# Capture SIGINT for cleanup when the script is aborted
def end_read(signal,frame):
    global notFound
    print "Ctrl+C captured, ending read."
    notFound = False
    GPIO.cleanup()

# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

# Create an object of the class MFRC522
MIFAREReader = MFRC522.MFRC522()

print "Welcome to the TT League Terminal"

Player1Id = ""
Player2Id = ""

def waitForTag():
    global notFound
    notFound = True
    while notFound:

       # Scan for cards
       (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

       # If a card is found
       if status == MIFAREReader.MI_OK:
           print "tag detected"

           # Get the UID of the card
           (status,uid) = MIFAREReader.MFRC522_Anticoll()

           # If we have the UID, continue
           if status == MIFAREReader.MI_OK:
              print "tag id read"
              notFound = False
              return uid


print "waiting now for player 1 scan ..."
player1 = waitForTag()
print 'player 1 - %x%x%x%x' % (player1[0], player1[1], player1[2], player1[3])
sleep(2)
print "player 1 found, now waiting for player 2 scan ..."
player2 = waitForTag()
print 'player 2 - %x%x%x%x' % (player2[0], player2[1], player2[2], player2[3])
print
print
print "Both found, let's play table tennis"
