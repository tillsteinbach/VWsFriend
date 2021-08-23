# Here is the build image
FROM python:3.8.0-slim as builder
RUN apt-get update \
&& apt-get install gcc libpq-dev python-dev -y \
&& apt-get clean
RUN python -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install vwsfriend

FROM python:3.9.6-slim-buster

ENV WECONNECT_USER=
ENV WECONNECT_PASSWORD=
ENV WECONNECT_INTERVAL=
ENV ADDITIONAL_PARAMETERS=
ENV DATABASE_URL=

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN mkdir -p /config

CMD vwsfriend --username ${WECONNECT_USER} --password ${WECONNECT_PASSWORD} --interval ${WECONNECT_INTERVAL} --database-url ${DATABASE_URL} --config-dir /config ${ADDITIONAL_PARAMETERS}
