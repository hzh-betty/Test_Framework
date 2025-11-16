# -*- coding: utf-8 -*-
import time
import pytest
import warnings

from common.operator_yaml import OperatorYaml
from base.remove_file import remove_files
from common.ding_robot import send_dd_msg
from conf.setting import dd_msg

yfd = OperatorYaml()


@pytest.fixture(scope="session", autouse=True)
def clear_extract():
    # Ignore HTTPS and Resource warnings
    warnings.simplefilter('ignore', ResourceWarning)

    # Clear YAML data and remove temporary report files
    yfd.clear_data()
    remove_files("./report/temp", ['json', 'txt', 'attach', 'properties'])


def generate_test_summary(terminal_reporter):
    """Generate a summary string of test results"""
    total = terminal_reporter._numcollected
    passed = len(terminal_reporter.stats.get('passed', []))
    failed = len(terminal_reporter.stats.get('failed', []))
    error = len(terminal_reporter.stats.get('error', []))
    skipped = len(terminal_reporter.stats.get('skipped', []))
    duration = time.time() - terminal_reporter._sessionstarttime

    summary = f"""
    Automation Test Results Summary:
    Total test cases: {total}
    Passed: {passed}
    Failed: {failed}
    Errors: {error}
    Skipped: {skipped}
    Total duration: {duration:.2f}s
    """
    print(summary)
    return summary


def pytest_terminal_summary(terminal_reporter):
    """Collect pytest results and print/send summary"""
    summary = generate_test_summary(terminal_reporter)
    if dd_msg:
        send_dd_msg(summary)
