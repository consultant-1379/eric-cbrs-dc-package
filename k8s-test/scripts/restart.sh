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

KUBECTL_CLIENT_MAJOR_VERSION=$(kubectl version --short 2>/dev/null | grep Client | awk -F. '{ print $2 }')

if [ $KUBECTL_CLIENT_MAJOR_VERSION != 26 ] ; then
  echo "Incorrect kubectl client major version. Supported is 26."
  exit 1
fi

USAGE="
Bash script that restarts all deployments and statefulsets in a given namespace.

Use with caution!

Restarts ALL deployments using rollout command then waits for them to come back online.
Restarts ALL statefulsets by setting the replicas to 0, then back to original, then waits for then to come back online.

Usage: ./$(basename $0) [-n namespace]
Example: ./$(basename $0) -n cbrs
"

if [[ $# -ne 1 ]]; then
  echo "$USAGE"
  exit 1
fi

NAMESPACE=$1
echo $NAMESPACE
echo

echo "Current status"
kubectl get statefulsets -n $NAMESPACE | tee before.txt
kubectl get deployments -n $NAMESPACE | tee -a before.txt
kubectl get pods -n $NAMESPACE | tee -a before.txt
kubectl get pods -n $NAMESPACE | wc -l | tee -a before.txt

echo
echo "Restarting deployments"
DEPLOYMENTS=$(kubectl get deployments -n $NAMESPACE --no-headers=true | awk '{ print $1}')
for deployment in $DEPLOYMENTS; do
  kubectl rollout restart deployments/$deployment -n $NAMESPACE
done

echo
echo "Scaling statefulsets"
STATEFULSETS=$(kubectl get statefulsets -n $NAMESPACE --no-headers=true | awk '{ print $1}')
for statefulset in $STATEFULSETS; do
  REPLICAS=$(kubectl get statefulset $statefulset --no-headers=true | awk '{print $2}' | awk -F/ '{ print $2}')
  kubectl scale --replicas=0 statefulset/$statefulset -n $NAMESPACE
  for i in $(seq $REPLICAS); do
    kubectl wait pod ${statefulset}-$(($i-1)) --for delete --timeout=5s -n $NAMESPACE
  done
  kubectl scale --replicas=$REPLICAS statefulset/$statefulset -n $NAMESPACE
  echo "$statefulset scaled back to $REPLICAS"
done

echo
echo "Waiting for deployments to start"
for deployment in $DEPLOYMENTS; do
  kubectl rollout status -w deployment/$deployment -n $NAMESPACE
done

echo
echo "Waiting for statefulsets to start"
for statefulset in $STATEFULSETS; do
  REPLICAS=$(kubectl get statefulset $statefulset -n $NAMESPACE --no-headers=true | awk '{print $2}' | awk -F/ '{ print $2}')
  for i in $(seq $REPLICAS); do
    kubectl wait pod ${statefulset}-$(($i-1)) --for condition=Ready --timeout=2m -n $NAMESPACE
  done
done

echo
echo "Current status"
kubectl get statefulsets -n $NAMESPACE | tee after.txt
kubectl get deployments -n $NAMESPACE | tee -a after.txt
kubectl get pods -n $NAMESPACE | tee -a after.txt
kubectl get pods -n $NAMESPACE | wc -l | tee -a after.txt

exit 0

echo
while :; do
  PODS=$(kubectl get pods  -n $NAMESPACE | grep -v "1/1" | grep -v "2/2" |  grep -v "3/3" | grep -v "4/4" | grep -v "5/5" | grep -v "6/6" | grep -v "7/7" | grep -v Completed)
  clear
  echo "$PODS"
  if [ $(echo "$PODS" | wc -l) == 1 ] ; then
    echo "ALL PODS RUNNING"
    break
  fi
  sleep 3
done
