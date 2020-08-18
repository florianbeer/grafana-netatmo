# grafana-netatmo

Netatmo Weather Station dashboard for Grafana

[https://grafana.com/grafana/dashboards/12378](https://grafana.com/grafana/dashboards/12378)

![Screenshot](https://raw.githubusercontent.com/florianbeer/grafana-netatmo/master/screenshot.png)

## Installation

* Create a [Netatmo developer account](https://dev.netatmo.com/apidocumentation), create file called "config" or use Environment Variables and fill in your CLIENT_ID, CLIENT_SECRET, USERNAME and PASSWORD.
* Environment Variables take precedence over everything else and will overwrite you config vars.
* The default is to search for a config file right next to the script, but you can point to any config file with the "-f" switch.

```ini
[global]
interval =

[netatmo]
client_id =
client_secret =
netatmo_username =
netatmo_password =

[influx]
influx_host =
influx_port =
influx_db =
influx_username =
influx_password =
```

* If you don't add InfluxDB credentials a localhost connection with no authentication is used. 
* Create a cron job to run the script periodically e.g.

```bash
# cat /etc/cron.d/netatmo
*/5 * * * * root  /usr/local/bin/netatmo_influx.py > /dev/null 2>&1
```

You can also use docker to run the script. Either build it yourself or use my prebuild containers at [Docker Hub](https://hub.docker.com/r/karaktaka/grafana-netatmo).
