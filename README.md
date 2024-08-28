Build the full chart and pull down all dependencies:
```shell
./build.sh -d -C <chart>
e.g:
./build.sh -d -C eric-cbrs-dc-package
```

To lint the chart:
```shell
./build.sh -l
```

To clean a chart build:
```shell
./build.sh -c -C <chart>
e.g:
./build.sh -c -C eric-cbrs-dc-package
```

To build a chart package:
```shell
./build.sh -d -p -C <chart>
e.g:
./build.sh -d -p -C eric-cbrs-dc-package
```

Pre-Install Config (CRDs) (only needed once to get them installed)
```shell
helm upgrade --install --atomic eric-tm-ingress-controller-cr-crd eric-tm-ingress-controller-cr-crd-<version>.tgz -n <namespace>
helm upgrade --install --atomic eric-sec-sip-tls-crd eric-sec-sip-tls-crd-<version>.tgz -n <namespace>
```


Install by:
```shell
helm install <release_name> chart/eric-cbrs-dc-package/ -f chart/eric-cbrs-dc-package/values.yaml --set tags.eric-cbrs-dc-common=true --debug -n <namespace> --wait --timeout 15m
e.g:
helm install eric-dc-common-services-cbrs1631 chart/eric-cbrs-dc-package/ -f chart/eric-cbrs-dc-package/values.yaml --set tags.eric-cbrs-dc-common=true --debug -n cbrs1631 --wait --timeout 15m
```

Uninstall by:
```shell
./cbrs_uninstall.sh -n <namespace> -r <release_name>
e.g:
./cbrs_uninstall.sh -n enm43 -r eric-dc-common-services-enm43
```

To build a CSAR, use the build script in the csar/build.sh

