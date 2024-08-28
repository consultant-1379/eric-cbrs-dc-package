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

set -e
set -o pipefail

USAGE="
Script that can be used to setup CBRS enrollment in cENM prior to CBRS installation.

Under the hood it uses enroll.py script that is executed on cENM general scripting VM.

Options
  -n <namespace> the CBRS namespace (Default cbrs)
  -o <output> the certm file to be written to (Default k8s-test/target/eric-sec-certm-deployment-configuration.json)

Usage: $(basename $0) [-n namespace] [-o output]
Example: $(basename $0) -n cbrs -o k8s-test/target/eric-sec-certm-deployment-configuration.json
"

CBRS_NAMESPACE=cbrs
CERTM_OUTPUT=k8s-test/target/eric-sec-certm-deployment-configuration.json
SCRIPTING_HOST=general-scripting-0
SCRIPTING_USER=administrator
SCRIPTING_PASS=TestPassw0rd
SCRIPTING_HOME=home/shared/administrator

while getopts 'n:o:' opt; do
  case "$opt" in
    n)
      CBRS_NAMESPACE="$OPTARG"
      ;;
    o)
      CERTM_OUTPUT="$OPTARG"
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

echo "Script parameters"
echo "  CBRS_NAMESPACE="$CBRS_NAMESPACE
echo "  CERTM_OUTPUT="$CERTM_OUTPUT
echo "  SCRIPTING_HOST="$SCRIPTING_HOST
echo "  SCRIPTING_USER="$SCRIPTING_USER
echo "  SCRIPTING_PASS="$SCRIPTING_PASS

echo "Generating unique entity ID"
ENTITY_ID="${CBRS_NAMESPACE}_$(date +%s)"
echo "  ENTITY_ID="$ENTITY_ID

echo "Set unique log file"
LOG_FILE=k8s-test/target/logs/enroll_${ENTITY_ID}.log
echo "  LOG_FILE="$LOG_FILE

echo "Get ENM namespace"
ENM_NAMESPACE=$(helm list -A | grep eric-enm-pre-deploy-integration | awk '{ print $2 }')
echo "  ENM_NAMESPACE="$ENM_NAMESPACE

echo "Get virtual service IP"
VIRTUAL_SERVICE_IP=$(kubectl -n $ENM_NAMESPACE get ericingress pkiraserv -o yaml | grep virtualServiceIP | awk '{ print $2 }')
echo "  VIRTUAL_SERVICE_IP="$VIRTUAL_SERVICE_IP

echo "Check access to scripting"
kubectl exec -n ${CBRS_NAMESPACE}-test -it gauge-runner -- bash -c "\
sshpass -p ${SCRIPTING_PASS} ssh -o StrictHostKeyChecking=no ${SCRIPTING_USER}@${SCRIPTING_HOST}.${ENM_NAMESPACE}.svc.cluster.local \
pwd" 1>>${LOG_FILE}

echo "Copy script to scripting"
kubectl cp -c general-scripting k8s-test/scripts/enroll.py ${ENM_NAMESPACE}/${SCRIPTING_HOST}:/${SCRIPTING_HOME}/ --retries=3

echo "Executing enroll.py script"
kubectl exec -n ${CBRS_NAMESPACE}-test -it gauge-runner -- bash -c "\
sshpass -p ${SCRIPTING_PASS} ssh -o StrictHostKeyChecking=no ${SCRIPTING_USER}@${SCRIPTING_HOST}.${ENM_NAMESPACE}.svc.cluster.local \
python3 enroll.py ${ENTITY_ID} ${VIRTUAL_SERVICE_IP}" 1>>${LOG_FILE}

echo "Copy result from scripting"
rm -rf $CERTM_OUTPUT
kubectl cp -c general-scripting ${ENM_NAMESPACE}/${SCRIPTING_HOST}:${SCRIPTING_HOME}/enroll_${ENTITY_ID}/eric-sec-certm-deployment-configuration.json $CERTM_OUTPUT --retries=3

echo "CertM file written to: "$CERTM_OUTPUT
