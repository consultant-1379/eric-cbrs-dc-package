FROM	alpine:3.7
RUN	apk add rsyslog rsyslog-tls
ENTRYPOINT ["rsyslogd", "-n", "-f", "/etc/rsyslog.conf"]