# ttleagueterminal
This project will run on a battery powered device (RaspberryPi Zero W)
to be able to send game points to a running node.js app acting as server

# Dependencies
* Python-evdev - https://python-evdev.readthedocs.io/en/latest/index.html
  * Install via ``sudo pip install evdev``
* Adafruit CharLCD - https://github.com/adafruit/Adafruit_Python_CharLCD
  * Or now possible to install via ``sudo pip install adafruit-charlcd``
* SocketIO Client 0.5 - https://pypi.python.org/pypi/socketIO-client/0.5.7.2
* RPi - As running on a Raspberry Pi Zero W
* SPI-Py - https://github.com/lthiery/SPI-Py
* MFRC522 - https://github.com/mxgxw/MFRC522-python

# Config 
* Clone git repository to ``/home/pi``
* Install dependencies
* Config backend and LCD
  * See options in file _config.default.json_ (needs to be edited and saved as _config.json_)
  * LCD connection needs to be configured (HD44780 controller compatible)
* To boot into "app" add a line ``su - pi -c '/home/pi/ttleagueterminal/startup.sh &'`` into file ``/etc/rc.local`` before the exit instruction
  * this command changes into a shell for user ```pi``` and starts the terminal
