To build rsyslog-testserver image
------------
From k8s-test/rsyslogserver directory
For pipeline:
```bash
docker build -t armdocker.rnd.ericsson.se/proj_oss/domainproxy/rsyslog-testserver:stagingtest .

docker push armdocker.rnd.ericsson.se/proj_oss/domainproxy/rsyslog-testserver:stagingtest
```
For development:
```bash
docker build -t armdocker.rnd.ericsson.se/proj_oss/domainproxy/rsyslog-testserver:stagingtestdev .

docker push armdocker.rnd.ericsson.se/proj_oss/domainproxy/rsyslog-testserver:stagingtestdev
```
To update certs 
------------
From k8s-test/rsyslogserver/certs directory
```bash
openssl genrsa -out root-ca.key 2048
openssl req -x509 -new -nodes -key root-ca.key -sha256 -days 365 -out root-ca.crt
cat root-ca.crt | tr -d "\r\n" | tr -d "\n" | sed 's/-----BEGIN CERTIFICATE-----/-----BEGIN CERTIFICATE-----\n/g' | sed 's/-----END CERTIFICATE-----/\n-----END CERTIFICATE-----/g' > trustedcert
cat trustedcert -> copy the content to k8s-test/eric-sec-certm-deployment-configuration.json file under ca-certs with name as log-syslog-client
```
For log-transformer side:
```bash
cd log-transformer

openssl genrsa -out log-transformer-rsyslog.key 2048
openssl req -new -sha256 -key log-transformer-rsyslog.key -subj "/CN=eric-log-transformer" -out log-transformer-rsyslog.csr
openssl x509 -req -in log-transformer-rsyslog.csr -CA root-ca.crt -CAkey root-ca.key -CAcreateserial -out log-transformer-rsyslog.crt -days 365 -sha256

cat log-transformer-rsyslog.key >  p12-input.txt
cat log-transformer-rsyslog.crt >>  p12-input.txt

openssl pkcs12 -export -in p12-input.txt -out container.p12 (remember the password and use it in the json)
base64 container.p12 | tr -d \\n > container-base64.p12

cat container-base64.p12 -> copy the content to json file under pkcs12 with name as log-syslog-client
```
For rsyslog-server side:
```bash
cd rsyslog

openssl genrsa -out rsyslog-log-transformer.key 2048
openssl req -new -sha256 -key rsyslog-log-transformer.key -subj "/CN=rsyslog-server" -out rsyslog-log-transformer.csr
openssl x509 -req -in rsyslog-log-transformer.csr -CA root-ca.crt -CAkey root-ca.key -CAcreateserial -out rsyslog-log-transformer.crt -days 365 -sha256
```