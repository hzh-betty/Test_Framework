import sys
import os
import traceback
import configparser
from conf import setting
from common.record_log import logs

class OperatorConfig:
    def __init__(self, filename=None):
        # 1. Determine the configuration file path
        if filename is None:
            self.__filename = setting.FILE_PATH['CONFIG']
        else:
            self.__filename = filename

        # 2. Read the configuration file
        self.config = configparser.ConfigParser()
        try:
            self.config.read(self.__filename, encoding='utf-8')
        except configparser.MissingSectionHeaderError :
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logs.error(str(traceback.format_exc(exc_traceback)))

        logs.debug(f'Config file{self.__filename} successfully read')


    def get_item_value(self,section_name):
        try:
            items = self.config.items(section_name)
        except configparser.NoSectionError :
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logs.error(str(traceback.format_exc(exc_traceback)))
            return None
        logs.debug(f'Get config items: section [{section_name}] = {items}')
        return dict(items)

    def get_section_for_data(self,section_name,option_name):
        try :
            value = self.config.get(section_name,option_name)
        except configparser.NoOptionError :
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logs.error(str(traceback.format_exc(exc_traceback)))
            return None
        except configparser.NoSectionError :
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logs.error(str(traceback.format_exc(exc_traceback)))
            return None

        logs.debug(f'Get config value: section [{section_name}] option [{option_name}] = {value}')
        return value

    def write_config(self,section_name,option_name,option_value):
        # 1. Write data to the configuration file
        if section_name not in self.config.sections():
            self.config.add_section(section_name)
        self.config.set(section_name,option_name,option_value)

        # 2. Save the configuration file
        tmp = self.__filename + '.tmp'
        with open(tmp,'w',encoding='utf-8') as configfile:
            self.config.write(configfile)
        os.replace(tmp,self.__filename)

    def get_section_mysql(self, option):
        return self.get_section_for_data("MYSQL", option)

    def get_section_redis(self, option):
        return self.get_section_for_data("REDIS", option)

    def get_section_clickhouse(self, option):
        return self.get_section_for_data("CLICKHOUSE", option)

    def get_section_mongodb(self, option):
        return self.get_section_for_data("MongoDB", option)

    def get_report_type(self, option):
        return self.get_section_for_data('REPORT_TYPE', option)

    def get_section_ssh(self, option):
        return self.get_section_for_data("SSH", option)