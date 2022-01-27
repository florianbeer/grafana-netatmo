#!/usr/bin/env python3
# encoding=utf-8

import signal
import logging
import argparse
import configparser
from time import sleep
from os import environ
from pathlib import Path
from datetime import datetime
from requests import ConnectionError
from influxdb_client import InfluxDBClient, WritePrecision
from pyatmo import ClientAuth, WeatherStationData, ApiError


def parse_config(config_file=None):
    _config = configparser.ConfigParser(interpolation=None)

    if config_file is None:
        config_file = Path("config")

    if config_file.exists():
        _config.read(config_file)

    return _config


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", dest="config", type=str, nargs=1, required=False)
    parser.add_argument("-v", "--verbose", dest="verbosity", action="count", default=0)

    return parser.parse_args()


def set_logging_level(verbosity):
    switcher = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
    }
    loglevel = switcher.get(verbosity)
    logging.basicConfig(format="%(asctime)s - %(levelname)s:%(message)s", datefmt="%d.%m.%Y %H:%M:%S", level=loglevel)


def shutdown(_signal):
    global running
    running = False


if __name__ == "__main__":
    running = True
    interval = None
    authorization = None
    client_id = None
    client_secret = None
    netatmo_username = None
    netatmo_password = None
    influx_host = None
    influx_port = None
    influx_bucket = None
    influx_protocol = None
    influx_token = None
    influx_org = None
    args = parse_args()
    config = parse_config(args.config)

    # set logging level
    set_logging_level(args.verbosity)

    if environ.get("TERM"):
        signal.signal(signal.SIGTERM, shutdown)
        signal.signal(signal.SIGINT, shutdown)

    if "global" in config:
        interval = int(config["global"]["interval"])

    if "netatmo" in config:
        client_id = config["netatmo"]["client_id"]
        client_secret = config["netatmo"]["client_secret"]
        netatmo_username = config["netatmo"]["netatmo_username"]
        netatmo_password = config["netatmo"]["netatmo_password"]

    if "influx" in config:
        influx_host = config["influx"]["influx_host"]
        influx_port = config["influx"]["influx_port"]
        influx_bucket = config["influx"]["influx_bucket"]
        influx_protocol = config["influx"]["influx_protocol"]
        influx_token = config["influx"]["influx_token"]
        influx_org = config["influx"]["influx_org"]

    if environ.get("NETATMO_CLIENT_ID"):
        client_id = environ.get("NETATMO_CLIENT_ID")
    if environ.get("NETATMO_CLIENT_SECRET"):
        client_secret = environ.get("NETATMO_CLIENT_SECRET")
    if environ.get("NETATMO_USERNAME"):
        netatmo_username = environ.get("NETATMO_USERNAME")
    if environ.get("NETATMO_PASSWORD"):
        netatmo_password = environ.get("NETATMO_PASSWORD")

    if environ.get("INFLUX_HOST"):
        influx_host = environ.get("INFLUX_HOST")
    elif influx_host is None:
        influx_host = "localhost"
    if environ.get("INFLUX_PORT"):
        influx_port = environ.get("INFLUX_PORT")
    elif influx_port is None:
        influx_port = 8086
    if environ.get("INFLUX_BUCKET"):
        influx_bucket = environ.get("INFLUX_BUCKET")
    elif influx_bucket is None:
        influx_bucket = "netatmo"
    if environ.get("INFLUX_PROTOCOL"):
        if environ.get("INFLUX_PROTOCOL") == "True":
            influx_protocol = "https"
        else:
            influx_protocol = "http"
    elif influx_protocol is None:
        influx_protocol = "http"
    if environ.get("INFLUX_TOKEN"):
        influx_token = environ.get("INFLUX_TOKEN")
    if environ.get("INFLUX_ORG"):
        influx_org = environ.get("INFLUX_ORG")
    if interval is None:
        interval = 300  # interval in seconds; default are 5 Minutes
    elif environ.get("INTERVAL"):
        interval = int(environ.get("INTERVAL"))

    while running:
        try:
            authorization = ClientAuth(
                client_id=client_id,
                client_secret=client_secret,
                username=netatmo_username,
                password=netatmo_password,
                scope="read_station",
            )
        except ApiError:
            logging.error("No credentials supplied. No Netatmo Account available.")
            exit(1)
        except ConnectionError:
            logging.error(f"Can't connect to Netatmo API. Retrying in {interval} second(s)...")
            pass
        except KeyboardInterrupt:
            logging.info("Received Interrupt. Shutting down...")
            running = False
        else:
            try:
                weatherData = WeatherStationData(authorization)
                weatherData.update()

                with InfluxDBClient(
                    url=f"{influx_protocol}://{influx_host}:{influx_port}",
                    token=influx_token,
                    org=influx_org,
                    debug=False,
                ) as _client:
                    with _client.write_api() as _write_client:

                        for station_id in weatherData.stations:
                            station_data = []
                            module_data = []

                            station = weatherData.get_station(station_id)
                            station_name = station["station_name"]
                            station_module_name = station["module_name"]

                            altitude = station["place"]["altitude"]
                            country = station["place"]["country"]
                            timezone = station["place"]["timezone"]
                            longitude = station["place"]["location"][0]
                            latitude = station["place"]["location"][1]

                            for module_id, moduleData in weatherData.get_last_data(station_id).items():
                                module = weatherData.get_module(module_id)
                                module_name = module["module_name"] if module else station["module_name"]

                                if not module:
                                    for measurement in ["altitude", "country", "longitude", "latitude", "timezone"]:
                                        value = eval(measurement)
                                        if type(value) == int:
                                            value = float(value)
                                        station_data.append(
                                            {
                                                "measurement": measurement,
                                                "tags": {"station": station_name, "module": module_name},
                                                "fields": {"value": value},
                                                "time": moduleData["When"],
                                            }
                                        )

                                for sensor, value in moduleData.items():
                                    if sensor.lower() == "wifi_status":
                                        sensor = "rf_status"
                                    if sensor.lower() != "when":
                                        if type(value) == int:
                                            value = float(value)
                                        module_data.append(
                                            {
                                                "measurement": sensor.lower(),
                                                "tags": {"station": station_name, "module": module_name},
                                                "fields": {"value": value},
                                                "time": moduleData["When"],
                                            }
                                        )

                            now = datetime.utcnow()
                            strtime = now.strftime("%Y-%m-%d %H:%M:%S")

                            if _write_client.write(
                                influx_bucket, influx_org, station_data, write_precision=WritePrecision.S
                            ):
                                logging.info(
                                    f"({strtime}) Stations: {len(station_data)} Data Points written to Influxdb"
                                )

                            if _write_client.write(
                                influx_bucket, influx_org, module_data, write_precision=WritePrecision.S
                            ):
                                logging.info(f"({strtime}) Modules: {len(module_data)} Data Points written to Influxdb")
            except ApiError as error:
                logging.error(error)
                pass
            except KeyboardInterrupt:
                logging.info("Received Interrupt. Shutting down...")
                running = False

        sleep(interval)
