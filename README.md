# ttleagueterminal
This project will run on a battery powered device (RaspberryPi Zero W)
to be able to send game points to a running node.js app acting as server

# Dependencies
Some of these packages and system tools are already included in the full raspian distrobution, but i'm always using the lite images 
* Git
  * Install via ``sudo apt-get install git``
* Python-Dev
  * Install via ``sudo apt-get install python-dev``
* Python-Pip
  * Install via ``sudo apt-get install python-pip``
* Python-evdev - https://python-evdev.readthedocs.io/en/latest/index.html
  * Install via ``sudo pip install evdev``
* SPI-Py - https://github.com/lthiery/SPI-Py
  * Clone git repository: ``git clone https://github.com/lthiery/SPI-Py.git``
  * Change into the directory ``cd SPI-Py``
  * Install via ``sudo python setup.py install``
* MFRC522 - https://github.com/mxgxw/MFRC522-python
  * Because i had to patch it, it is included in code
* Python package requirements could be installed via ``sudo pip install -r requirements.txt``
  * socketIO-client
  * evdev
  * adafruit-charlcd

# Config 
* Clone git repository to ``/home/pi``
* Install dependencies
* Config backend and LCD
  * See options in file _config.default.json_ (needs to be edited and saved as _config.json_)
  * LCD connection needs to be configured (HD44780 controller compatible)
* To boot into "app" add a line ``su - pi -c '/home/pi/ttleagueterminal/startup.sh &'`` into file ``/etc/rc.local`` before the exit instruction
  * this command changes into a shell for user ```pi``` and starts the terminal
