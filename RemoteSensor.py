#!/usr/bin/env python
#
#
'''
## License
The MIT License (MIT)
GrovePi for the Raspberry Pi: an open source platform for connecting Grove Sensors to the Raspberry Pi.
Copyright (C) 2017  Dexter Industries
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''
from grovepi import *
from grove_rgb_lcd import *
import os
import math
import json
import requests
from time import gmtime, strftime, sleep

# Define ports for the sensors
lightSensor = 0         # Light Sensor
tempHumSensor = 4      # Humidity Sensor

REST_SERVER = "http://192.168.0.231:8080/reading"
HEADER = {'Content-type': 'application/json'}
INSTANCE = 101

# set the name of the JSON file to write to
filename = "/var/www/html/temp_hum_history.json"
backlog = []

# Define variables used throughout script
daylight = False        # Boolean to determine if it is daylight hours
lastTime = 0            # Last write to databse file, in seconds from epoch

lastText = ""		# Initialize last test written - to cut down on flicker
newFile = False
cycleTime = 2          # The frequency at which the script runs
sensorCycle = 5      # The number of seconds between sensor recordings

# Check if filename exists and is valid
try:
        with open(filename, 'rt') as f:
                firstLine = f.readline()                        # Read first line of output file
        if firstLine != '{ "localReadings": [ ':                 # If the first line is not correct
                with open(filename, 'wt') as f:                 # Overwrite and start new file
                        f.write('{ "localReadings": [\n')
                        f.write('])')
                        newFile = True
except IOError:
        with open(filename, 'wt') as f:                         # If filename does not exist
                f.write('{ "localReadings:" [ \n')
                f.write('])')
                newFile = True

while True:
        currLight = analogRead(lightSensor)                     # Read light sensor
        # print(currLight)                                        # Troubleshooting
	[currTemp, currHum] = dht(tempHumSensor, 0)             # Read temp and humidity
	currTemp = (currTemp / 5.0) * 9.0 + 32.0		# Convert C to F - multiple by 5/9 and add 32
	temp = int(currTemp * 10) / 10.0			# Round down to closest tenth degree
	currTime = time.time()
	if currTime > lastTime + sensorCycle:                   # If a sensorCycle number of seconds have passed
		lastTime = currTime                             # Reset lastTime to current time
		#################################################
		# Build data in JSON format			#
		#################################################
		JSONData = '{ "instance" : %3d, "time" : "%s", "light" : %3d, "temp" : %.01f, "humidity" : %2d }'%(INSTANCE, time.asctime(), currLight, currTemp, currHum)
		# print(JSONData)
		#################################################
		# Write data locally				#
		#################################################
		try:						# Need to remove the last newline and closing brace
			with open(filename, 'rb+') as f:	# Open as binary stream
				f.seek(-3, os.SEEK_END)		# Move to two characters before the end
				f.truncate()			# Truncate to remove
				print("Deleted trailing curly braces")
			with open(filename,'a') as f:		# Write to JSON file on every read
				if newFile == False:
					f.write(",\n")		# Need a comma on every entry but the last
					print("Added comma")
				else:
					f.write("\n")		# If first entry, no leading comma is needed
					print("Added new line without comma")
					newFile = False		# No longer a new file
				f.write(JSONData)	# write jsonstring
				f.write("\n]}")		# write list and element close brackets
		except IOError:
			print("FILE ERROR!!!\n")
		#################################################
		# Send data to server				#
		#################################################
		try:
			r = requests.post(url = REST_SERVER, data = JSONData, headers = HEADER)		# Post the JSON data to server
			status_code = r.status_code							# Export result
			if r.status_code == 200:							# 200 = Success
				print('Data uploaded!')
			elif r.status_code == 404:							# 404 = File not found
				print('Not Found')
			else:
				print('Data NOT uploaded: ')
				print(r.status_code)
		except requests.exceptions.RequestException:
			print("Connection Error")
			status_code = 503
		if status_code == 200:
			while len(backlog) > 0 and status_code == 200:					# If connected and backlog exists
				JSONData = backlog.pop()						# get entry from backlog
				try:
					r = requests.post(url = REST_SERVER, data = JSONData, headers = HEADER)		# Try sending entry to server
					status_code = r.status_code							# Read Result
				except requests.exception.RequestException:
					status_code = 503
				if status_code != 200:
					backlog.append(JSONData)					# If not uploaded, put back into backlog
				else:
					print("Uploaded Backup Entry!")					# print to screen
					print len(backlog)
		else:											# If upload not successful
			backlog.append(JSONData)							# Add entry to backlog
			print len(backlog)
	sleep(cycleTime)


 