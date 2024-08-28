#!/bin/bash
#
# COPYRIGHT Ericsson 2023
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
#

USAGE="
Bash script that collects log files from each pod in the given namespace.

Usage: ./$(basename $0) -n <namespace> -t <target logs directory>
Example: ./$(basename $0) -n cbrs -t k8s-test/target/logs
"

NAMESPACE=cbrs
TARGET_LOGS_DIR=k8test/target/logs

while getopts 'n:t:' opt; do
  case "$opt" in
    n)
      NAMESPACE="$OPTARG"
      ;;
    t)
      TARGET_LOGS_DIR="$OPTARG"
      ;;
    :)
      echo "option requires an argument."
      echo "$USAGE"
      exit 1
      ;;
    ?)
      echo "$USAGE"
      exit 1
      ;;
  esac
done
shift "$(($OPTIND -1))"

LOGS_NAME=all-pods-file-logs-$NAMESPACE-$(date +'%Y-%m-%d_%H-%M-%S')
TEMP_LOGS_DIR=$TARGET_LOGS_DIR/$LOGS_NAME
TARGET_LOGS_FILE=$TARGET_LOGS_DIR/$LOGS_NAME.tar.gz

echo "Collecting logs from each pod in namespace: "$NAMESPACE
echo "Collecting logs to: "$TARGET_LOGS_FILE

mkdir -p $TARGET_LOGS_DIR
rm -rf $TEMP_LOGS_DIR
mkdir $TEMP_LOGS_DIR

for pod in $(kubectl get pods --no-headers -n $NAMESPACE | grep Running | awk '{ print $1 }'); do
    kubectl cp $NAMESPACE/$pod:/logs $TEMP_LOGS_DIR/$pod 2>&1 >>$TARGET_LOGS_DIR/collect_log_files.log --retries=3
    # Get logs from pods where tar is not installed
    if [ ! -d $TEMP_LOGS_DIR/$pod ]; then
        mkdir $TEMP_LOGS_DIR/$pod
        for file in $(kubectl exec -i $pod -n $NAMESPACE -- ls -l /logs | awk '{print $9}' | tr -d '\r' ); do
            kubectl exec -i $pod  -n $NAMESPACE -- cat $(echo /logs/$file) > $TEMP_LOGS_DIR/$pod/$file
        done
    fi
    echo "Collected "$(find -L $TEMP_LOGS_DIR/$pod 2>/dev/null | wc -l)" files from "$NAMESPACE/$pod
done

echo "Collected "$(find -L $TEMP_LOGS_DIR 2>/dev/null | wc -l)" files from namespace: "$NAMESPACE

tar -zcf $TARGET_LOGS_FILE -C $TEMP_LOGS_DIR .
echo "Collected logs is stored in file: "$TARGET_LOGS_FILE
rm -rf $TEMP_LOGS_DIR
