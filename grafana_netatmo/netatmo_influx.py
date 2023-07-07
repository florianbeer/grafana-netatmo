#!/usr/bin/env python3
# encoding=utf-8

import signal
import logging
import argparse
import configparser
import pyatmo.helpers
from time import sleep
from os import environ
from pathlib import Path
from datetime import datetime
from requests import ConnectionError
from influxdb_client import InfluxDBClient, WritePrecision
from influxdb_client.client.exceptions import InfluxDBError
from pyatmo import ClientAuth, WeatherStationData, ApiError


class BatchingCallback(object):
    @staticmethod
    def success(conf: (str, str, str), data: str):
        logger.info(f"Written batch with size {len(data)}.")
        logger.debug(f"Batch: {conf}, Data: {data}")

    @staticmethod
    def error(conf: (str, str, str), data: str, exception: InfluxDBError):
        logger.error(f"Cannot write batch due: {exception}")
        logger.debug(f"Batch: {conf}, Data: {data}, Exception: {exception}")

    @staticmethod
    def retry(conf: (str, str, str), data: str, exception: InfluxDBError):
        logger.warning(f"Retryable error occurs for batch, retry: {exception}")
        logger.debug(f"Batch: {conf}, Data: {data}, Exception: {exception}")


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


def get_environ(name, def_val):
    env_val = def_val
    if environ.get(name):
        env_val = environ.get(name)

    return env_val


def set_logging_level(verbosity, level):
    switcher = {
        1: "WARNING",
        2: "INFO",
        3: "DEBUG",
    }
    if verbosity > 0:
        level = switcher.get(verbosity)

    fmt = logging.Formatter("%(asctime)s - %(levelname)s:%(message)s", datefmt="%d.%m.%Y %H:%M:%S")

    # Basic Setting for Debugging
    pyatmo.helpers.LOG.setLevel(level)

    # Logger
    _logger = logging.getLogger(__name__)

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)

    _logger.addHandler(ch)
    _logger.setLevel(level)
    _logger.info(f"Setting loglevel to {level}.")

    return _logger


def shutdown(_signal):
    global running
    running = False


if __name__ == "__main__":
    running = True
    interval = None
    loglevel = None
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
    influx_debug = False
    influx_callback = BatchingCallback()
    args = parse_args()
    config = parse_config(args.config)

    if get_environ("TERM", None):
        signal.signal(signal.SIGTERM, shutdown)
        signal.signal(signal.SIGINT, shutdown)

    if "global" in config:
        interval = int(config["global"].get("interval", "300"))  # interval in seconds; default are 5 Minutes
        loglevel = config["global"].get("loglevel", "INFO")  # set loglevel by Name

    if "netatmo" in config:
        client_id = config["netatmo"].get("client_id", None)
        client_secret = config["netatmo"].get("client_secret", None)
        netatmo_username = config["netatmo"].get("netatmo_username", None)
        netatmo_password = config["netatmo"].get("netatmo_password", None)

    if "influx" in config:
        influx_host = config["influx"].get("influx_host", "localhost")
        influx_port = config["influx"].get("influx_port", "8086")
        influx_bucket = config["influx"].get("influx_bucket", "netatmo")
        influx_protocol = config["influx"].get("influx_protocol", "http")
        influx_token = config["influx"].get("influx_token", None)
        influx_org = config["influx"].get("influx_org", None)

    # Environment Variables takes precedence over config if set
    client_id = get_environ("NETATMO_CLIENT_ID", client_id)
    client_secret = get_environ("NETATMO_CLIENT_SECRET", client_secret)
    netatmo_username = get_environ("NETATMO_USERNAME", netatmo_username)
    netatmo_password = get_environ("NETATMO_PASSWORD", netatmo_password)
    influx_host = get_environ("INFLUX_HOST", influx_host)
    influx_port = get_environ("INFLUX_PORT", influx_port)
    influx_bucket = get_environ("INFLUX_BUCKET", influx_bucket)
    influx_protocol = get_environ("INFLUX_PROTOCOL", influx_protocol)
    influx_token = get_environ("INFLUX_TOKEN", influx_token)
    influx_org = get_environ("INFLUX_ORG", influx_org)
    interval = int(get_environ("INTERVAL", interval))
    loglevel = get_environ("LOGLEVEL", loglevel)

    # set logging level
    logger = set_logging_level(args.verbosity, loglevel)
    if loglevel == "DEBUG" or args.verbosity == 3:
        influx_debug = True

    logger.info("Starting Netatmo Crawler...")
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
            logger.error("No credentials supplied. No Netatmo Account available.")
            exit(1)
        except ConnectionError:
            logger.error(f"Can't connect to Netatmo API. Retrying in {interval} second(s)...")
            pass
        else:
            try:
                weatherData = WeatherStationData(authorization)
                weatherData.update()

                with InfluxDBClient(
                    url=f"{influx_protocol}://{influx_host}:{influx_port}",
                    token=influx_token,
                    org=influx_org,
                    debug=influx_debug,
                ) as _client:
                    with _client.write_api(
                        success_callback=influx_callback.success,
                        error_callback=influx_callback.error,
                        retry_callback=influx_callback.retry,
                    ) as _write_client:
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
                                module_data_type = module["data_type"][0] if module else station["data_type"][0]

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
                                                "tags": {"station": station_name, "module": module_name, "data_type": module_data_type},
                                                "fields": {"value": value},
                                                "time": moduleData["When"],
                                            }
                                        )

                            now = datetime.utcnow()
                            strtime = now.strftime("%Y-%m-%d %H:%M:%S")

                            _write_client.write(
                                influx_bucket, influx_org, station_data, write_precision=WritePrecision.S
                            )

                            _write_client.write(
                                influx_bucket, influx_org, module_data, write_precision=WritePrecision.S
                            )
            except ApiError as error:
                logger.error(error)
                pass

        sleep(interval)
