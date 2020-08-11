FROM python:3.8-alpine

COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt \
    && echo "*/10 * * * * python /netatmo_influx.py" > /etc/crontabs/root

COPY netatmo_influx.py /netatmo_influx.py

CMD [ "/usr/sbin/crond", "-f", "-l", "8" ]
