FROM python:3.8-alpine

COPY requirements.txt /app/requirements.txt
COPY netatmo_influx.py /app/netatmo_influx.py

RUN apk add --no-cache build-base \
    && python3 -m pip install --no-cache-dir --trusted-host pypi.python.org -r /app/requirements.txt \
    && apk del build-base \
    && rm -rf /var/cache/apk/*

CMD [ "python3", "/app/netatmo_influx.py" ]
