#!/usr/bin/python3
###########################################################################
# COPYRIGHT Ericsson 2022
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
###########################################################################
import os
import sys
import xml.etree.ElementTree as xmlParser
from datetime import datetime
from datetime import timedelta
from distutils.dir_util import copy_tree
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        print("""Gauge report aggregator
The script produces an aggregated gauge report in the report target directory')
based on the individual gauge reports stored in the reports source directory')
using the report templates.

Usage "./gauge_report_aggregator.py <reports source directory> <report target directory>
Example "./gauge_report_aggregator.py k8s-test/target/reports/gauge-reports k8s-test/target/reports/html-report""")
        sys.exit(1)

    reports_source_dir = sys.argv[1]
    report_target_dir = sys.argv[2]

    if not os.path.exists(reports_source_dir) or not os.listdir(reports_source_dir):
        print('No report to aggregate in folder:', reports_source_dir)
        return
    elif len(os.listdir(reports_source_dir)) == 1:
        print('No aggregation required as there is only one report found')
        copy_tree(str(next(Path(reports_source_dir).iterdir())) + '/html-report', report_target_dir)
        print('Report file generated:', report_target_dir)
        return
    # Step 1 - copy report resources from source to target
    copy_report_resources(reports_source_dir, report_target_dir)

    # Step 2 - calculate summaries
    total_time, total_specs, total_specs_failed, total_tests, total_tests_failed, total_tests_skipped = calculate_summaries(
        reports_source_dir)

    # Step 3 - render aggregated report
    spec_summaries = list(render_spec_summaries(reports_source_dir, 'specs/').values())
    aggregated_report_content = render_report('', spec_summaries, '',
                                              total_time, total_specs, total_specs_failed, total_tests,
                                              total_tests_failed, total_tests_skipped)
    aggregated_report_file = report_target_dir + '/index.html'
    write_file(aggregated_report_file, aggregated_report_content)

    # Step 4 - render spec reports
    spec_summaries = render_spec_summaries(reports_source_dir, '')
    for source_spec_report in spec_summaries.keys():
        spec_details = extract_spec_details(read_file(source_spec_report))
        spec_report_content = render_report('../', list(spec_summaries.values()), spec_details,
                                            total_time, total_specs, total_specs_failed, total_tests,
                                            total_tests_failed, total_tests_skipped)
        spec_report_name = source_spec_report.split('/')[-1]
        spec_report_file = report_target_dir + '/specs/' + spec_report_name
        write_file(spec_report_file, spec_report_content)


def read_file(file_name):
    with open(file_name, 'r') as file:
        return file.read()


def write_file(file_name, data):
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    with open(file_name, "w") as file:
        file.write(data)
    print('Report file generated:', file_name)


def extract_xml_report(report_dir):
    xml_report = report_dir + '/xml-report/result.xml'
    testsuite = xmlParser.parse(xml_report).getroot().find('testsuite')
    name = testsuite.get('name')
    spec = testsuite.get('package').replace('/gauge-tests/', '')
    time = int(float(testsuite.get('time')))
    tests = int(testsuite.get('tests'))
    skipped = int(testsuite.get('skipped', 0))
    failed = int(testsuite.get('failures'))
    return name, spec, time, tests, failed, skipped


def extract_spec_details(html_report):
    spec_divider = '<div id="specificationContainer" class="details">'
    footer_divider = '<footer class="footer">'
    divided = html_report.split(spec_divider)[1].split(footer_divider)[0]
    spec_details = '</div>'.join(divided.split('</div>')[0:-2])
    return spec_details


def render_spec_row(href, name, time, failed):
    template = read_file(os.path.dirname(__file__) + '/spec_row.tmpl')
    return (template
            .replace('__SPEC_HREF__', href)
            .replace('__SPEC_NAME__', name)
            .replace('__SPEC_TIME__', str(timedelta(seconds=time)))
            .replace('__SPEC_CLASS__', 'passed' if failed == 0 else 'failed'))


