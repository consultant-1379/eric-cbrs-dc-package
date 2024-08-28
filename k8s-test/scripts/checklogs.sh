#! /bin/bash
#
# COPYRIGHT Ericsson 2023
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
#
readonly NAMESPACE=$1
readonly LOGS_FOLDER=k8s-test/target/logs

DATE=$(date +'%Y-%m-%d_%H-%M-%S')
readonly LOG_TEST_EXEMPTIONS=k8s-test/scripts/checklogs_exemptions.txt
readonly LOG_TEST=$LOGS_FOLDER/log_test-$DATE.txt
readonly LOG_REPORT=$LOGS_FOLDER/log_report-$DATE.txt

# shellcheck disable=SC2010
POD_LOGS=$(ls -t $LOGS_FOLDER | grep all-pods  | head -1)

# shellcheck disable=SC2010
ADP_LOGS=$LOGS_FOLDER/$(ls -t ${LOGS_FOLDER} | grep logs_"$NAMESPACE" | grep tgz | head -1)

usage(){
  cat <<USAGE_TEXT
Bash script that checks the ADP and POD logs and assures there are non empty log files present for each pod.

Exemptions file checklogs_exemptions.txt can be populated with a list of names where logs are not mandatory.

Usage: ./$(basename "$0") [namespace]
Check the ADP and POD logs and ensure there are non-empty log files present for each pod in NAMESPACE.

Example: ./$(basename "$0") cbrs
USAGE_TEXT
}

check_pod_logs() {
  local pods_to_check
  local file_size

  add_to_log_test "Checking POD logs in file $POD_LOGS"

  pods_to_check=$(tar --exclude="*/*/*" -tf $LOGS_FOLDER/"$POD_LOGS" | awk -F"/" '{ print $2 }' | grep .)

  for pod in $pods_to_check; do
    add_to_log_test "  $pod"
    for logfile in $(tar -ztvf $LOGS_FOLDER/"$POD_LOGS"  | grep log$ | grep "$pod" | awk '{ print $6 }'); do

      file_size=$(tar -ztvf $LOGS_FOLDER/"$POD_LOGS" | grep "$pod" | grep "$logfile"$ | awk '{ print $3 }')
      if [[ $file_size != "0" ]]; then
        echo "$pod" pod "$file_size" "$logfile" >> "$LOG_REPORT"
      fi
      add_to_log_test "    $file_size $logfile"
    done
  done
}

check_adp_logs() {
  local pods_to_check
  local file_size

  add_to_log_test "Checking ADP logs in $ADP_LOGS"

  pods_to_check=$(tar --exclude="*/*/*/*" -tf "$ADP_LOGS" | grep "/logs/" | grep ".txt$" | grep -E -v "kube_podstolog.txt|top_node_output|top_pod_output.txt" | awk -F/logs/ '{ print $2 }' | awk -F_ '{ print $1}' | uniq)

  for pod in $pods_to_check; do
    add_to_log_test "  $pod"
    for logfile in $(tar -ztvf "$ADP_LOGS"  | grep "/logs/$pod" | awk '{ print $6 }'); do
      file_size=$(tar -ztvf "$ADP_LOGS" | grep "/logs/$pod" | grep "$logfile"$ | awk '{ print $3 }')
      if [[ $file_size != "0" ]]; then
        echo "$pod" adp "$file_size" "$logfile" >> "$LOG_REPORT"
      fi
      add_to_log_test "    $file_size $logfile"
    done
  done
}

assert_each_pod_has_logs() {
  local -i number_of_logfiles
  local -i exemption
  local -i passed=0
  local -i warning=0
  local -i failed=0

  local pod_list_file
  local pods

  add_to_log_test "Asserting each pod has logs"

  pod_list_file=$(tar -tf "$ADP_LOGS" | grep kube_podstolog.txt)
  pods=$(tar xfO "$ADP_LOGS" -C $LOGS_FOLDER "$pod_list_file" | tail -n +2 | awk '{ print $1}')
  for pod in $pods; do
    number_of_logfiles=$(grep --count "^$pod" "$LOG_REPORT")
    if [[ $number_of_logfiles == "0" ]]; then
      exemption=$(echo "$pod" | grep -c -f $LOG_TEST_EXEMPTIONS)
      if [[ $exemption != "0" ]]; then
        ((warning++))
        add_to_log_test "WARNING $pod has no logs"
      else
        ((failed++))
        add_to_log_test "FAILED  $pod has no logs"
      fi
    else
      add_to_log_test "PASSED  $pod has $number_of_logfiles log files"
      ((passed++))
    fi
  done

  add_to_log_test "Log report written to $LOG_REPORT"
  echo "Test report written to $LOG_TEST"

  if [ "$failed" -gt "0" ]; then
    add_to_log_test "There are test FAILURES. Passed: $passed, warning: $warning, failed: $failed"
    exit 1
  else
    add_to_log_test "Test PASSED. Passed: $passed, warning: $warning, failed: $failed"
    exit 0
  fi
}

add_to_log_test() {
  echo "$@" | tee -a "$LOG_TEST"
}

#Main
main() {
  if (( $# != 1 )); then
    usage 1>&2
    exit 1
  fi

  check_pod_logs
  check_adp_logs

  sort -o "$LOG_REPORT" "$LOG_REPORT"

  assert_each_pod_has_logs
}

main "$@"
