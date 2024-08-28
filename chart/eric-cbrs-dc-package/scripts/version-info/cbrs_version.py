#!/usr/bin/python3

# --------------------------------------------------------------------------
#  COPYRIGHT Ericsson 2023
#
#  The copyright to the computer program(s) herein is the property of
#  Ericsson Inc. The programs may be used and/or copied only with written
#  permission from Ericsson Inc. or in accordance with the terms and
#  conditions stipulated in the agreement/contract under which the
#  program(s) have been supplied.
# --------------------------------------------------------------------------
"""
This script provides CBRS version and CBRS version history information for CBRS DC SA Installation.
Usage:
python3 Scripts/version-info/cbrs_version.py <CBRS DC SA Namespace> [--history]
"""

import subprocess
import json
import sys
import re

CBRS_VERSION_HISTORY_CONFIGMAP = "eric-cbrs-version-history"
CBRS_VERSION_CONFIGMAP = "eric-cbrs-version-configmap"


def is_invalid_namespace(namespace):
    """
    Verify namespace input provided by user
    """
    pattern = re.compile(r"^[a-zA-Z0-9-_]{1,63}$")
    return not pattern.match(namespace)


def run_kubectl_command(command):
    """
    This is method for running kubectl commands
    """
    try:
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        error_msg = str(e.stderr.strip())
        if e.returncode == 1:
            print(f"Kubectl Error: Command execution failed. Details: {error_msg}")
        else:
            print(
                f"Kubectl Error: Unexpected error occurred. Error code: {e.returncode}, Message: {error_msg}"
            )
        sys.exit(1)


def run_helm_command(command):
    """
    This is method for running helm commands
    """
    try:
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        error_msg = str(e.stderr.strip())

        if "release: not found" in error_msg:
            print(
                f"Helm Error: eric-cbrs-dc-common-cbrs Release not found. Details: {error_msg}"
            )
            sys.exit(1)
        elif e.returncode == 1:
            print(f"Helm Error: Command execution failed. Details: {error_msg}")
        else:
            print(
                f"Helm Error: Unexpected error occurred. Error code: {e.returncode}, Message: {error_msg}"
            )

        sys.exit(1)


def get_last_helm_operation(namespace):
    """
    This method will identify the last helm operation performed in CBRS deployment

    Details of different helm actions
    II - Initial Install
    UG - Upgrade
    RB - Rollback
    UN - Unknown helm operation, ex. in the case where error occurs and helm operation results in failure

    """
    release_name = "eric-cbrs-dc-common-" + namespace
    time_stamp_length = 19
    helm_history_command = [
        "helm",
        "history",
        release_name,
        "--namespace",
        namespace,
        "--max",
        "1",
        "-o",
        "json",
    ]

    helm_output = run_helm_command(helm_history_command)
    try:
        history = json.loads(helm_output)
        if not history:
            print(
                "Error: No history found for the eric-cbrs-dc-common-cbrs Helm release. The release might not exist."
            )
            sys.exit(1)

        last_entry = history[-1]
        last_description = last_entry["description"]

        last_updated_str = last_entry["updated"]
        last_updated_formatted = last_updated_str[:time_stamp_length]

        if "Install complete" in last_description:
            helm_action = "II"
        elif "Upgrade complete" in last_description:
            helm_action = "UG"
        elif "Rollback to" in last_description:
            helm_action = "RB"
        else:
            helm_action = "UN"

        return helm_action, last_updated_formatted
    except json.JSONDecodeError:
        print(
            "Error: Failed to parse JSON from helm output. Please check if Helm is properly configured."
        )
        sys.exit(1)
    except ValueError:
        print(
            "Error: Failed to parse the date from Helm history. Please check the date format."
        )
        sys.exit(1)


