#!/usr/bin/env python3
###########################################################################
# COPYRIGHT Ericsson 2022
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
###########################################################################
"""
Helm chart analyzer.

Analyses integration chart structure and release dates of dependencies.

The usage of the script is as follows:
    python3 helm-chart-analyzer.py <chart-name> <chart-version> <threshold_warning> <threshold_error>

Example:
    python3 helm-chart-analyzer.py eric-cbrs-dc-package 0.39.0-32 21 42
"""

import argparse
import json
import logging
import os
import re
import shutil
import tarfile
from dataclasses import dataclass, field
from datetime import datetime
from distutils.version import LooseVersion
from typing import Optional

import requests
import yaml
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.ERROR)


@dataclass
class ChartInfo:
    name: str
    version: str
    parent: str
    date: Optional[datetime] = None
    repository: Optional[str] = None
    url: Optional[str] = None
    package: Optional[requests.Response] = None
    children: list = field(default_factory=list)
    latest_version: Optional[str] = None
    latest_date: Optional[datetime] = None
    message: Optional[str] = None

    @staticmethod
    def create_chart_info(name: str, version: str, parent: str):
        return ChartInfo(name, version, parent)


repo_sero = "https://arm.sero.gic.ericsson.se/artifactory/proj-exilis-released-helm/"
repo_adp = "https://arm.sero.gic.ericsson.se/artifactory/proj-adp-gs-all-helm/"
repo_adprs = "https://arm.sero.gic.ericsson.se/artifactory/proj-cran-adprs-release-helm"

repo_cbrs_base = "https://arm.seli.gic.ericsson.se/artifactory/proj-eric-cbrs-dc"
repo_cbrs_drop = repo_cbrs_base + "-drop-helm"
repo_cbrs_release = repo_cbrs_base + "-released-helm"
repo_cbrs_int = repo_cbrs_base + "-ci-internal-helm"

default_repos = [
    repo_sero,
    repo_adp,
    repo_adprs,
    repo_cbrs_drop,
    repo_cbrs_release,
    repo_cbrs_int,
]
non_default_chart_folders = {"eric-ctrl-brocli": "backup-restore-cli"}

repositories = {}
charts = []
chart_tree = {}

chart_version_latest = []
chart_version_info = []
chart_version_warning = []
chart_version_error = []


def main():
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("chart_name", help="Name of the chart to check")
    parser.add_argument("chart_version", help="Version of the chart to check")
    parser.add_argument(
        "threshold_warning", help="Days of threshold for dependency version warnings"
    )
    parser.add_argument(
        "threshold_error", help="Days of threshold for dependency version errors"
    )
    chart_name = parser.parse_args().chart_name
    chart_version = parser.parse_args().chart_version

    threshold_warning = int(parser.parse_args().threshold_warning)
    threshold_error = int(parser.parse_args().threshold_error)

    download_package(chart_name, chart_version)

    process_chart_recursively(chart_name, chart_tree, None)
    logging.debug(json.dumps(chart_tree, indent=2, default=str))

    for chart in charts:
        populate_chart_repository(chart)
    logging.debug(json.dumps(repositories, indent=2, default=str))

    for chart in charts:
        populate_chart_date(chart)
    for chart in charts:
        populate_latest_version(chart)
    for chart in charts[1:]:
        populate_message(chart, threshold_warning, threshold_error)
    logging.debug(json.dumps(charts, indent=2, default=str))

    print("Chart structure analysis")
    print()
    print_project_structure(chart_tree, "")
    print()
    print("Dependency version analysis")
    print()
    print_dependency_version_analysis(charts)
    print()
    print("Dependency version summary")
    print()
    print_dependency_version_summary(threshold_warning, threshold_error)
    shutil.rmtree(chart_name)


def print_project_structure(charts: dict, indent: str):
    for chart in charts.keys():
        print(f"{indent}{chart}")
        print_project_structure(charts[chart], f"{indent}    ")


def print_dependency_version_analysis(charts):
    for chart in charts:
        print(chart.name)
        print(f"  Version: {chart.version}")
        print(f"  Date: {str_date(chart.date)}")
        if chart.latest_version is not None:
            print(f"  Latest version: {chart.latest_version}")
        if chart.latest_date is not None:
            print(f"  Latest date: {str_date(chart.latest_date)}")
        if chart.message is not None:
            print(f"  {chart.message}")


def print_dependency_version_summary(threshold_warning: int, threshold_error: int):
    latest = len(chart_version_latest)
    info = len(chart_version_info)
    warnings = len(chart_version_warning)
    errors = len(chart_version_error)

    print(
        f"There are {latest + info + warnings + errors} dependency charts in {charts[0].name} {charts[0].version}."
    )
    print(f"  {latest} of them are the latest available version.")
    print(
        f"  {info + warnings + errors} of them are not on the latest version, out of which"
    )
    print(
        f"  {warnings} of them are {threshold_warning}-{threshold_error} days older than latest: {chart_version_warning}."
    )
    print(
        f"  {errors} of them are {threshold_error} days older than latest version: {chart_version_error}."
    )


def download_package(chart_name, chart_version: str) -> Optional[str]:
    logging.info(f"Downloading and unpacking {chart_name} {chart_version}")
    chart = ChartInfo.create_chart_info(
        name=chart_name, version=chart_version, parent=None
    )
    populate_chart_repository(chart)
    chart_file_name = f"{chart_name}-{chart_version}.tgz"
    with open(chart_file_name, "wb") as output:
        output.write(chart.package.content)
    with tarfile.open(chart_file_name) as file:
        file.extractall()
    os.remove(chart_file_name)


