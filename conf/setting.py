import logging
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

LOG_LEVEL = logging.INFO  # Set file logging level
CONSOLE_LOG_LEVEL = logging.DEBUG  # Set console logging level

API_TIMEOUT = 60  # API request timeout in seconds

SHEET_ID = 0  # Excel Sheet ID

REPORT_TYPE = 'allure'  # Report type: allure or tm

dd_msg = False  # Enable DingTalk message notifications

# Define commonly used file paths
FILE_PATH = {
    'CONFIG': os.path.join(ROOT_DIR, 'conf/config.ini'),
    'LOG': os.path.join(ROOT_DIR, 'logs'),
    'YAML': os.path.join(ROOT_DIR),
    'TEMP': os.path.join(ROOT_DIR, 'report/temp'),
    'TMR': os.path.join(ROOT_DIR, 'report/tm_report'),
    'EXTRACT': os.path.join(ROOT_DIR, 'extract.yaml'),
    'XML': os.path.join(ROOT_DIR, 'data/sql'),
    'RESULT_XML': os.path.join(ROOT_DIR, 'report'),
    'EXCEL': os.path.join(ROOT_DIR, 'data', '测试数据.xls')
}

# Define login request headers
LOGIN_HEADER = {
    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive'
}
