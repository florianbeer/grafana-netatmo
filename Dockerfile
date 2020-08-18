FROM python:3.8-alpine

COPY requirements.txt /app/requirements.txt
COPY netatmo_influx.py /app/netatmo_influx.py

RUN pip install --trusted-host pypi.python.org -r /app/requirements.txt

CMD [ "python3", "/app/netatmo_influx.py" ]
