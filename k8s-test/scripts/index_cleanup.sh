#!/bin/bash

###########################################################################
# COPYRIGHT Ericsson 2023
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
###########################################################################

KUBECTL=/usr/local/bin/kubectl
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
SIX_MONTHS_OLDER=$(date -d "182 days ago" '+%Y%m%d')
SEVEN_DAYS_OLDER=$(date -d "6 days ago" '+%Y%m%d')
declare -g INGEST_POD

usage() {
  echo "Usage: $0 <Namespace of CBRS DC SA>"
  echo "Example: $0 cbrs"
}

setup() {
  local log_dir="${SCRIPT_DIR}/index_cleanup_logs"
  mkdir -p "$log_dir"

  # Cleanup old logs before creating a new one
  cleanup_old_logs "$log_dir"

  timestamp=$(date '+%Y%m%d-%H%M%S')
  log_file="$log_dir/index_cleanup_$timestamp.log"
}

cleanup_old_logs() {
  local log_directory="$1"
  local max_logs=30 # Set the maximum number of log files to keep

  # Find and delete the oldest files exceeding the max_logs count
  find "$log_directory" -maxdepth 1 -type f -name 'index_cleanup_*.log' \
    -printf '%T+ %p\n' | sort -r | tail -n +$((max_logs + 1)) | cut -d ' ' -f 2- | xargs -r rm --
}

set_variables() {
  INGEST_POD=$($KUBECTL get pods -n "$1" | grep ingest | grep Running | awk '{print $1}')
}

print_initial_info() {
  echo "Seven days ago date: $SEVEN_DAYS_OLDER"
  echo "Six months ago date: $SIX_MONTHS_OLDER"
  echo "The namespace argument passed is: $1"
  echo "The ingest pod in CBRS deployment is: $INGEST_POD"
}

cbrsEsRest() {
  local namespace=$1
  shift
  $KUBECTL -n "$namespace" exec -c ingest "$INGEST_POD" -- /bin/esRest "$@"
  return $?
}

cluster_information() {
  echo "###########################################"
  echo "Information on data-search-engine cluster"
  echo "###########################################"
  cbrsEsRest "$1" GET /
  local status=$?
  if [[ $status -ne 0 ]]; then
    echo "Error occurred in cluster_information with status $status"
    exit $status
  fi
  echo ""
}

health_check() {
  echo "###########################################"
  echo "Healthcheck for data-search-engine"
  echo "###########################################"
  cbrsEsRest "$1" GET /_cluster/health?pretty
  local status=$?
  if [[ $status -ne 0 ]]; then
    echo "Error occurred in health_check with status $status"
    exit $status
  fi
  echo ""
}

check_read_only_indices() {
  echo "###########################################"
  echo "Check if any indices have gone into read-only mode"
  echo "###########################################"
  cbrsEsRest "$1" GET /_cluster/state/blocks?pretty
  local status=$?
  if [[ $status -ne 0 ]]; then
    echo "Error occurred in check_read_only_indices with status $status"
    exit $status
  fi
  echo ""
}

disk_usage_before_cleanup() {
  echo "###########################################"
  echo "Before cleanup - Disk usage for data-search-engine data pods"
  echo "###########################################"
  cbrsEsRest "$1" GET "/_cat/allocation?v&h=disk.used,disk.avail,disk.total,disk.percent,node"
  local status=$?
  if [[ $status -ne 0 ]]; then
    echo "Error occurred in disk_usage_before_cleanup with status $status"
    exit $status
  fi
  echo ""
}

list_indices_before_cleanup() {
  echo "###########################################"
  echo "Before cleanup - List of all the indices present in data-search-engine"
  echo "###########################################"
  cbrsEsRest "$1" GET /_cat/indices?v
  local status=$?
  if [[ $status -ne 0 ]]; then
    echo "Error occurred in list_indices_before_cleanup with status $status"
    exit $status
  fi
  echo ""
}

date_wise_list_of_indices() {
  indices_output=$(cbrsEsRest "$1" GET /_cat/indices?v)
  local status=$?

  if [[ $status -ne 0 ]]; then
    echo "Error occurred in date_wise_list_of_indices while running cbrsEsRest with status $status"
    exit $status
  fi

  if [[ -z "$indices_output" ]]; then
    echo "Error occurred in date_wise_list_of_indices, No indices present"
    exit 1
  fi

  echo "###########################################"
  echo "Date wise list of indexes"
  echo "###########################################"
  echo "$indices_output" | awk '
    BEGIN {
      FS=" ";
      validInput=0;
    }
    NR > 1 {

      # Example output row to be parsed is as following
      # green  open   cbrs_info_logs_index-2023.11.18           5A-k4EmbQ86oRWsdm81EDA   5   1      88925            0     44.9mb         22.3mb
      # Example index name cbrs_info_logs_index-2023.11.18

      split($3, parts, "-");
      date=parts[length(parts)]; # The date is the last part of index name
      gsub(/\./, "-", date); # replace . with - in date
      indices[date]=indices[date] " " $3;
      validInput=1;
    }
    END {
      if (!validInput) {
        print "Error in date_wise_list_of_indices, No valid data to process.";
        exit 1;
      }
      for (date in indices) {
        print "Date: " date;
        # Split concatenated indices into an array of indices which belong to same date
        n=split(indices[date], indexArray, " ");
        for (i=1; i <= n; i++) {
          if (indexArray[i] != "") {
            print indexArray[i];
          }
        }
        print "";
      }
    }
  '

  local awk_status=$?
  if [[ $awk_status -ne 0 ]]; then
    echo "Error occurred in date_wise_list_of_indices during awk processing with status $awk_status"
    exit $awk_status
  fi
}