def process_chart_recursively(
    chart_directory: str, chart_tree: dict, parent: Optional[str]
):
    logging.info(f"Processing chart directory {chart_directory}")
    # Load information
    with open(chart_directory + "/Chart.yaml", "r") as stream:
        yaml_data = yaml.safe_load(stream)

    # Process repository data
    if "dependencies" in yaml_data.keys():
        for dep in yaml_data["dependencies"]:
            repositories[dep["name"]] = dep["repository"]

    # Process chart data
    chart_name = yaml_data["name"]
    chart_version = yaml_data["version"]

    charts.append(
        ChartInfo.create_chart_info(
            name=chart_name, version=chart_version, parent=parent
        )
    )
    chart_tree[chart_name] = {}

    # Recursive call
    if os.path.isdir(chart_directory + "/charts"):
        for subdir in os.listdir(chart_directory + "/charts"):
            process_chart_recursively(
                chart_directory + "/charts/" + subdir,
                chart_tree[chart_name],
                chart_directory.split("/")[-1],
            )


def populate_chart_repository(chart: ChartInfo):
    logging.info(f"Populating chart repository: {chart.name}")
    if chart.name in repositories.keys():
        repos_to_check = [repositories[chart.name]]
    else:
        repos_to_check = default_repos

    for repository in repos_to_check:
        response = check_chart_repository(chart.name, chart.version, repository)
        if response.status_code == 200:
            chart.url = response.url
            chart.repository = repository
            chart.package = response
            return
    logging.warning(f"Chart {chart.name} is not found in any of the repositories")


def populate_chart_date(chart: ChartInfo):
    if chart.package is not None:
        logging.info(f"Populating chart date: {chart.name}")
        date = chart.package.headers["Last-Modified"]
        chart.date = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %Z")


def get_chart_folder(chart_name: str):
    if chart_name in non_default_chart_folders.keys():
        return non_default_chart_folders[chart_name]
    else:
        return chart_name


def check_chart_repository(chart_name: str, chart_version: str, repository: str):
    folder = get_chart_folder(chart_name)
    url = f"{repository}/{folder}/{chart_name}-{chart_version}.tgz"
    return requests.get(url, auth=get_auth(repository))


def get_auth(repository: str) -> Optional[tuple]:
    if "sero" in repository:
        username = os.getenv("SERO_USER")
        password = os.getenv("SERO_PASSWORD")
        return username, password
    else:
        return None


def get_versions(chart: ChartInfo) -> list:
    url = f"{chart.repository}/{get_chart_folder(chart.name)}/"
    response = requests.get(url, auth=get_auth(chart.repository))

    versions = []

    for line in BeautifulSoup(response.content, "html.parser").get_text().splitlines():
        if (
            chart.name in line
            and "md5" not in line
            and "sha1" not in line
            and "sha256" not in line
            and ".tgz" in line
        ):
            version = line.split()[0].split(f"{chart.name}-")[1].split(".tgz")[0]
            try:
                chart_date = datetime.strptime(line.split()[1], "%d-%b-%Y")
            except ValueError:
                logging.warning(f"Skipping processing of line {line}")
                continue
            versions.append((version, chart_date))
    return versions


def populate_latest_version(chart: ChartInfo):
    logging.info(f"Populating latest version info {chart.name}")

    latest_version_dates = {}
    latest_versions = {chart.version: None}

    for other_version, other_date in get_versions(chart):
        if other_date >= chart.date:
            clean_version = re.sub(r"[^0-9.+-]", "", other_version)
            if clean_version != other_version:
                logging.warning(
                    f"Invalid characters detected and removed from {other_version}, changed to {clean_version}"
                )

            latest_versions[clean_version] = other_version
            latest_version_dates[clean_version] = other_date

    # Sort versions
    latest_versions_sorted = list(latest_versions.keys())
    latest_versions_sorted.sort(key=LooseVersion)

    # Find the latest version (based on build date)
    latest = latest_versions_sorted[-1]
    latest_version = latest_versions.get(latest)
    latest_date = latest_version_dates.get(latest)
    # Check latest version
    if chart.version != latest_version:
        chart.latest_version = latest_version
        chart.latest_date = latest_date


def populate_message(chart: ChartInfo, threshold_warning: int, threshold_error: int):
    logging.info(f"Populating message for {chart.name}")
    days_old = (datetime.now() - chart.date).days
    if chart.latest_version is not None:
        days_from_latest = (chart.latest_date - chart.date).days
        if days_from_latest <= threshold_warning:
            prefix = "INFO: "
            chart_version_info.append(chart.name)
        elif days_from_latest < threshold_error:
            prefix = "WARNING: "
            chart_version_warning.append(chart.name)
        else:
            prefix = "ERROR: "
            chart_version_error.append(chart.name)

        if is_sub_chart(chart):
            chart.message = f"{prefix}{days_from_latest} day(s) older than latest. {days_old} day(s) old. Check parent chart {chart.parent} for new version."
        else:
            chart.message = f"{prefix}{days_from_latest} day(s) older than latest. {days_old} day(s) old."
    else:
        chart.message = f"INFO: Latest version. {days_old} day(s) old."
        chart_version_latest.append(chart.name)
    if chart.package is None:
        chart.message = "ERROR: Package not found in any of the repositories"


def is_sub_chart(chart: ChartInfo):
    return chart.parent is not None and chart.parent != charts[0].name


def str_date(date: datetime):
    return datetime.strftime(date, "%Y-%m-%d")


if __name__ == "__main__":
    main()
