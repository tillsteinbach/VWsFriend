FROM python:3.9.5-alpine

ENV WECONNECT_USER=
ENV WECONNECT_PASSWORD=
ENV WECONNECT_INTERVAL=
ENV ADDITIONAL_PARAMETERS=
ENV DATABASE_URL=

COPY . vwsfriend
RUN apk add --no-cache --virtual .build-deps rust build-base gcc libc-dev libffi-dev musl-dev python3-dev libffi-dev openssl-dev cargo && \
   apk --no-cache add jpeg-dev \
                          zlib-dev \
                          freetype-dev \
                          lcms2-dev \
                          openjpeg-dev \
                          tiff-dev \
                          tk-dev \
                          tcl-dev && \
    pip install -r ./vwsfriend/requirements.txt && \
    pip install -r ./vwsfriend/setup_requirements.txt && \
    pip install -r ./vwsfriend/test_requirements.txt && \
    pip install ./vwsfriend/ && \
    apk del .build-deps

CMD vwsfriend --username ${USER} --password ${PASSWORD} --interval ${WECONNECT_INTERVAL} --database-url ${DATABASE_URL} ${ADDITIONAL_PARAMETERS}
