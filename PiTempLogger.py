#! /usr/bin/python3

#
# 20210523
# Written from various resrouces on the internet
#


import subprocess, time
import os
import subprocess
import glob
import argparse
import time
import datetime
import sys
from influxdb import InfluxDBClient
import requests, json
from decimal import *


# defines DB resource
client = InfluxDBClient("www.sm.sm", 8086, "grafana", "44knf7PU", "astrocarttemp")


# This def executes the temp readings from GPIO - via
#  https://github.com/rhubarbdog/am2320/blob/master/am2320.py
# Each sensor is connected to a different bus with different GPIO pins
#  per - https://www.instructables.com/Raspberry-PI-Multiple-I2c-Devices/
# Beware! https://github.com/raspberrypi/firmware/issues/1401
# FIX for slow
# https://github.com/raspberrypi/linux/issues/1467
def temp():
        global mirrorT
        global airT
        global mirrorH
        global airH
        global D
        try:
                sp = subprocess.Popen('/home/pi/am2320/run.sh',
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True)
                air,err=sp.communicate()
                # Store the return code in rc variable
                rc=sp.wait()
				# string sort of output for desired values
                airT=float(air[:-26][12:])
                airH=float(air[:-5][33:])
        except:
                # pre-store values to prevent scrtipt from stopping if sensors have errorsairT=1.1
                airH=1.1
                pass
        try:
                sp = subprocess.Popen('/home/pi/am2320.Bus4/run.sh',
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True)
                mirror,err=sp.communicate()
                # Store the return code in rc variable
                rc=sp.wait()
                # string sort of output for desired values
				mirrorT=float(mirror[:-26][12:])
                mirrorH=float(mirror[:-5][33:])
        except:
                # pre-store values to prevent scrtipt from stopping if sensors have errors
				mirrorT=1.1
                mirrorH=1.1
                pass
        D=mirrorT-airT
        return mirrorT,airT,mirrorH,airH,D

# Change your city and key!
# OpenWeather is used, to compare to telescope's inside parked temp to outside
# Create an OpenWeather account to get an API if you want this feature - https://home.openweathermap.org/api_keys
def OpenWeather():
        global OWF
        global OWH
        # Python program to find current
        # weather details of any city
        # using openweathermap api

        # Enter your API key here
        api_key = "abc123"

        # base_url variable to store url
        base_url = "http://api.openweathermap.org/data/2.5/weather?"

        # Give city name
        #city_name = input("Enter city name : ")
        city_name = 'Apex'

        # complete_url variable to store
        # complete url address
        complete_url = base_url + "appid=" + api_key + "&q=" + city_name

        # get method of requests module
        # return response object
        response = requests.get(complete_url)

        # json method of response object
        # convert json format data into
        # python format data
        x = response.json()

        # Now x contains list of nested dictionaries
        # Check the value of "cod" key is equal to
        # "404", means city is found otherwise,
        # city is not found
        if x["cod"] != "404":

                        # store the value of "main"
                        # key in variable y
                        y = x["main"]

                        # store the value corresponding
                        # to the "temp" key of y
                        current_temperature = y["temp"]
                        F=(((current_temperature-273.15)*9)/5)+32
                        F=round(F,2)
                        OWF=F

                        # store the value corresponding
                        # to the "pressure" key of y
                        current_pressure = y["pressure"]

                        # store the value corresponding
                        # to the "humidity" key of y
                        current_humidiy = y["humidity"]
                        OWH=current_humidiy
                        # store the value of "weather"
                        # key in variable z
                        z = x["weather"]

                        # store the value corresponding
                        # to the "description" key at
                        # the 0th index of z
                        weather_description = z[0]["description"]

                        # print following values
                        '''
                        print(" Temp (F) = " +
                                                                                        str(F) +
                                        "\n pressure (hPa) = " +
                                                                                        str(current_pressure) +
                                        "\n humidity (%) = " +
                                                                                        str(current_humidiy) +
                                        "\n Conditions = " +
                                                                                        str(weather_description))
                        '''
                        return OWF,OWH
        else:
                        print(" City Not Found ")



# this section takes the read values and creates json objects
# that are then used to write to Influx
def log():
        OpenWeather()
        temp()
        timestamp=datetime.datetime.utcnow().isoformat()
        json_AirTemp = [
                {
                        "measurement": "AirTemp",
                        "tags": {
                                "host": "astrocart",
                                "region": "garage"
                        },
                        "time": timestamp,
                        "fields": {
                                "value": airT
                   }
                }
        ]
        json_MirrorTemp = [
                {
                        "measurement": "MirrorTemp",
                        "tags": {
                                "host": "astrocart",
                                "region": "garage"
                        },
                        "time": timestamp,
                        "fields": {
                                "value": mirrorT
                        }
                }
]
        json_AirHumidity = [
                {
                        "measurement": "AirHumidity",
                        "tags": {
                                "host": "astrocart",
                                "region": "garage"
                        },
                        "time": timestamp,
                        "fields": {
                                "value": airH
                   }
                }
        ]
        json_MirrorHumidity = [
                {
                        "measurement": "MirrorHumidity",
                        "tags": {
                                "host": "astrocart",
                                "region": "garage"
                        },
                        "time": timestamp,
                        "fields": {
                                "value": mirrorH
                        }
                }
]
        json_DeltaT = [
                {
                        "measurement": "DeltaTemp",
                        "tags": {
                                "host": "astrocart",
                                "region": "garage"
                        },
                        "time": timestamp,
                        "fields": {
                                "value": D
                        }
                }
]
        json_OWF = [
                {
                        "measurement": "OpenWeatherTemp",
                        "tags": {
                                "host": "astrocart",
                                "region": "garage"
                        },
                        "time": timestamp,
                        "fields": {
                                "value": OWF
                        }
                }
]
        json_OWH = [
                {
                        "measurement": "OpenWeatherHumidity",
                        "tags": {
                                "host": "astrocart",
                                "region": "garage"
                        },
                        "time": timestamp,
                        "fields": {
                                "value": OWH
                        }
                }
]
        client.create_database('astrocarttemp')
        client.write_points(json_AirTemp)
        client.write_points(json_MirrorTemp)
        client.write_points(json_AirHumidity)
        client.write_points(json_MirrorHumidity)
        client.write_points(json_DeltaT)
        client.write_points(json_OWF)
        client.write_points(json_OWH)
#       result = client.query('select value from AirTemp;')
#       print("Result: {0}".format(result))


#This is the main function that loops over all the outputs every 5 seconds; it optionally outputs text
# for a simple webview outside grafana/influx
while True:
        log()
        time.sleep(5)
        sp = subprocess.Popen('echo \'\' > mirror.txt ; echo \'Current Astrocart Airtemp: \''+str(airT)+' >> mirror.txt; echo \'Current Astrocart Humidity: \''+str(airH)+' >> mirror.txt',
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True)
