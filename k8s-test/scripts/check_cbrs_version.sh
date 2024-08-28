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

# Asserts output of cbrs_version.py script, in the following format:
# 2023-12-13T13:46:11 - CBRS 24.02 (Package Version: 0.36.0-38) (CBRS product number: CXF 101 0177)
#
# Asserts output of cbrs_version.py script with --history flag, in the following format:
# 2023-12-13T13:46:11 - UG - CBRS 24.02 (Package Version: 0.36.0-38) (CBRS product number: CXF 101 0177)
#

VERSION_OUTPUT_FILE=$1
OPTION=$2

INSTALL_TIME_REGEX="[1-9][0-9]{3}\-[0-1]?[1-9]\-[0-3]?[0-9]+T[0-2]?[0-9]:[0-5]?[0-9]:[0-5]?[0-9]+"
SPRINT_VERSION_REGEX="CBRS [0-9]?[0-9]\.[0-9][0-9]"
PACKAGE_VERSION_REGEX="\(Package Version: [0-9]+\.[0-9]+\.[0-9]+[-+]*\S*\)"
PRODUCT_NUMBER_REGEX="\(CBRS product number: CXF 101 0177\)"

assert_install_time() {
  echo "Assert CBRS version contains install time"
  install_time_found=$(grep -E "$INSTALL_TIME_REGEX" "$VERSION_OUTPUT_FILE")
  if [ -z "$install_time_found" ]; then
    fail "No match found for install time"
  fi
}

assert_sprint_version() {
  echo "Assert CBRS version contains sprint version"
  sprint_version_found=$(grep -E "$SPRINT_VERSION_REGEX" "$VERSION_OUTPUT_FILE")
  if [ -z "$sprint_version_found" ]; then
    fail "No match found for sprint version"
  fi
}

assert_package_version() {
  echo "Assert CBRS version contains package version"
  package_version_found=$(grep -E "$PACKAGE_VERSION_REGEX" "$VERSION_OUTPUT_FILE")
  if [ -z "$package_version_found" ]; then
    fail "No match found for package version"
  fi
}

assert_product_number() {
  echo "Assert CBRS version contains product number"
  product_number_found=$(grep -E "$PRODUCT_NUMBER_REGEX" "$VERSION_OUTPUT_FILE")
  if [ -z "$product_number_found" ]; then
    fail "No match found for product number"
  fi
}

assert_upgrade_activity() {
  echo "Asserting CBRS version history contains upgrade activity"
  upgrade_activity_found=$(grep -E "\- UG \-" "$VERSION_OUTPUT_FILE")
  if [ -z "$upgrade_activity_found"  ]; then
    fail "No match found for upgrade activity"
  fi
}

fail() {
    echo "$@"
    echo
    echo "CBRS Version test FAILED"
    exit 1
}

echo
echo "Checking CBRS Version information in output file '$VERSION_OUTPUT_FILE':"
cat "$VERSION_OUTPUT_FILE"
echo

assert_install_time
assert_sprint_version
assert_package_version
assert_product_number

if [ "$OPTION" = "--history" ]; then
  assert_upgrade_activity
fi

echo
echo "CBRS Version test PASSED"
echo
