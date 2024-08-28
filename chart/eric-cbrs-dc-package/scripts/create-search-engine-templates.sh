#bin/bash!
###########################################################################
# COPYRIGHT Ericsson 2022
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
###########################################################################

CACERT=/run/secrets/tls-root-ca/cacertbundle.pem
CERT=/run/secrets/se-client-cert/clientcert.pem
KEY=/run/secrets/se-client-cert/clientkey.pem

HOST=$SEARCH_ENGINE
PORT=$SEARCH_ENGINE_PORT
BASE_URL=$(printf 'https://%s:%s/' "$HOST" "$PORT")
REQUEST_INTERVAL=5
COMPONENT=$(cat /template/component_template.json)
INDEX=$(cat /template/index_template.json)

# *******************************************************
# Function Name: sendRequest
# Description: Securely sends the given data to the specified path
# GLOBALS:
#   - CACERT
#   - CERT
#   - KEY
#   - URL
# ARGS:
#   - $1, The URL path to send the data too
#   - $2, The data to be sent in the request body
# RETURN:
#   - 0 if successful
#   - non-zero on error
# *******************************************************
sendRequest() {
  FULL_URL=$(printf '%s%s' "$BASE_URL" "$1")
  RESPONSE="false"
  while true
  do
    RESPONSE=$(curl -X PUT --cacert $CACERT --cert $CERT --key $KEY "$FULL_URL" -H 'Content-Type: application/json' -d "$2")
    #Checking result before sleeping
    if [[ $RESPONSE = '{"acknowledged":true}' ]]; then
      # If successful break out of loop
      break
    fi
    # Sleep before sending another request
    sleep $REQUEST_INTERVAL
  done
}

echo "Waiting for $HOST to be available..."
/bin/bash -c "/var/tmp/check_service.sh -s $HOST"

echo "Attempting to create component template..."
sendRequest _component_template/cbrs_component_template "$COMPONENT"
echo "Component template created..."

echo "Attempting to create index template..."
sendRequest _index_template/cbrs_index_template "$INDEX"
echo "Index template created..."

echo "Templates created successfully."