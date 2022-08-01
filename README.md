# grafana-netatmo
Netatmo Weather Station dashboard for Grafana

https://grafana.com/grafana/dashboards/12378

![Screenshot](https://raw.githubusercontent.com/florianbeer/grafana-netatmo/master/screenshot.png)

## Installation

* Create a [Netatmo developer account](https://dev.netatmo.com/apidocumentation) and fill in your CLIENT_ID, CLIENT_SECRET, USERNAME and PASSWORD in the script.
* This script assumes you have InfluxDB running on the same machine as this script and it uses no authentication.
* Create a cron job to run the script periodically e.g.

```
# cat /etc/cron.d/netatmo
*/5 * * * * root  /usr/local/bin/netatmo_influx.py > /dev/null 2>&1
```

## Possible error when running the script
If netatmo_influx.py shows this error when running, you might need to downgrade to v1.6.0 of lnetatmo:

```Traceback (most recent call last):
File "netatmo_influx.py", line 39, in
for module, moduleData in weatherData.lastData(station=station_name, exclude=3600).items():
TypeError: lastData() got an unexpected keyword argument 'station'
