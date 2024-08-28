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
CBRS kubernetes resources health check script. Script takes CBRS namespace as argument and
lists resources status. Log messages based on basic checks.
"""
from __future__ import unicode_literals

import re
import sys
import subprocess
from argparse import ArgumentParser
import argparse
import itertools
import logger
from logger import LogLevel as log


cronjobs = []


def print_line_break():
    """
    Prints line breaks between outputs
    """
    line_break_char_count = 90
    line_break_char = '='
    print(line_break_char * line_break_char_count)


def run_all_healthchecks(k8s_name_space, verbose=True):
    """
    Runs list of commands and shows details on CBRS kubernetes cluster/namespace resources
    """
    display_hc_title(k8s_name_space)
    failed_checks =  check_k8s_nodes(verbose) + \
    check_pods(k8s_name_space, verbose) + \
    check_statefulsets(k8s_name_space, verbose) + \
    check_deployments(k8s_name_space, verbose) + \
    check_jobs(k8s_name_space, verbose) + \
    check_pvc(k8s_name_space, verbose)
    check_ingress(k8s_name_space, verbose)
    check_service(k8s_name_space, verbose)

    return failed_checks


def display_hc_title(k8s_name_space):
    """
    Display the title with the given namespace
    """

    log.info(f"Executing K8s health checks on namespace: {k8s_name_space}")
    print_line_break()


def run_ingress_health_checks(k8s_name_space, verbose):
    """
    Runs k8s specific health check
    """
    check_ingress(k8s_name_space, verbose)
    return 0


def show_ingress(k8s_name_space, verbose):
    """
    There is no condition to validate against in case of ingress
    hence nothing gets displayed for the non-verbose option.
    Lists CBRS ingress details for the verbose option
    """
    command = ['kubectl', 'get', 'ingress', '-n', k8s_name_space]
    header, records = execute_command(command)
    validated_records = {}
    validated_records['good_records'] = records
    validated_records['failed_records'] = []
    validated_records['warning_records'] = []
    print_summary(header, validated_records, verbose)

def run_service_health_checks(k8s_name_space, verbose):
    """
    Runs k8s specific health check
    """
    check_service(k8s_name_space, verbose)
    return 0

def check_service(k8s_name_space, verbose):
    """
    There is no condition to validate against in case of services
    hence nothing gets displayed for the non-verbose option.
    Lists CBRS service details for the verbose option
    """
    command = ['kubectl', 'get', 'service', '-n', k8s_name_space]
    header, records = execute_command(command)
    validated_records = {}
    validated_records['good_records'] = records
    validated_records['failed_records'] = []
    validated_records['warning_records'] = []
    print_summary(header, validated_records, verbose)

def check_ingress(k8s_name_space, verbose):
    """
    Checks health of CBRS ingress
    """
    log.info('Getting CBRS ingress...')
    show_ingress(k8s_name_space, verbose)


def execute_command(command, silent=False):
    """
    Executes given kubectl command that outputs a string formatted to look like a table.
    This function returns the header string and the list of strings representing records
    of this table.

            Parameters:
                    command (list): command with arguments
                    silent (bool):  supress stderr

            Returns:
                    header (string): table header
                    rows (list): table records
    """
    try:
        command_output = subprocess.check_output(
            command, stderr=subprocess.DEVNULL if silent else None).decode().strip()
        rows = command_output.split('\n')
        header = rows.pop(0)
        return header, rows
    except subprocess.CalledProcessError:
        if 'can-i' not in command:
            log.error(f'[{" ".join(command)}] returned non-zero exit code')
    return "", []


def validate_resource_status(header, records, attribute_name, condition=''):
    """
    Based on given condition for a given attribute this function groups and returns
    two lists containing good records and failed records.

            Parameters:
                    header (str): string representing table header
                    records (list): list of strings representing table records
                    attribute_name: (str): name of the attribute
                    condition (str): condition

            Returns:
                    records (list): list of good records
                    failed_records (list): list of failed records
    """
    validated_records = {}
    failed_records = []
    good_records = []
    warning_records = []
    if records:
        header_key_attribute_index = header.split().index(attribute_name)
        for record in records:
            if attribute_name == 'STATUS':
                if record.split()[header_key_attribute_index] != condition:
                    failed_records.append(record)
                    continue
            else:
                readiness = record.split()[header_key_attribute_index].split('/')
                if readiness[0] != readiness[1]:
                    if is_cronjob_instance(record.split()[0]):
                        warning_records.append(record)
                    else:
                        failed_records.append(record)
                        continue

            good_records.append(record)

    validated_records['failed_records'] = failed_records
    validated_records['good_records'] = good_records
    validated_records['warning_records'] = warning_records

    return validated_records


def print_summary(header, validated_records=None, verbose=True, resource_type=None):
    """
    Prints given header and records in form of a coloured table
    """
    good_records = validated_records['good_records']
    failed_records = validated_records['failed_records']
    warning_records = validated_records['warning_records']

    if failed_records or warning_records or (verbose and good_records):
        print(f"{logger.BOLD}{header}{logger.END}")

    if verbose and good_records:
        for record in good_records:
            print(record)

    if warning_records:
        for record in warning_records:
            print(f"{logger.YELLOW}{record}{logger.END}")

    if failed_records:
        for record in failed_records:
            print(f"{logger.RED}{record}{logger.END}")

    if resource_type:
        if warning_records:
            log.info(f'Detected {len(warning_records)} Active CronJobs')
        if failed_records:
            log.error(f'Health check failed.'
                       f'Detected incorrect status for {len(failed_records)} {resource_type}s')
        elif good_records:
            log.info(f'Health check Ok. All {resource_type}s are in correct state')
    print_line_break()


def check_pvc(k8s_name_space, verbose):
    """
    Validate PVCs status
    """
    log.info("Running CBRS PVCs health check")
    command = ['kubectl', 'get', 'pvc', '-n', k8s_name_space]
    header, records = execute_command(command)
    validated_records = validate_resource_status(header, records, 'STATUS', 'Bound')
    print_summary(header, validated_records, verbose, 'PVC')

    return len(validated_records['failed_records'])


def consolidate_output(first_header, first_dataset, second_header, second_dataset):
    """
    Consolidates two datasets into one

            Parameters:
                    first_header (str): string representing table header
                    first_dataset (list): list of strings representing table records
                    second_header (str): string representing table header
                    second_dataset (list): list of strings representing table records
            Returns:
                    reader (str): string representing consolidated header
                    data (list): list of strings representing consolidated records
    """
    header = ''
    data = []
    if first_dataset:
        offset = 0
        nodes_header_length = len(first_header)
        longest_record_length = max(first_dataset, key=len)
        if nodes_header_length > len(longest_record_length):
            offset = len(first_header + ' ' * 4)
        else:
            offset = len(longest_record_length + ' ' * 4)

        header = first_header + \
            ' ' * (offset - len(first_header)) + second_header.split(' ', 1)[1].lstrip()

        for record in first_dataset:
            artifact_name = record.split()[0]
            resource_usage_record = [x for x in second_dataset if artifact_name in x]
            if resource_usage_record:
                resource_usage_details = resource_usage_record.pop().split(' ', 1)[1].lstrip()
                record = record + ' ' * \
                         (offset - len(record)) + resource_usage_details

            data.append(record)

    return header, data


def check_k8s_nodes(verbose = True):
    """
    Validate status of worker nodes
    """
    log.info('Running k8s nodes health check')
    check_permissions_command = ['kubectl', 'auth', 'can-i' , 'get', 'nodes']
    permissions_header = execute_command(check_permissions_command, silent=True)

    if permissions_header[0] == "yes":
        get_nodes_command = ['kubectl', 'get', 'nodes']
        optional_flag = '--use-protocol-buffers' if use_protocol_buffers() else ''
        top_nodes_command = ['kubectl', 'top', 'nodes', optional_flag]
        nodes_header, nodes = execute_command(get_nodes_command)
        top_nodes_header, nodes_resource_usage = execute_command(top_nodes_command)
        header, nodes = consolidate_output(nodes_header, \
                          nodes, top_nodes_header, nodes_resource_usage)
        validated_records = validate_resource_status(header, nodes,  'STATUS', 'Ready')
        print_summary(header, validated_records, verbose, 'Node')
        return len(validated_records['failed_records'])

    log.warning('Permission not granted: k8s nodes health check not available due to'
                ' insufficient permissions')
    print_line_break()
    return 0


def check_jobs(k8s_name_space, verbose=True):
    """
    Checks health of CBRS jobs
    """
    log.info("Running CBRS jobs health check")
    command = ['kubectl', 'get', 'jobs', '-n', k8s_name_space]
    header, records = execute_command(command)

    validated_records = validate_resource_status(header, records, 'COMPLETIONS')
    print_summary(header, validated_records, verbose, 'Job')

    return len(validated_records['failed_records'])


def check_deployments(k8s_name_space, verbose=True):
    """
    Checks health of CBRS deployments
    """
    log.info("Running CBRS deployments health check")
    command = ['kubectl', 'get', 'deployments', '-n', k8s_name_space]
    header, records = execute_command(command)
    validated_records = validate_resource_status(header, records, 'READY')
    print_summary(header, validated_records, verbose, 'Deployment')

    return len(validated_records['failed_records'])


def check_statefulsets(k8s_name_space, verbose):
    """
    Checks health of CBRS statefulsets
    """
    log.info("Running CBRS statefulsets health check")
    command = ['kubectl', 'get', 'statefulsets', '-n', k8s_name_space]
    header, records = execute_command(command)
    validated_records = validate_resource_status(header, records, 'READY')
    print_summary(header, validated_records, verbose, 'StatefulSet')

    return len(validated_records['failed_records'])


def print_pods_summary(header, healthy_pods, restarting_pods, failed_pods, verbose=True):
    """
    Outputs pods information
    """
    if (verbose and healthy_pods) or failed_pods or restarting_pods:
        print(f"{logger.BOLD}{header}{logger.END}")

    if healthy_pods and verbose:
        for record in healthy_pods:
            print(record)
    if restarting_pods:
        for record in filter(lambda i: i not in failed_pods, restarting_pods):
            print(f"{logger.YELLOW}{record}{logger.END}")
    if failed_pods:
        for pod in failed_pods:
            restarts_attribute_index = re.split(r'(\s+)', header).index('RESTARTS')
            pod_attributes = re.split(r'(\s+)', pod)
            restarts = pod_attributes[restarts_attribute_index]
            if int(restarts) > 0:
                pod_attributes[restarts_attribute_index] = \
                    f"{logger.YELLOW}{pod_attributes[restarts_attribute_index]}" \
                    f"{logger.END}{logger.RED}"
            pod = "".join(pod_attributes)
            print(f"{logger.RED}{pod}{logger.END}")

    if restarting_pods:
        log.warning(f'Detected restarts of {len(restarting_pods)} Pods')
    if failed_pods:
        log.error(f'Health check failed. Detected incorrect status for {len(failed_pods)} Pods')
    elif healthy_pods:
        log.info('Health check OK. All Pods are in correct state')

    print_line_break()


def is_cronjob_instance(resource_name):
    """
    Check if the given resource is an instance created by the CronJob
            Parameters:
                    resource_name (str): name of the resource

            Returns:
                    Boolean: True if the resource is an instance of the CronJob, otherwise False
    """
    for cronjob in cronjobs:
        if cronjob in resource_name:
            return True
    return False


def get_cronjobs(k8s_name_space):
    """
    Retrieves CronJobs from the given namespace

            Parameters:
                    k8s_name_space (str): k8s namespace

    """
    log.info("Running CBRS cronjobs health check")
    get_cronjobs_command = ['kubectl', 'get', 'cronjobs', '-n', k8s_name_space]
    header, records = execute_command(get_cronjobs_command)
    if len(header) > 0:
        header_attributes = header.split()
        name_attribute_index = header_attributes.index('NAME')
        for record in records:
            cronjob_name = record.split()[name_attribute_index]
            cronjobs.append(cronjob_name)



def validate_pods_health(header, pods):
    """
    This function groups and returns three lists containing good, restarting and failed pods.

            Parameters:
                    header (str): string representing table header
                    pods (list): list of strings representing table records

            Returns:
                    healthy_pods (list): list of good pods
                    restarting_pods (list): list of failed pods
                    failed_pods (list): list of pods with restarts
    """
    healthy_pods = []
    restarting_pods = []
    failed_pods = []
    if pods:
        header_attributes = header.split()
        name_attribute_index = header_attributes.index('NAME')
        status_attribute_index = header_attributes.index('STATUS')
        restarts_attribute_index = header_attributes.index('RESTARTS')
        for pod in pods:
            healthy = True
            pod_attributes = pod.split()
            status = pod_attributes[status_attribute_index]
            restarts = int(pod_attributes[restarts_attribute_index])
            allowed_status = ['Running', 'Completed']
            if is_cronjob_instance(pod_attributes[name_attribute_index]):
                allowed_status = ['Init', 'ContainerCreating',
                                  'PodInitializing', 'Running', 'Completed']
            if status not in allowed_status:
                failed_pods.append(pod)
                healthy = False
            if restarts:
                restarting_pods.append(pod)
                healthy = False

            if healthy:
                healthy_pods.append(pod)

    return healthy_pods, restarting_pods, failed_pods


def use_protocol_buffers():
    """
    Returns True if kubectl version is higher or equal to 1.21.0, otherwise returns False
    :return: Boolean
    """
    kubectl_version_command = ['kubectl', 'version', '--client']
    try:
        command_output = subprocess.check_output(kubectl_version_command).decode().strip()
        kubectl_client_version = re.findall("([0-9]+[.]+[0-9]+[.]+[0-9])", command_output)[0]
        return int(kubectl_client_version.replace('.', '')) >= 1210
    except subprocess.CalledProcessError:
        log.error(f'[{" ".join(kubectl_version_command)}] returned non-zero exit code')
    return False


def check_pods(k8s_name_space, verbose=True):
    """
    Checks health of CBRS pods
    """
    log.info("Running CBRS pods health check")
    get_pods_command = ['kubectl', 'get', 'pods', '-n', k8s_name_space]
    pods_header, pods = execute_command(get_pods_command)
    if not pods_header:
        print_line_break()
        return 0
    optional_flag = '--use-protocol-buffers' if use_protocol_buffers() else ''
    top_pods_command = ['kubectl', 'top', 'pods', '-n', k8s_name_space, optional_flag]
    top_pods_header, pods_resource_usage = execute_command(top_pods_command)

    header, pods = consolidate_output(pods_header, pods, top_pods_header, pods_resource_usage)

    healthy_pods, restarting_pods, failed_pods = validate_pods_health(header, pods)

    print_pods_summary(header, healthy_pods, restarting_pods, failed_pods, verbose)

    return len(failed_pods)


def main(args):
    """
    Check for arguments and execute all health checks if default argument is passed else
    ask the user to select a healthcheck to run from a given list of options
    """
    print_line_break()
    if args.namespace:
        k8s_name_space = args.namespace
    else:
        log.error('Kubernetes namespace - '
                    'A valid namespace must be provided to the script by the user.'
                    'Healthcheck not performed.')
        sys.exit(1)

    get_cronjobs(k8s_name_space)

    if args.resource:
        failed_checks = get_selected_resource(k8s_name_space, args.resource, args.verbose)
    else:
        failed_checks = run_all_healthchecks(k8s_name_space, args.verbose)

    if failed_checks:
        sys.exit(1)


def get_arguments(args):
    """
    Processes command arguments
    """
    parser = ArgumentParser(description='Executes k8s healthchecks.', usage=argparse.SUPPRESS,)
    parser.add_argument('-n', '--namespace', default="",
    help='set the namespace to run the healthcheck on')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        dest='verbose', help='set verbose output')
    resources=["deployments", "ingress", "jobs", "nodes", "pods",  "pvc", "statefulsets", "service"]
    parser.add_argument('-r', '--resource', choices=resources, action="append", default=[],
                        nargs='*', help='run selected checks with space separated'
                                        ' list of k8s resources : '
                        '[' + ', '.join(resources) + ']', metavar='')

    try:
        return parser.parse_args(args)
    except SystemExit:
        if '-h' in args or '--help' in args:
            sys.exit(0)
        parser.print_help()
        sys.exit(1)


def get_selected_resource(k8s_name_space, selected_resource, verbose=False):
    """
    Process health check on selected columns
    """
    display_hc_title(k8s_name_space)

    resource_set = {
        'run_all_kubernetes_health_checks': lambda: run_all_healthchecks(k8s_name_space, verbose),
        'check_pods': lambda: check_pods(k8s_name_space, verbose),
        'check_nodes': lambda: check_k8s_nodes(verbose),
        'check_ingress': lambda: run_ingress_health_checks(k8s_name_space, verbose),
        'check_jobs': lambda: check_jobs(k8s_name_space, verbose),
        'check_deployments': lambda: check_deployments(k8s_name_space, verbose),
        'check_statefulsets': lambda: check_statefulsets(k8s_name_space, verbose),
        'check_pvc': lambda: check_pvc(k8s_name_space, verbose),
        'check_service': lambda: run_service_health_checks(k8s_name_space, verbose)
    }

    failed_checks = 0

    flatten_list_of_resources = list(itertools.chain(*selected_resource))
    selected_resource = list(dict.fromkeys(flatten_list_of_resources))

    for resource in selected_resource:
        failed_checks += resource_set['check_' + str(resource)]()
    return failed_checks


if __name__ == '__main__':
    main(get_arguments(sys.argv[1:]))