def render_report(root_href, spec_rows, spec_details, total_time, total_specs, total_specs_failed, total_tests,
                  total_tests_failed, total_tests_skipped):
    template = read_file(os.path.dirname(__file__) + '/report.tmpl')
    total_specs_passed = total_specs - total_specs_failed
    total_tests_passed = total_tests - total_tests_failed - total_tests_skipped
    return (template
            .replace('__SPEC_ROWS__', "\n" + "\n".join(spec_rows))
            .replace('__ROOT_HREF__', root_href)
            .replace('__DATE__', datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
            .replace('__RATE__', str(round(total_tests_passed / total_tests * 100)) + '%')
            .replace('__TOTAL_TIME__', str(timedelta(seconds=total_time)))
            .replace('__SPEC_DETAILS__', spec_details)
            .replace('__GREEN__',
                     "Congratulations! You've gone all <span class=\"green\">green</span> and saved the environment!" if total_specs_failed == 0 else "")
            .replace('__TOTAL_SPECS__', str(total_specs))
            .replace('__TOTAL_SPECS_PASSED__', str(total_specs_passed))
            .replace('__TOTAL_SPECS_FAILED__', str(total_specs_failed))
            .replace('__TOTAL_SPECS_SKIPPED__', "N/A")
            .replace('__TOTAL_TESTS__', str(total_tests))
            .replace('__TOTAL_TESTS_PASSED__', str(total_tests_passed))
            .replace('__TOTAL_TESTS_FAILED__', str(total_tests_failed))
            .replace('__TOTAL_TESTS_SKIPPED__', str(total_tests_skipped)))


def copy_report_resources(reports_source_dir, reports_target_dir):
    report_source_dir = str(next(Path(reports_source_dir).iterdir())) + '/html-report'
    copy_tree(report_source_dir + '/css', reports_target_dir + '/css')
    copy_tree(report_source_dir + '/fonts', reports_target_dir + '/fonts')
    copy_tree(report_source_dir + '/images', reports_target_dir + '/images')
    copy_tree(report_source_dir + '/js', reports_target_dir + '/js')


def calculate_summaries(reports_source_dir):
    total_time, total_specs, total_specs_failed, total_tests, total_tests_failed, total_tests_skipped = 0, 0, 0, 0, 0, 0
    for report_dir in Path(reports_source_dir).iterdir():
        name, _, time, tests, failed, skipped = extract_xml_report(str(report_dir))
        total_specs += 1
        total_specs_failed += 0 if failed == 0 else 1
        total_tests += tests
        total_tests_skipped += skipped
        total_tests_failed += failed
        total_time += time
        print(name)
        print(f"  Tests: {tests}, Passed: {tests - failed - skipped}, Failed: {failed}, Skipped: {skipped}")
    print(f"Total Specs: {total_specs}, Passed: {total_specs - total_specs_failed}, Failed: {total_specs_failed}, Skipped: N/A")
    print(f"Total Tests: {total_tests}, Passed: {total_tests - total_tests_failed - total_tests_skipped}, Failed: {total_tests_failed}, Skipped: {total_tests_skipped}")
    return total_time, total_specs, total_specs_failed, total_tests, total_tests_failed, total_tests_skipped


def render_spec_summaries(reports_source_dir, target_href):
    rendered_spec_rows = {}
    for report_dir in sorted(Path(reports_source_dir).iterdir(), key=os.path.getmtime):
        name, spec, time, tests, failed, skipped = extract_xml_report(str(report_dir))
        source_spec_report = reports_source_dir + '/' + report_dir.name + '/html-report/' + spec.replace('.spec',
                                                                                                         '.html')
        target_spec_report = target_href + source_spec_report.split('/')[-1]
        rendered_spec_rows[source_spec_report] = render_spec_row(target_spec_report, name, time, failed)
    return rendered_spec_rows


if __name__ == "__main__":
    main()
