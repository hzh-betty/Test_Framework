import base64
import calendar
import datetime
import hashlib
import os.path
import random
import re
import time
from hashlib import sha1
from conf.setting import ROOT_DIR
from pandas.tseries.offsets import Day
from common.operator_csv import OperatorCsv
from common.operator_yaml import OperatorYaml
import csv


class DebugTalk:

    def __init__(self):
        self.read = OperatorYaml()  # Initialize YAML reader

    def get_extract_data(self, node_name, randoms=None) -> str:
        """
        Get data from extract.yaml. If randoms is number, use specific logic.
        :param node_name: key in extract.yaml
        :param randoms: int to control return
        :return: data string or list
        """
        data = self.read.get_data()
        if randoms is not None and bool(re.compile(r'^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$').match(randoms)):
            randoms = int(randoms)
            data_value = {
                randoms: self.get_extract_order_data(data, randoms),
                0: random.choice(data),
                -1: ','.join(data),
                -2: ','.join(data).split(','),
            }
            data = data_value[randoms]
        else:
            data = self.read.get_extract_yaml(node_name, randoms)
        return data

    @staticmethod
    def get_extract_order_data(data, randoms):
        """Get ordered data if randoms is not 0, -1, -2"""
        if randoms not in [0, -1, -2]:
            return data[randoms - 1]
        return None

    @staticmethod
    def md5_encryption(params):
        """MD5 encryption"""
        enc_data = hashlib.md5()
        enc_data.update(params.encode(encoding="utf-8"))
        return enc_data.hexdigest()

    @staticmethod
    def sha1_encryption(params):
        """SHA1 encryption"""
        enc_data = sha1()
        enc_data.update(params.encode(encoding="utf-8"))
        return enc_data.hexdigest()

    @staticmethod
    def base64_encryption(params):
        """Base64 encoding"""
        base_params = params.encode("utf-8")
        encr = base64.b64encode(base_params)
        return encr

    @staticmethod
    def timestamp():
        """Current 10-digit timestamp"""
        t = int(time.time())
        return t

    @staticmethod
    def timestamp_thirteen():
        """Current 13-digit timestamp"""
        t = int(time.time()) * 1000
        return t

    @staticmethod
    def start_time():
        """Yesterday standard time"""
        now_time = datetime.datetime.now()
        day_before_time = (now_time - 1 * Day()).strftime("%Y-%m-%d %H:%M:%S")
        return day_before_time

    @staticmethod
    def end_time():
        """Current standard time"""
        now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return now_time

    @staticmethod
    def start_forward_time():
        """15 days before today, date only"""
        now_time = datetime.datetime.now()
        day_before_time = (now_time - 15 * Day()).strftime("%Y-%m-%d")
        return day_before_time

    @staticmethod
    def start_after_time():
        """7 days after today, date only"""
        now_time = datetime.datetime.now()
        day_after_time = (now_time + 7 * Day()).strftime("%Y-%m-%d")
        return day_after_time

    @staticmethod
    def end_year_time():
        """Current date, date only"""
        now_time = datetime.datetime.now().strftime("%Y-%m-%d")
        return now_time

    @staticmethod
    def today_zero_timestamp():
        """Today 00:00:00 timestamp, 10 digits"""
        time_stamp = int(time.mktime(datetime.date.today().timetuple()))
        return time_stamp

    @staticmethod
    def today_zero_stamp():
        """Today 00:00:00 timestamp, 13 digits"""
        time_stamp = int(time.mktime(datetime.date.today().timetuple())) * 1000
        return time_stamp

    @staticmethod
    def specified_zero_tamp(days):
        """Timestamp of 00:00:00 for specific day"""
        tom = datetime.date.today() + datetime.timedelta(days=int(days))
        date_tamp = int(time.mktime(time.strptime(str(tom), '%Y-%m-%d'))) * 1000
        return date_tamp

    @staticmethod
    def specified_end_tamp(days):
        """Timestamp of 23:59:59 for specific day"""
        tom = datetime.date.today() + datetime.timedelta(days=int(days) + 1)
        date_tamp = int(time.mktime(time.strptime(str(tom), '%Y-%m-%d'))) - 1
        return date_tamp * 1000

    @staticmethod
    def month_start_time():
        """First day of current month, date only"""
        now = datetime.datetime.now()
        this_month_start = datetime.datetime(now.year, now.month, 1).strftime("%Y-%m-%d")
        return this_month_start

    @staticmethod
    def month_end_time():
        """Last day of current month, date only"""
        now = datetime.datetime.now()
        this_month_end = datetime.datetime(now.year, now.month, calendar.monthrange(now.year, now.month)[1]).strftime(
            "%Y-%m-%d")
        return this_month_end

    @staticmethod
    def month_first_time():
        """First day of month 00:00:00 timestamp, 13 digits"""
        now = datetime.datetime.now()
        this_month_start = datetime.datetime(now.year, now.month, 1)
        first_time_stamp = int(time.mktime(this_month_start.timetuple())) * 1000
        return first_time_stamp

    @staticmethod
    def fenceAlarm_alarmType_random():
        """Random fence alarm type"""
        alarm_type = ["1", "3", "8", "2", "5", "6"]
        fence_alarm = random.choice(alarm_type)
        return fence_alarm

    @staticmethod
    def fatigueAlarm_alarmType_random():
        """Random fatigue alarm type"""
        alarm_type = ["1", "3", "8"]
        fatigue_alarm = random.choice(alarm_type)
        return fatigue_alarm

    @staticmethod
    def jurisdictionAlarm_random():
        """Random jurisdiction alarm type"""
        alarm_type = ["1", "3", "8", "2", "5", "6", "9"]
        jurisdiction_alarm = random.choice(alarm_type)
        return jurisdiction_alarm

    @staticmethod
    def vehicle_random():
        """Random vehicle number from CSV"""
        data = OperatorCsv(os.path.join(ROOT_DIR, 'data', 'vehicleNo.csv')).get_each_column_by_name('vno')
        vel_num = random.choice(data)
        return vel_num

    @staticmethod
    def read_csv_data(file_name):
        """Read CSV data, return first row"""
        with open(os.path.join(ROOT_DIR, 'data', file_name), 'r', encoding='utf-8') as f:
            csv_reader = list(csv.reader(f))
            user_lst, passwd_lst = [], []
            for user, passwd in csv_reader:
                user_lst.append(user)
                passwd_lst.append(passwd)
            return user_lst[0], passwd_lst[0]

    @staticmethod
    def get_baseurl(host):
        """Get base URL from config"""
        from conf.operator_config import OperatorConfig
        conf = OperatorConfig()
        url = conf.get_section_for_data('api_envi', host)
        return url