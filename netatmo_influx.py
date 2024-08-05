#!/usr/bin/env python3
# encoding=utf-8

import lnetatmo
from influxdb import InfluxDBClient
from os.path import expanduser, exists
import json

#
#  custom influx config file
#
#   {
#     "INFLUX_HOST" : "",
#     "INFLUX_PORT" : "",
#   }
INFLUXCONFIG = "~/.netatmo.influxdb"

if (INFLUXCONFIG):
  influxconfigFile = expanduser(INFLUXCONFIG)
  with open(influxconfigFile, "r") as f:
      influxconfig = {k.upper():v for k,v in json.loads(f.read()).items()}

  #print(influxconfig)
  client = InfluxDBClient(host=influxconfig["INFLUX_HOST"], port=influxconfig["INFLUX_PORT"])
else:
  #print("default")
  client = InfluxDBClient()
  if {'name': 'netatmo'} not in client.get_list_database():
    client.create_database('netatmo')

authorization = lnetatmo.ClientAuth()

weatherData = lnetatmo.WeatherStationData(authorization)

#print(weatherData.stationByName())
for station in weatherData.stations:
    station_data = []
    module_data = []
    station = weatherData.stationById(station)
    station_name = station['station_name']
    altitude = station['place']['altitude']
    country= station['place']['country']
    timezone = station['place']['timezone']
    longitude = station['place']['location'][0]
    latitude = station['place']['location'][1]
    for module, moduleData in weatherData.lastData(station=station_name, exclude=3600).items():
        for measurement in ['altitude', 'country', 'longitude', 'latitude', 'timezone']:
            value = eval(measurement)
            if type(value) == int:
                value = float(value)
            station_data.append({
                "measurement": measurement,
                "tags": {
                    "station": station_name,
                    "module": module
                },
                "time": moduleData['When'],
                "fields": {
                    "value": value
                }
            })

        for sensor, value in moduleData.items():
            if sensor.lower() != 'when':
                if type(value) == int:
                    value = float(value)
                module_data.append({
                    "measurement": sensor.lower(),
                    "tags": {
                        "station": station_name,
                        "module": module
                    },
                    "time": moduleData['When'],
                    "fields": {
                        "value": value
                    }
                })

    client.write_points(station_data, time_precision='s', database='netatmo')
    client.write_points(module_data, time_precision='s', database='netatmo')
