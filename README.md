# grafana-netatmo
![pyatmo](./pyatmo.png)

Netatmo Weather Station dashboard for Grafana

![Screenshot](./screenshot.png)

## InfluxDB 2.0
This Version is for InfluxDB 2.0 only.

If you want to upgrade your Docker InfluxDB to 2.0, there is a guide available [here](https://docs.influxdata.com/influxdb/v2.0/upgrade/v1-to-v2/docker/). 

## Installation

* Create a [Netatmo developer account](https://dev.netatmo.com/apidocumentation) and create an app there.
* Generate a refresh token in your app, scroll down to the "Token generator" and generate a new one with the appropriate scopes.
* Create file called "config" or use Environment Variables and fill in your NETATMO_CLIENT_ID, NETATMO_CLIENT_SECRET and NETATMO_REFRESH_TOKEN.
* Environment Variables take precedence over everything else and will overwrite your config vars.
* The default is to search for a config file right next to the script, but you can point to any config file with the "-f" switch.

```ini
[global]
interval = 300
loglevel = INFO

[netatmo]
client_id =
client_secret =
refresh_token =

[influx]
influx_host =
influx_port =
influx_bucket =
influx_protocol =
influx_token =
influx_org =
```

* Create a cron job to run the script periodically e.g.

```bash
# cat /etc/cron.d/netatmo
*/5 * * * * root  /usr/local/bin/netatmo_influx.py > /dev/null 2>&1
```

You can also use docker to run the script. Either build it yourself or use my prebuild containers from [Github Container Registry](https://github.com/karaktaka/grafana-netatmo/pkgs/container/grafana-netatmo).
