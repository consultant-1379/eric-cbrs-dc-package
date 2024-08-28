Information on eric-sec-certm-deployment-configuration.json file.

In real world, this file is created by the user who installs DC SA. It is documented in the CBRS install guide how to do it.

More information of this file and its structure can be found here:
https://adp.ericsson.se/marketplace/certificate-management/documentation/2.6.0/dpi/service-user-guide#configuration-over-nbi

You can use the following command to convert a p12 file to the expected format in JSON:
p12=p12=dc-sas-client.p12
cat ${p12} | base64 | tr -d '\n' > ${p12}_base64

You can use the following command to convert a pem certificate to the expected format in JSON:
cert=dc-sas-client-trusted-ca.crt
cat ${cert} | tr -d "\r\n" | tr -d "\n" | sed 's/-----BEGIN CERTIFICATE-----/-----BEGIN CERTIFICATE-----\\n/g' | sed 's/-----END CERTIFICATE-----/\\n-----END CERTIFICATE-----/g' > ${cert}_converted

Information about the certificates used in staging tests here
https://confluence-oss.seli.wh.rnd.internal.ericsson.com/display/SDP/Staging+test+certificate+configuration