# Here is the build image
FROM python:3.8.0-slim as builder
RUN apt-get update \
&& apt-get install gcc -y \
&& apt-get clean
COPY . vwsfriend
RUN pip install --upgrade pip
RUN pip install --user vwsfriend

FROM python:3.9.6-slim-buster

ENV WECONNECT_USER=
ENV WECONNECT_PASSWORD=
ENV WECONNECT_INTERVAL=
ENV ADDITIONAL_PARAMETERS=
ENV DATABASE_URL=

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
RUN mkdir -p /config

CMD vwsfriend --username ${WECONNECT_USER} --password ${WECONNECT_PASSWORD} --interval ${WECONNECT_INTERVAL} --database-url ${DATABASE_URL} --config-dir /config ${ADDITIONAL_PARAMETERS}
