To build domainproxy-testserver image
------------
First thing to do is to to build the testserver package, for that:
1. Clone domain-proxy-sat-tests repo https://gerrit-gamma.gic.ericsson.se/#/admin/projects/OSS/com.ericsson.oss.testware/domain-proxy-sat-tests
2. Build sas-wiremock-extension inside domain-proxy-sat-tests and add it to local repository

i) from domain-proxy-sat-tests root folder:
```bash
   cd sas-wiremock-extension/
   mvn clean install
```
ii) from your user folder (ex : /c/Users/SIGNUM):
```bash
    mkdir .m2/repository/com/ericsson/oss/services/domainproxy/sas-wiremock-extension/0.0.1/
    cp .m2/repository/com/ericsson/nms/sas-wiremock-extension/0.0.1/sas-wiremock-extension-0.0.1.jar  .m2/repository/com/ericsson/oss/services/domainproxy/sas-wiremock-extension/0.0.1/
```
Clone the repo https://gerrit-gamma.gic.ericsson.se/#/admin/projects/OSS-PROTO/com.ericsson.oss.services.domainproxy/domain-proxy-test-server
```bash
    cd domain-proxy-test-server/domain-proxy-test-server
    mvn package
```
Now, to build the image:

i) copy the generated package *dp-testserver-jar-with-dependencies.jar* into this repo *eric-cbrs-dc-package/k8s-test/dptestserver*

ii) verify that the configuration file *dptestserver/dp-config.yml* meets your needs.

iii) from the dptestserver directory run:

For pipeline:
```bash
docker build -t armdocker.rnd.ericsson.se/proj_oss/domainproxy/domainproxy-testserver:stagingtest .

docker push armdocker.rnd.ericsson.se/proj_oss/domainproxy/domainproxy-testserver:stagingtest
```
For development:
```bash
docker build -t armdocker.rnd.ericsson.se/proj_oss/domainproxy/domainproxy-testserver:stagingtestdev .

docker push armdocker.rnd.ericsson.se/proj_oss/domainproxy/domainproxy-testserver:stagingtestdev
```