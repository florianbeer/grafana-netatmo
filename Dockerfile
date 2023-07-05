FROM python:3.11-alpine

ENV POETRY_VIRTUALENVS_IN_PROJECT=true

COPY pyproject.toml poetry.lock README.md grafana_netatmo/netatmo_influx.py /app/

WORKDIR /app
RUN apk add --no-cache build-base \
    && python3 -m pip install --no-cache-dir --trusted-host pypi.python.org poetry==1.4.2 \
    && poetry install --no-interaction --no-ansi --without dev \
    && apk del build-base \
    && rm -rf /var/cache/apk/* ~/.cache/pypoetry ~/.local/share/virtualenv

CMD [ "poetry", "run", "python", "/app/netatmo_influx.py" ]
