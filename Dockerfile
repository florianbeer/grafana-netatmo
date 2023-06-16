FROM python:3.11-alpine

COPY pyproject.toml poetry.lock grafana_netatmo/netatmo_influx.py /app/

WORKDIR /app
RUN apk add --no-cache build-base \
    && python3 -m pip install --no-cache-dir --trusted-host pypi.python.org poetry==1.4.2 \
    && poetry install --no-interaction --no-ansi \
    && apk del build-base \
    && rm -rf /var/cache/apk/*

CMD [ "python3", "/app/netatmo_influx.py" ]
