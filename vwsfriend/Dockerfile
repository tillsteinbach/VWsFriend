# Here is the build image
FROM ubuntu:20.04 as builder

ENV DEBIAN_FRONTEND="noninteractive"
ENV TZ="Etc/UTC"

RUN apt-get update && apt-get install --no-install-recommends -y python3.9 python3.9-dev python3.9-venv python3-pip python3-wheel build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN python3.9 -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"
RUN pip3 install --no-cache-dir wheel
RUN pip3 install --no-cache-dir vwsfriend

#RUN python setup.py install

FROM ubuntu:20.04 AS runner-image

ENV WECONNECT_USER=
ENV WECONNECT_PASSWORD=
ENV WECONNECT_INTERVAL=
ENV ADDITIONAL_PARAMETERS=
ENV DATABASE_URL=

RUN apt-get update && apt-get install --no-install-recommends -y python3.9 python3-venv && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN mkdir -p /config

# make sure all messages always reach console
ENV PYTHONUNBUFFERED=1

CMD vwsfriend --username ${WECONNECT_USER} --password ${WECONNECT_PASSWORD} --interval ${WECONNECT_INTERVAL} --database-url ${DATABASE_URL} --config-dir /config ${ADDITIONAL_PARAMETERS}
