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
Bash script that executes a CLI command on a deployment.

After executing the command, it assert the expected response, and retries unitl the expected result is returned.
The script produces a log file with the results.

Options
  -n <namespace> the namespace to run the command
  -d <deployment> the deployment (or pod) to run the command
  -c <command> the command to run
  -e <expected> (optional) the expected regex to match the command output
  -s (optional) to enable scrict execution and fail when command returns error
  -r <retries> (optional) the number of retries before declaring failed execution
  -l <logfile> (optional) the logfile to write the results to
  -t (optional) to enable tracelogs

Usage: $(basename $0) [-n namespace] [-d deployment] [-c command] [-r retries] [-e expected] [-s] [-l logfile] [-t]
Example: $(basename $0) -n cbrs -d eric-ctrl-brocli -c \"brocli list\" -r 5 -e \"COMPLETED\" -l result.log
"

NAMESPACE=cbrs
DEPLOYMENT=eric-ctrl-brocli
EXPECTED=*
RETRIES=0
ATTEMPTS=0
LOGFILE=/dev/null
TRACELOG=false
STRICT=false


while getopts 'n:d:c:r:e:l:ts' opt; do
  case "$opt" in
    n)
      NAMESPACE="$OPTARG"
      ;;
    d)
      DEPLOYMENT="$OPTARG"
      ;;
    c)
      COMMAND="$OPTARG"
      ;;
    e)
      EXPECTED="$OPTARG"
      ;;
    r)
      RETRIES="$OPTARG"
      ;;
    l)
      LOGFILE="$OPTARG"
      ;;
    t)
      TRACELOG=true
      ;;
    s)
      STRICT=true
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

if [ $TRACELOG == true ]; then
  echo "Namespace: "$NAMESPACE
  echo "Deplyoment: "$DEPLOYMENT
  echo "Command: "$COMMAND
  echo "Expected: "$EXPECTED
  echo "Retries: "$RETRIES
  echo "Logfile: "$LOGFILE
fi

mkdir -p $(dirname $LOGFILE)

while [ $RETRIES -ge $ATTEMPTS ]
do
  ATTEMPTS=$(($ATTEMPTS+1))

  if [[ $(kubectl get deployment $DEPLOYMENT -n $NAMESPACE 2>/dev/null) ]] ; then
    RESULT=$(kubectl exec -n $NAMESPACE -it deploy/$DEPLOYMENT -- bash -c "$COMMAND 2>&1" 2>/dev/null)
  else
    RESULT=$(kubectl exec -n $NAMESPACE -it $DEPLOYMENT -- bash -c "$COMMAND 2>&1" 2>/dev/null)
  fi

  RET=$?
  echo "$RESULT"

  if [[ ( $STRICT == false || $RET == 0 ) && $RESULT == *$EXPECTED* ]] ; then
    echo
    if [ $ATTEMPTS -ge 2 ] ; then
      echo "Passed - "$(date)" - Command ["$COMMAND"] result matches ["$EXPECTED"] after ["$ATTEMPTS"] attempts" | tee -a $LOGFILE
    else
      echo "Passed - "$(date)" - Command ["$COMMAND"] result matches ["$EXPECTED"]" | tee -a $LOGFILE
    fi
    exit 0
  else
    sleep 5
  fi
done
echo
echo "Failed - "$(date)" - Command ["$COMMAND"] result NOT matches ["$EXPECTED"] after ["$ATTEMPTS"] attempts" | tee -a $LOGFILE
exit 1
