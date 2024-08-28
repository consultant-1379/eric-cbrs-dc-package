#!/bin/bash
rm -f all.yaml
cat <&0 > all.yaml
cat all.yaml  |
  # change any {} into "{..}" so they can be restored later
  sed 's/\([a-zA-Z0-9_-]\+\): {}/\1: "{..}"/'  |
  # delete all 'limits'
  yq-4.x eval 'del(..|.limits?)' - |
  # delete all 'requests'
  yq-4.x eval 'del(..|.requests?)' - |
  # set all 'replicas' to 1
  yq-4.x eval '(..|select(has("replicas"))).replicas |= 1' - |
  # set pvc requests to 1Gi
  yq-4.x eval '(select(.kind == "PersistentVolumeClaim") | .spec.resources) = {"requests": {"storage": "1Gi"}}' -  |
  # set pvc templates to request 1Gi
  yq-4.x eval '((..|select(has("volumeClaimTemplates"))).volumeClaimTemplates.[].spec.resources) = {"requests": {"storage": "1Gi"}}' - |
  # remove any {} added by yq
  sed 's/\([a-zA-Z0-9_-]\+\): {}/\1: /' |
  # restore original {}
  sed 's/\([a-zA-Z0-9_-]\+\): "{..}"/\1: {}/'  |
  # remove any line that only contains {} and save the result to minimized.yaml
  sed 's/^{}$//' > minimized.yaml  2> /dev/null
cat minimized.yaml && rm all.yaml minimized.yaml
