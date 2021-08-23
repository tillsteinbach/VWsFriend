FROM python:3.9.5-alpine

ENV WECONNECT_USER=
ENV WECONNECT_PASSWORD=
ENV WECONNECT_INTERVAL=
ENV ADDITIONAL_PARAMETERS=
ENV DATABASE_URL=

RUN apk add --no-cache --virtual .build-deps rust build-base gcc libc-dev libffi-dev musl-dev python3-dev libffi-dev openssl-dev cargo postgresql-dev && \
   apk --no-cache add libpq && \
   apk --no-cache add jpeg-dev \
                          zlib-dev \
                          freetype-dev \
                          lcms2-dev \
                          openjpeg-dev \
                          tiff-dev \
                          tk-dev \
                          tcl-dev
RUN --mount=type=cache,target=/root/.cache pip install vwsfriend
RUN apk del .build-deps
RUN mkdir -p /config

CMD vwsfriend --username ${WECONNECT_USER} --password ${WECONNECT_PASSWORD} --interval ${WECONNECT_INTERVAL} --database-url ${DATABASE_URL} --config-dir /config ${ADDITIONAL_PARAMETERS}
