#! /bin/bash
#
# COPYRIGHT Ericsson 2024
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
#

usage(){
  cat <<USAGE_TEXT
This script checks to ensure that the given namespace does not have resources left behind, after the namespace is cleaned.

The script checks: helm releases, persistent volume claims (PVCs), pods, secrets, services, roles, role bindings, ingress class, statefulsets.
If any of the listed resources contain data, the test will fail.

Usage: ./$(basename "$0") [namespace]
Checks to confirm there are no resources present in the specified NAMESPACE.

Example: ./$(basename "$0") cbrs
USAGE_TEXT
}

passed=0
failed=0
warnings=0

namespace="$1"

max_attempts=15
attempt_num=1

assert_helm_releases_removed() {
  local resource_name="Helm releases"
  helm_count=$(helm list --all -n "$namespace" 2>/dev/null | grep -v "NAME" | wc -l)
  if [ "$helm_count" -eq 0 ]; then
    pass "$resource_name"
  else
    fail "$resource_name" "$helm_count"
  fi
}

assert_pods_removed(){
  local resource_name="Pods"

  while [ $attempt_num -lt $max_attempts ]; do
    pods_count=$(kubectl get pods -n "$namespace" 2>/dev/null | grep -v -e "NAME" | wc -l)

    if [ "$pods_count" -eq 0 ]; then
      pass "$resource_name"
      return 0
    fi
    echo "Detected $pods_count pods still not deleted. Sleeping for 10 seconds..."
    sleep 10

    ((attempt_num++))
  done

  fail "$resource_name" "$pods_count"
  return 1
}

assert_pvc_removed() {
  local resource_name="PVC"
  pvc_count=$(kubectl get pvc -n "$namespace" 2>/dev/null | grep -v "NAME" | wc -l)
  if [ "$pvc_count" -eq 0 ]; then
    pass "$resource_name"
  else
    fail "$resource_name" "$pvc_count"
  fi
}

assert_secrets_removed(){
  local resource_name="Secrets"
  all_secrets_count=$(kubectl get secrets -n "$namespace" 2>/dev/null | grep -v "NAME" | wc -l)
  remaining_secrets_count=$(check_remaining_secrets)
  unexpected_secrets_count=$((all_secrets_count - remaining_secrets_count))

  if [ "$unexpected_secrets_count" -eq 0 ]; then
    pass "$resource_name"
  else
    fail "$resource_name" "$unexpected_secrets_count"
  fi
  if [ "$remaining_secrets_count" -gt 0 ]; then
    warning "$resource_name" "$remaining_secrets_count"
  fi
}

assert_services_removed(){
  local resource_name="Services"
  services_count=$(kubectl get services -n "$namespace" 2>/dev/null | grep -v "NAME" | grep -v "\-test" | wc -l)
  if [ "$services_count" -eq 0 ]; then
    pass "$resource_name"
  else
    fail "$resource_name" "$services_count"
  fi
}

assert_roles_removed(){
  local resource_name="Roles"
  roles_count=$(kubectl get roles -n "$namespace" 2>/dev/null | grep -v "NAME" | wc -l)
  if [ "$roles_count" -eq 0 ]; then
    pass "$resource_name"
  else
    fail "$resource_name" "$roles_count"
  fi
}

assert_rolebindings_removed(){
  local resource_name="Rolebindings"
  rolebindings_count=$(kubectl get rolebindings -n "$namespace" 2>/dev/null | grep -v "NAME" | wc -l)
  if [ "$rolebindings_count" -eq 0 ]; then
    pass "$resource_name"
  else
    fail "$resource_name" "$rolebindings_count"
  fi
}

assert_ingressclass_removed(){
  local resource_name="Ingressclass"
  ingress_count=$(kubectl get ingressclass | grep "$namespace" 2>/dev/null | grep -v "NAME" | wc -l)
  if [ "$ingress_count" -eq 0 ]; then
    pass "$resource_name"
  else
    fail "$resource_name" "$ingress_count"
  fi
}

assert_statefulset_removed(){
  local resource_name="Statefulset"
  statefulset_count=$(kubectl get statefulset -n "$namespace" 2>/dev/null | grep -v "NAME" | wc -l)
  if [ "$statefulset_count" -eq 0 ]; then
    pass "$resource_name"
  else
    fail "$resource_name" "$statefulset_count"
  fi
}

# It needs to be investigated in the future why these secrets are not deleted when the Helm charts are uninstalled
check_remaining_secrets(){
  local secrets_to_verify=("armdocker" "eric-cnom-server-certm-certificate-secret" "eric-log-transformer-asymmetric-secret" "eric-sec-admin-user-management-iam-authentication-ldap-client-tls-cert")
  local remaining_secrets_count=0

  for secret in "${secrets_to_verify[@]}"; do
    if kubectl get secret "$secret" -n "$namespace" >/dev/null 2>&1; then
      ((remaining_secrets_count++))
    fi
  done

  echo "$remaining_secrets_count"
}

pass(){
  local resource_name=$1
  echo "$resource_name NOT in namespace: PASSED"
  ((passed++))
}

fail(){
  local resource_name=$1
  local resource_count=$2
  echo "$resource_name found in namespace: FAILED"
  echo "Number of $resource_name found: $resource_count"
  ((failed++))
}

warning(){
  local resource_name=$1
  local resource_count=$2
  echo "Known "$resource_name" found "$resource_count": WARNING"
  ((warnings++))
}

print_test_report(){
  echo "==========================================================================================="
  echo "Test Report:"
  echo "-------------------------------------------------------------------------------------------"
  if (( failed > 0 )); then
      echo "Test FAILED."
      echo "Passed: $passed, failed: $failed, warnings: $warnings"
      echo "==========================================================================================="
      exit 1
  else
      echo "Test PASSED."
      echo "Passed: $passed, failed: $failed, warnings: $warnings"
      echo "==========================================================================================="
      exit 0
  fi
}

main() {
    if (( $# != 1 )); then
      usage 1>&2
      exit 1
    fi

    echo "==========================================================================================="
    echo "Checking for resources in namespace $namespace..."
    echo "==========================================================================================="

    assert_pods_removed
    assert_helm_releases_removed
    assert_pvc_removed
    assert_secrets_removed
    assert_services_removed
    assert_roles_removed
    assert_rolebindings_removed
    assert_ingressclass_removed
    assert_statefulset_removed
    print_test_report
}

main "$@"