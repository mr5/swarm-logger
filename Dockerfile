FROM python:2.7.14-alpine3.7
COPY . /opt/swarm-logger/
WORKDIR /opt/swarm-logger/
RUN pip install -r requirements.txt
RUN apk update --no-cache
RUN apk add logrotate
COPY ./logrotate.conf /etc/logrotate.d/swarm-logger
CMD python ./swarm_logger.py
VOLUME ["/acs/log/swarm-logger"]
