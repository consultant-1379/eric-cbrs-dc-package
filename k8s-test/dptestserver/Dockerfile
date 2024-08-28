FROM armdocker.rnd.ericsson.se/proj_oss_releases/enm/jdk-base-enm

RUN mkdir -p /dp/cpi

RUN yum -y install net-tools

ADD certs/node/mock-node-netconf-server.cert /dp/
ADD certs/node/mock-node-netconf-server.key /dp/
ADD certs/node/mock-node-netconf-trusted-ca.pem /dp/
ADD certs/sas/mock-sas-rest-server.jks /dp/
ADD certs/sas/mock-sas-rest-server-truststore.jks /dp/
ADD certs/dcm/cbrs-dc-sa-keystore.jks /dp/
ADD certs/dcm/cbrs-dc-sa-truststore.jks /dp/
ADD log4j.xml /dp/
ADD dp-config.yml /dp/
ADD dp-testserver-jar-with-dependencies.jar /dp/
ADD cpi/cpi.csv /dp/cpi/

RUN chmod 755 /dp/*.*

EXPOSE 8305
EXPOSE 8306
EXPOSE 43340
EXPOSE 43341
EXPOSE 6513

VOLUME /dp/cpi/

WORKDIR /dp/

CMD ["bash", "-c", "java -Xms512m -Xmx5120m -XX:+UseG1GC -XX:+UnlockCommercialFeatures -XX:+FlightRecorder -Xss512k -XX:+UnlockExperimentalVMOptions -XX:+ParallelRefProcEnabled -XX:+AggressiveOpts -XX:+UseFastAccessorMethods -XX:+DoEscapeAnalysis -XX:+UseStringDeduplication -XX:+UseCompressedOops -Dlog4j.configuration=file:/dp/log4j.xml -jar /dp/dp-testserver-jar-with-dependencies.jar -c /dp/dp-config.yml"]
