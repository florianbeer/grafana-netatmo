FROM python:3.11-alpine

ENV POETRY_VIRTUALENVS_IN_PROJECT=true

COPY pyproject.toml poetry.lock README.md /app/
COPY grafana_netatmo/netatmo_influx.py /app/grafana_netatmo/

WORKDIR /app
RUN apk add --no-cache build-base libffi-dev \
    && python3 -m pip install --no-cache-dir --trusted-host pypi.python.org poetry==1.4.2 \
    && poetry install --no-interaction --no-ansi --without dev \
    && apk del build-base libffi-dev \
    && rm -rf /var/cache/apk/* ~/.cache/pypoetry ~/.local/share/virtualenv

CMD [ "poetry", "run", "python", "/app/grafana_netatmo/netatmo_influx.py" ]
