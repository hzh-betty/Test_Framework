import re
import jenkins
from conf.operator_config import OperatorConfig


class PJenkins(object):
    conf = OperatorConfig()

    def __init__(self):
        self.__config = {
            'url': self.conf.get_section_jenkins('url'),
            'username': self.conf.get_section_jenkins('username'),
            'password': self.conf.get_section_jenkins('password'),
            'timeout': int(self.conf.get_section_jenkins('timeout'))
        }
        self.__server = jenkins.Jenkins(**self.__config)

        self.job_name = self.conf.get_section_jenkins('job_name')

    def get_job_number(self):
        """Get the latest build number of the job"""
        build_number = self.__server.get_job_info(self.job_name).get('lastBuild').get('number')
        return build_number

    def get_build_job_status(self):
        """Get the status of the latest build"""
        build_num = self.get_job_number()
        job_status = self.__server.get_build_info(self.job_name, build_num).get('result')
        return job_status

    def get_console_log(self):
        """Get console log of the latest build"""
        console_log = self.__server.get_build_console_output(self.job_name, self.get_job_number())
        return console_log

    def get_job_description(self):
        """Return job description and URL"""
        description = self.__server.get_job_info(self.job_name).get('description')
        url = self.__server.get_job_info(self.job_name).get('url')
        return description, url

    def get_build_report(self):
        """Return test report of the latest build"""
        report = self.__server.get_build_test_report(self.job_name, self.get_job_number())
        return report

    def report_success_or_fail(self):
        """Summarize test report: counts, pass/fail/skip rates, duration"""
        report_info = self.get_build_report()
        pass_count = report_info.get('passCount')
        fail_count = report_info.get('failCount')
        skip_count = report_info.get('skipCount')
        total_count = int(pass_count) + int(fail_count) + int(skip_count)
        duration = int(report_info.get('duration'))
        hour = duration // 3600
        minute = duration % 3600 // 60
        seconds = duration % 3600 % 60
        execute_duration = f'{hour}h {minute}m {seconds}s'
        content = f'Total {total_count} test cases: Pass: {pass_count}, Fail: {fail_count}, Skip: {skip_count}; Duration: {hour}h {minute}m {seconds}s'
        # Extract test report link from console log
        console_log = self.get_console_log()
        report_line = re.search(r'http://192.168.105.36:8088/job/hbjjapi/(.*?)allure', console_log).group(0)
        report_info = {
            'total': total_count,
            'pass_count': pass_count,
            'fail_count': fail_count,
            'skip_count': skip_count,
            'execute_duration': execute_duration,
            'report_line': report_line
        }
        return report_info


if __name__ == '__main__':
    p = PJenkins()
    res = p.report_success_or_fail()
    # result = re.search(r'http://192.168.105.36:8088/job/hbjjapi/(.*?)allure', res).group(0)
    print(res)

