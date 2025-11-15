import allure
import jsonpath
import operator

from common.record_log import logs
from common.connection import MysqlConnection


class Assertions:
    """
    API assertion modes supported:
    1) String contains assertion
    2) Equality assertion
    3) Inequality assertion
    4) Any value assertion
    5) Database assertion
    """

    @staticmethod
    def contains_assert(value, response, status_code):
        """
        String contains assertion: checks if expected string exists in API response.
        :param status_code:
        :param value: Expected result from YAML
        :param response: Actual API response
        :param status_code:  status code
        :return: Flag, 0=success, >0=failure
        """
        flag = 0
        for assert_key, assert_value in value.items():
            if assert_key == "status_code":
                if assert_value != status_code:
                    flag += 1
                    allure.attach(f"Expected: {assert_value}\nActual: {status_code}", 'Status code assertion failed',
                                  attachment_type=allure.attachment_type.TEXT)
                    logs.error("Contains assertion failed: status code [%s] != [%s]" % (status_code, assert_value))
            else:
                resp_list = jsonpath.jsonpath(response, "$..%s" % assert_key)
                if isinstance(resp_list[0], str):
                    resp_list = ''.join(resp_list)
                if resp_list:
                    assert_value = None if assert_value.upper() == 'NONE' else assert_value
                    if assert_value in resp_list:
                        logs.info("String contains assertion passed: expected [%s], actual [%s]" % (assert_value, resp_list))
                    else:
                        flag += 1
                        allure.attach(f"Expected: {assert_value}\nActual: {resp_list}", 'Text assertion failed',
                                      attachment_type=allure.attachment_type.TEXT)
                        logs.error("Text assertion failed: expected [%s], actual [%s]" % (assert_value, resp_list))
        return flag

    @staticmethod
    def equal_assert(expected_results, actual_results):
        """
        Equality assertion: compares expected and actual results.
        :param expected_results: Expected results from YAML
        :param actual_results: Actual API response
        :return: Flag, 0=success, >0=failure
        """
        flag = 0
        if isinstance(actual_results, dict) and isinstance(expected_results, dict):
            common_keys = list(expected_results.keys() & actual_results.keys())[0]
            new_actual_results = {common_keys: actual_results[common_keys]}
            eq_assert = operator.eq(new_actual_results, expected_results)
            if eq_assert:
                logs.info(f"Equality assertion passed: actual {new_actual_results} equals expected {expected_results}")
                allure.attach(f"Expected: {expected_results}\nActual: {new_actual_results}", 'Equality assertion passed',
                              attachment_type=allure.attachment_type.TEXT)
            else:
                flag += 1
                logs.error(f"Equality assertion failed: actual {new_actual_results} != expected {expected_results}")
                allure.attach(f"Expected: {expected_results}\nActual: {new_actual_results}", 'Equality assertion failed',
                              attachment_type=allure.attachment_type.TEXT)
        else:
            raise TypeError('Equality assertion: both expected and actual results must be dicts!')
        return flag

    @staticmethod
    def not_equal_assert(expected_results, actual_results):
        """
        Inequality assertion: verifies actual result does not equal expected.
        """
        flag = 0
        if isinstance(actual_results, dict) and isinstance(expected_results, dict):
            common_keys = list(expected_results.keys() & actual_results.keys())[0]
            new_actual_results = {common_keys: actual_results[common_keys]}
            eq_assert = operator.ne(new_actual_results, expected_results)
            if eq_assert:
                logs.info(f"Inequality assertion passed: actual {new_actual_results} != expected {expected_results}")
                allure.attach(f"Expected: {expected_results}\nActual: {new_actual_results}", 'Inequality assertion passed',
                              attachment_type=allure.attachment_type.TEXT)
            else:
                flag += 1
                logs.error(f"Inequality assertion failed: actual {new_actual_results} equals expected {expected_results}")
                allure.attach(f"Expected: {expected_results}\nActual: {new_actual_results}", 'Inequality assertion failed',
                              attachment_type=allure.attachment_type.TEXT)
        else:
            raise TypeError('Inequality assertion: both expected and actual results must be dicts!')
        return flag

    @staticmethod
    def assert_response_any(actual_results, expected_results):
        """
        Assert any value in API response.
        :return: 0=pass, >0=fail
        """
        flag = 0
        try:
            exp_key = list(expected_results.keys())[0]
            if exp_key in actual_results:
                act_value = actual_results[exp_key]
                rv_assert = operator.eq(act_value, list(expected_results.values())[0])
                if rv_assert:
                    logs.info("Any value assertion passed")
                else:
                    flag += 1
                    logs.error("Any value assertion failed")
        except Exception as e:
            logs.error(e)
            raise
        return flag

    @staticmethod
    def assert_response_time(res_time, exp_time):
        """
        Assert response time is less than expected.
        """
        try:
            assert res_time < exp_time
            return True
        except Exception:
            logs.error('Response time [%ss] exceeds expected [%ss]' % (res_time, exp_time))
            raise

    @staticmethod
    def assert_mysql_data(expected_results):
        """
        Database assertion: check if query returns expected results.
        :return: 0=success, >0=failure
        """
        flag = 0
        conn = MysqlConnection()
        db_value = conn.execute_query(expected_results)
        if db_value is not None:
            logs.info("Database assertion passed")
        else:
            flag += 1
            logs.error("Database assertion failed: data not found")
        return flag

    def assert_result(self, expected, response, status_code):
        """
        Main assertion method: checks all assertion types. all_flag=0 means pass.
        """
        all_flag = 0
        try:
            logs.info("Expected results from YAML: %s" % expected)
            for yq in expected:
                for key, value in yq.items():
                    if key == "contains":
                        flag = self.contains_assert(value, response, status_code)
                        all_flag += flag
                    elif key == "eq":
                        flag = self.equal_assert(value, response)
                        all_flag += flag
                    elif key == 'ne':
                        flag = self.not_equal_assert(value, response)
                        all_flag += flag
                    elif key == 'rv':
                        flag = self.assert_response_any(actual_results=response, expected_results=value)
                        all_flag += flag
                    elif key == 'db':
                        flag = self.assert_mysql_data(value)
                        all_flag += flag
                    else:
                        logs.error("Unsupported assertion type")
        except Exception as exceptions:
            logs.error('Assertion error: check YAML expected values!')
            raise exceptions

        if all_flag == 0:
            logs.info("Test passed")
            assert True
        else:
            logs.error("Test failed")
            assert False
