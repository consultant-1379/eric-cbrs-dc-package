#!/bin/bash
rm -f all.yaml
cat <&0 > all.yaml
cat all.yaml  |
  # change any {} into "{..}" so they can be restored later
  sed 's/\([a-zA-Z0-9_-]\+\): {}/\1: "{..}"/'  |
  # delete all 'limits'
  yq-4.x eval 'del(..|.limits?)' - |
  # delete all 'requests.cpu'
  yq-4.x eval 'del((..|select(has("requests"))).requests.cpu?)' - |
  # delete all 'requests.memory'
  yq-4.x eval 'del((..|select(has("requests"))).requests.memory?)' - |
  # set all 'replicas' greater than 0 to 1, except for 'search-engine
  yq-4.x eval '(.|select(.metadata.name != "*-search-engine-*")|..|select(has("replicas"))|select(.replicas != 0)).replicas |= 1' - |
  # keep search-engine pods together since some environments don't have nfs storage
  yq-4.x eval '((..|select(has("serviceName"))| select(.serviceName == "eric-data-search*")) | .template.spec.affinity) = {"podAffinity":{"preferredDuringSchedulingIgnoredDuringExecution":[{"weight":100,"podAffinityTerm":{"labelSelector":{"matchExpressions":[{"key":"app","operator":"In","values":["eric-data-search-engine"]}]},"topologyKey":"kubernetes.io/hostname"}}]}}' - |
  yq-4.x eval '(select(.kind == "Deployment" and .metadata.name == "eric-data-search-engi*") | .spec.template.spec.affinity) = {"podAffinity":{"preferredDuringSchedulingIgnoredDuringExecution":[{"weight":100,"podAffinityTerm":{"labelSelector":{"matchExpressions":[{"key":"app","operator":"In","values":["eric-data-search-engine"]}]},"topologyKey":"kubernetes.io/hostname"}}]}}' - |
  # remove any {} added by yq
  sed 's/\([a-zA-Z0-9_-]\+\): {}/\1: /' |
  # restore original {}
  sed 's/\([a-zA-Z0-9_-]\+\): "{..}"/\1: {}/'  |
  # remove any line that only contains {} and save the result to minimized.yaml
  sed 's/^{}$//' > minimized.yaml  2> /dev/null
cat minimized.yaml && rm all.yaml minimized.yaml