retention_policy() {
  echo "###########################################"
  echo "Refer following policy for index retention in CBRS"
  echo ""
  echo "Retension period for following indexes is 7 days"
  echo "1. cbrs_info_logs_index"
  echo "2. cbrs_warn_and_above_logs_index"
  echo "3. cbrs_info_dc_service_index"
  echo "4. cbrs_debug_logs_index"
  echo ""
  echo "Retension period for following indexes is 180 days"
  echo "1. cbrs_security_logs_index"
  echo "2. cbrs_audit_logs_index"
  echo "###########################################"
}

delete_old_indices() {
  echo "###########################################"
  echo "Index deletion starts from here"
  echo "###########################################"

  indices_output=$(cbrsEsRest "$1" GET /_cat/indices?v)
  local status=$?

  if [[ $status -ne 0 ]]; then
    echo "Error occurred in delete_old_indices while running cbrsEsRest with status $status"
    exit $status
  fi

  if [[ -z "$indices_output" ]]; then
    echo "Error occurred in delete_old_indices, No indices present"
    exit 1
  fi

  IFS=$'\n' read -r -d '' -a indices_to_delete < <(echo "$indices_output" | awk -v seven_days_older="$SEVEN_DAYS_OLDER" -v six_month_older="$SIX_MONTHS_OLDER" '
    BEGIN {
      FS=" ";
    }
    NR > 1 {
      # Split the index name by '-' to seperate date of index creation
      split($3, parts, "-");
      # The date is the last part of index name
      date=parts[length(parts)];
      # replace . with empty string in date, this format will make date comparision easy
      gsub(/\./, "", date);
      # First check indexes which have 7 days validity
      if (date < seven_days_older && ($3 ~ /^cbrs_info_logs_index-|^cbrs_warn_and_above_logs_index-|^cbrs_info_dc_service_index-|^cbrs_debug_logs_index-/)) {
        print $3;
      }
      # Check indexes which have 6 month validity
      if (date < six_month_older && ($3 ~ /^cbrs_security_logs_index-|^cbrs_audit_logs_index-/)) {
        print $3;
      }
    }
  ' && printf '\0')

  if [[ ${#indices_to_delete[@]} -eq 0 ]]; then
    echo "No indices found that match the deletion criteria."
    return 0
  fi

  for index in "${indices_to_delete[@]}"; do
    if [ -n "$index" ]; then
      echo "Deleting index: $index"
      cbrsEsRest "$1" DELETE "/$index?pretty"
      local delete_status=$?
      if [ $delete_status -ne 0 ]; then
        echo "Error deleting index $index with status $delete_status"
      else
        echo "Index $index successfully deleted."
      fi
    fi
  done

}

disk_usage_after_cleanup() {
  echo "###########################################"
  echo "After cleanup - Disk usage for data-search-engine data pods"
  echo "###########################################"
  cbrsEsRest "$1" GET "/_cat/allocation?v&h=disk.used,disk.avail,disk.total,disk.percent,node"
  local status=$?
  if [[ $status -ne 0 ]]; then
    echo "Error occurred in disk_usage_after_cleanup with status $status"
    exit $status
  fi
  echo ""
}

list_indices_after_cleanup() {
  echo "###########################################"
  echo "After cleanup - List of all the indexes present in data-search-engine"
  echo "###########################################"
  cbrsEsRest "$1" GET '/_cat/indices?v'
  local status=$?
  if [[ $status -ne 0 ]]; then
    echo "Error occurred in list_indices_after_cleanup with status $status"
    exit $status
  fi
  echo ""
}

main() {
  local namespace="$1"
  set_variables "$namespace"
  print_initial_info "$namespace"
  cluster_information "$namespace"
  health_check "$namespace"
  check_read_only_indices "$namespace"
  disk_usage_before_cleanup "$namespace"
  list_indices_before_cleanup "$namespace"
  date_wise_list_of_indices "$namespace"
  retention_policy
  delete_old_indices "$namespace"
  disk_usage_after_cleanup "$namespace"
  list_indices_after_cleanup "$namespace"
}

if [[ "$#" -ne 1 ]]; then
  usage
  exit 1
fi

setup
main "$1" &>"${log_file}"