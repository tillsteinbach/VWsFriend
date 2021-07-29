FROM grafana/grafana:7.5.4

ENV GF_SECURITY_ADMIN_USER=admin
ENV GF_SECURITY_ADMIN_PASSWORD=admin
ENV GF_USERS_ALLOW_SIGN_UP=false
ENV GF_INSTALL_PLUGINS=natel-discrete-panel,pierosavi-imageit-panel
ENV DB_USER=admin
ENV DB_PASSWORD=secret

COPY ./config/grafana/provisioning/ /etc/grafana/provisioning/
COPY ./dashboards/ /var/lib/grafana/dashboards/

EXPOSE 3000
