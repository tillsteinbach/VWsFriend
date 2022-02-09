FROM grafana/grafana:8.3.6

ENV GF_SECURITY_ADMIN_USER=admin
ENV GF_SECURITY_ADMIN_PASSWORD=admin
ENV GF_USERS_ALLOW_SIGN_UP=false
ENV GF_INSTALL_PLUGINS="marcusolsson-json-datasource,pierosavi-imageit-panel,pr0ps-trackmap-panel,natel-plotly-panel,https://github.com/panodata/panodata-map-panel/releases/download/0.16.0/panodata-map-panel-0.16.0.zip;panodata-map-panel"
ENV GF_PLUGINS_ALLOW_LOADING_UNSIGNED_PLUGINS=panodata-map-panel
ENV GF_SERVER_ENABLE_GZIP=true
ENV DB_USER=admin
ENV DB_PASSWORD=secret
ENV VWSFRIEND_USERNAME=admin
ENV VWSFRIEND_PASSWORD=secret
ENV VWSFRIEND_HOSTNAME=
ENV VWSFRIEND_PORT=
ENV DB_HOSTNAME=postgresdbbackend
ENV DB_PORT=5432
ENV DB_NAME=vwsfriend
ENV GF_EXPLORE_ENABLED=false
ENV GF_ALERTING_ENABLED=false
ENV GF_METRICS_ENABLED=false
ENV GF_EXPRESSIONS_ENABLED=false
ENV GF_PLUGINS_PLUGIN_ADMIN_ENABLED=false
ENV GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH="/var/lib/grafana-static/dashboards/vwsfriend/VWsFriend/overview.json"

COPY ./config/grafana/provisioning/ /etc/grafana/provisioning/
COPY ./dashboards/ /var/lib/grafana-static/dashboards/

EXPOSE 3000
