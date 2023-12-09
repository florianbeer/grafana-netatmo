# grafana-netatmo
Netatmo Weather Station dashboard for Grafana

https://grafana.com/grafana/dashboards/12378

![Screenshot](https://raw.githubusercontent.com/florianbeer/grafana-netatmo/master/screenshot.png)

## Installation

* Create a [Netatmo developer account](https://dev.netatmo.com/apidocumentation)
* Create the file `~/.netatmo.credentials` and make it writable
```
{
  "CLIENT_ID" : "xxx",
  "CLIENT_SECRET" : "xxx",
  "REFRESH_TOKEN" : "xxx"
}
```
* This script assumes you have InfluxDB running on the same machine as this script and it uses no authentication.
* Create a cron job to run the script periodically e.g.

```
# cat /etc/cron.d/netatmo
*/5 * * * * root  /usr/local/bin/netatmo_influx.py > /dev/null 2>&1
```