def get_cbrs_version_configmap(namespace):
    """
    This method will extract current cbrs version from eric-cbrs-version-configmap
    """
    command = [
        "kubectl",
        "get",
        "configmap",
        CBRS_VERSION_CONFIGMAP,
        "-n",
        namespace,
        "-o",
        "json",
    ]

    kubectl_output = run_kubectl_command(command)

    try:
        configmap = json.loads(kubectl_output)
    except json.JSONDecodeError:
        print(
            "Error: Failed to parse JSON from kubectl output. Please check if kubectl is properly configured."
        )
        sys.exit(1)

    cbrs_version = configmap.get("data", {}).get(".cbrs-version")

    if not cbrs_version:
        print(
            "Error: The required information related to CBRS version is missing from the eric-cbrs-version-configmap"
        )
        sys.exit(1)

    return cbrs_version


def get_version_history(namespace):
    """
    This method will get the CBRS version history from eric-cbrs-version-history configmap
    """
    command = [
        "kubectl",
        "get",
        "configmap",
        CBRS_VERSION_HISTORY_CONFIGMAP,
        "-n",
        namespace,
        "-o",
        "json",
    ]

    try:
        kubectl_output = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
        ).stdout
        configmap = json.loads(kubectl_output)
        history = configmap.get("data", {}).get("history", "")
        return history.split("\n") if history else []
    except subprocess.CalledProcessError as e:
        error_msg = str(e.stderr.strip())
        if ("not found" in error_msg) or ("NotFound" in error_msg):
            return []
        else:
            print("Error: Failed to fetch eric-cbrs-version-history ConfigMap.")
            sys.exit(1)


def create_or_update_history(namespace, version_history_entry):
    """
    Update the CBRS version history in the eric-cbrs-version-history ConfigMap with any new entry.
    This will also create the eric-cbrs-version-history ConfigMap if it does not already exist.
    Args:
        namespace: The CBRS namespace.
        version_history_entry: The latest version history entry.
    """
    history = get_version_history(namespace)
    if not history:
        create_version_history_configmap(namespace, version_history_entry)
    elif version_history_entry != history[-1]:
        update_version_history(namespace, version_history_entry)


def create_version_history_configmap(namespace, initial_entry):
    """
    This method will create eric-cbrs-version-history ConfigMap and add a CBRS version record
    """
    command = [
        "kubectl",
        "create",
        "configmap",
        CBRS_VERSION_HISTORY_CONFIGMAP,
        "-n",
        namespace,
        "--from-literal=history=" + initial_entry,
    ]

    run_kubectl_command(command)


def update_version_history(namespace, new_entry):
    """
    This method will update eric-cbrs-version-history ConfigMap by appending a CBRS version record
    """

    current_history = get_version_history(namespace)
    updated_history = (
        "\n".join(current_history + [new_entry]) if current_history else new_entry
    )

    command = [
        "kubectl",
        "patch",
        "configmap",
        CBRS_VERSION_HISTORY_CONFIGMAP,
        "-n",
        namespace,
        "--patch",
        json.dumps({"data": {"history": updated_history}}),
        "-o",
        "json",
    ]

    run_kubectl_command(command)


def print_version_history(history):
    """
    This method will print version history in more readable way
    """
    print("CBRS Version history:")
    print(" ")
    print("Timestamp            Type  CBRS Version")
    for entry in reversed(history):
        print(entry)
    print(" ")


def main():
    try:
        num_args = len(sys.argv) - 1

        if num_args == 1 or (num_args == 2 and sys.argv[2] == "--history"):
            namespace = sys.argv[1]

            if is_invalid_namespace(namespace):
                print("Error: Invalid namespace provided.")
                sys.exit(1)

            cbrs_version = get_cbrs_version_configmap(namespace)
            helm_action, last_updated = get_last_helm_operation(namespace)

            version_history_entry = f"{last_updated} - {helm_action} - {cbrs_version}"
            create_or_update_history(namespace, version_history_entry)

            if num_args == 1:
                version_entry = f"{last_updated} - {cbrs_version}"
                print(version_entry)
            else:
                history = get_version_history(namespace)
                if history:
                    print_version_history(history)
                else:
                    print("CBRS version history not found.")
        else:
            print(
                "Usage: python3 Scripts/version-info/cbrs_version.py <CBRS DC SA Namespace> [--history]"
            )
            sys.exit(1)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
