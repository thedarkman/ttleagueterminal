#!/bin/bash

cd /home/pi/ttleagueterminal
git pull
if [ $? -eq 0 ]; then
   python terminal.py >> /home/pi/ttleagueterminal/terminal.log 2>&1
fi