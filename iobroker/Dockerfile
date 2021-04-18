FROM buanet/iobroker:v5.1.0

ENV INFLUXDB_ADMIN_USER=admin
ENV INFLUXDB_ADMIN_PASSWORD=secret
ENV INFLUXDB_DB=iobroker
ENV VWCONNECT_USER=test@test.de
ENV VWCONNECT_PASSWORD=secret
ENV VWCONNECT_PIN=1234
ENV VWCONNECT_TYPE=id
ENV VWCONNECT_INTERVAL=5

#RUN apt-get update && apt-get -y install gettext

COPY --chown=iobroker userscripts/userscript_firststart.sh /opt/userscripts/userscript_firststart.sh
#COPY --chown=iobroker userscripts/helpers /opt/userscripts/helpers
#COPY --chown=iobroker userscripts/data /opt/userscripts/data
COPY --chown=iobroker javascript /opt/javascript
