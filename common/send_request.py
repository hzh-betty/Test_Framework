import json
import allure
import pytest
import requests
import urllib3

from conf import setting
from common.record_log import logs
from common.operator_yaml import OperatorYaml



class SendRequest:
    """Send HTTP requests (supports GET and POST)."""

    def __init__(self, cookie=None):
        self.cookie = cookie
        self.read = OperatorYaml()

    def get(self, url, data, header):
        """
        :param url: Request URL
        :param data: Request parameters
        :param header: Request headers
        :return: Response data in dict format
        """
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        try:
            if data is None:
                response = requests.get(url, headers=header, cookies=self.cookie, verify=False)
            else:
                response = requests.get(url, data, headers=header, cookies=self.cookie, verify=False)
        except requests.RequestException as e:
            logs.error(e)
            return None
        except Exception as e:
            logs.error(e)
            return None

        return self.to_response_dic(response)

    def post(self, url, data, header):
        """
        :param url: Request URL
        :param data: Request parameters
        :param header: Request headers
        :return: Response data in dict format
        """
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        try:
            if data is None:
                response = requests.post(url, header, cookies=self.cookie, verify=False)
            else:
                response = requests.post(url, data, headers=header, cookies=self.cookie, verify=False)
        except requests.RequestException as e:
            logs.error(e)
            return None
        except Exception as e:
            logs.error(e)
            return None

        return self.to_response_dic(response)

    @staticmethod
    def to_response_dic(response):
        # Response time in milliseconds
        res_ms = response.elapsed.microseconds / 1000
        # Response time in seconds
        res_second = response.elapsed.total_seconds()
        response_dict = dict()
        response_dict['code'] = response.status_code  # HTTP status code
        response_dict['text'] = response.text  # Response body (raw text)
        try:
            response_dict['body'] = response.json().get('body')
        except Exception:
            response_dict['body'] = ''
        response_dict['res_ms'] = res_ms
        response_dict['res_second'] = res_second
        return response_dict

    def send_request(self, **kwargs):
        """General request handler using requests.session()."""
        session = requests.session()
        result = None
        cookie = {}

        try:
            result = session.request(**kwargs)
            set_cookie = requests.utils.dict_from_cookiejar(result.cookies)

            # Save cookies if returned by server
            if set_cookie:
                cookie['Cookie'] = set_cookie
                self.read.write_data(cookie)
                logs.info("Cookie: %s" % cookie)

            logs.info("Response: %s" % (result.text if result.text else result))

        except requests.exceptions.ConnectionError:
            logs.error("ConnectionError - Connection failed")
            pytest.fail("Request error. Possible cause: too many connections or request frequency too high.")
        except requests.exceptions.HTTPError:
            logs.error("HTTPError")
        except requests.exceptions.RequestException as e:
            logs.error(e)
            pytest.fail("Request failed. Please check system or data.")

        return result

    def run_main(self, name, url, case_name, header, method, cookies=None, file=None, **kwargs):
        """
        Execute API requests.
        :param name: API name
        :param url: Request URL
        :param case_name: Test case name
        :param header: Request headers
        :param method: HTTP method
        :param cookies: Cookies (optional)
        :param file: File upload (optional)
        :param kwargs: Request parameters (data/json/params)
        :return: Response object
        """

        try:
            # Log details for reports
            logs.info('API Name: %s' % name)
            logs.info('URL: %s' % url)
            logs.info('Method: %s' % method)
            logs.info('Case Name: %s' % case_name)
            logs.info('Headers: %s' % header)
            logs.info('Cookies: %s' % cookies)

            req_params = json.dumps(kwargs, ensure_ascii=False)

            if "data" in kwargs or "json" in kwargs or "params" in kwargs:
                allure.attach(req_params, 'Request Parameters', allure.attachment_type.TEXT)
                logs.info("Request Params: %s" % kwargs)
        except Exception as e:
            logs.error(e)

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        response = self.send_request(
            method=method,
            url=url,
            headers=header,
            cookies=cookies,
            files=file,
            timeout=setting.API_TIMEOUT,
            verify=False,
            **kwargs
        )

        return response
