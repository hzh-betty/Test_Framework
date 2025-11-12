import datetime
import time
from logging.handlers import RotatingFileHandler
from conf import setting
import logging
import os

log_path = setting.FILE_PATH['LOG']
if not os.path.exists(log_path):
    os.makedirs(log_path)
logfile_name  = log_path + r'\test.{}.logs'.format(time.strftime('%Y%m%d'))

class RecordLog:
    def __init__(self):
        self.handle_overdue_log()


    @staticmethod
    def handle_overdue_log():
        """Delete logs older than 7 days"""
        now_time = datetime.datetime.now()
        offset_date = datetime.timedelta(days=7)
        before_date = (now_time + offset_date).timestamp()
        for file in os.listdir(log_path):
            file_name = os.path.join(log_path, file)
            if os.path.isfile(file_name):
                file_create_time = os.path.getctime(file_name)
                if file_create_time < before_date:
                    os.remove(file_name)

    @staticmethod
    def output_logging():
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            # 1. Create logger
            logger.setLevel(setting.LOG_LEVEL)
            logger_format = logging.Formatter( '%(levelname)s - %(asctime)s -'
                                                  ' %(filename)s:%(lineno)d -[%(module)s:'
                                                  '%(funcName)s] - %(message)s')

            # 2. Create file handler
            fh = RotatingFileHandler(filename=logfile_name,mode='a',maxBytes=1024*1024*5,
                                     backupCount=5, encoding='utf-8')
            fh.setLevel(setting.LOG_LEVEL)
            fh.setFormatter(logger_format)
            logger.addHandler(fh)

            # 3. Create console handler
            sh = logging.StreamHandler()
            sh.setLevel(setting.CONSOLE_LOG_LEVEL)
            sh.setFormatter(logger_format)
            logger.addHandler(sh)
        return logger

logs = RecordLog().output_logging()

if __name__ == '__main__':
    logs.debug('this is a debug log')
    logs.info('this is an info log')
    logs.warning('this is a warning log')
    logs.error('this is an error log')
    logs.critical('this is a critical log')
