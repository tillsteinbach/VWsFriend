# syntax = docker/dockerfile:experimental
# Here is the build image
FROM ubuntu:21.10 as builder

ENV DEBIAN_FRONTEND="noninteractive"
ENV TZ="Etc/UTC"
ARG VERSION

RUN apt-get update && apt-get install --no-install-recommends -y python3.9 python3.9-dev python3.9-venv python3-pip python3-wheel build-essential && \
    apt-get install --no-install-recommends -y libpq-dev libffi-dev libssl-dev rustc cargo libjpeg-dev zlib1g-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


RUN python3.9 -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"
RUN pip3 install --no-cache-dir wheel
# This line is a workaround necessary for linux/arm/v7 architecture that has a bug with qemu: https://github.com/rust-lang/cargo/issues/8719
# RUN --security=insecure mkdir -p /root/.cargo/registry/index && chmod 777 /root/.cargo/registry/index && mount -t tmpfs none /root/.cargo/registry/index && pip3 install --no-cache-dir cryptography
RUN pip3 install --no-cache-dir vwsfriend==${VERSION}


FROM ubuntu:21.10 AS runner-image

ENV VWSFRIEND_USERNAME=
ENV VWSFRIEND_PASSWORD=
ENV VWSFRIEND_PORT=4000
ENV WECONNECT_USER=
ENV WECONNECT_PASSWORD=
ENV WECONNECT_INTERVAL=300
ENV ADDITIONAL_PARAMETERS=
ENV DATABASE_URL=

RUN apt-get update && apt-get install --no-install-recommends -y python3.9 python3-venv wget && \
    apt-get install --no-install-recommends -y libpq5 libjpeg8 zlib1g postgresql-client && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN mkdir -p /config

# make sure all messages always reach console
ENV PYTHONUNBUFFERED=1

EXPOSE 4000

CMD vwsfriend --username=${VWSFRIEND_USERNAME} --password=${VWSFRIEND_PASSWORD} --weconnect-username=${WECONNECT_USER} --weconnect-password=${WECONNECT_PASSWORD} --interval=${WECONNECT_INTERVAL} --port=${VWSFRIEND_PORT} --database-url=${DATABASE_URL} --config-dir=/config ${ADDITIONAL_PARAMETERS}
