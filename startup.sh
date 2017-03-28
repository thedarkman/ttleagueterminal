#!/bin/bash

cd /home/pi/ttleagueterminal
git pull
if [ $? -eq 0 ]; then
   python terminal.py
fi
