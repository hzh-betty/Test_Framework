import json
import re
from json.decoder import JSONDecodeError

import allure
import jsonpath

from common.assertions import Assertions
from common.debugtalk import DebugTalk
from common.operator_yaml import OperatorYaml
from common.record_log import logs
from common.send_request import SendRequest
from conf.operator_config import OperatorConfig



class RequestBase:

    def __init__(self):
        self.run = SendRequest()
        self.conf = OperatorConfig()
        self.read = OperatorYaml()
        self.asserts = Assertions()

    @staticmethod
    def replace_load(data):
        """Parse and replace dynamic variables in YAML data."""
        str_data = data
        if not isinstance(data, str):
            str_data = json.dumps(data, ensure_ascii=False)

        for i in range(str_data.count('${')):
            if '${' in str_data and '}' in str_data:
                start_index = str_data.index('$')
                end_index = str_data.index('}', start_index)
                ref_all_params = str_data[start_index:end_index + 1]

                # Extract function name
                func_name = ref_all_params[2:ref_all_params.index("(")]
                # Extract parameters inside parentheses
                func_params = ref_all_params[ref_all_params.index("(") + 1:ref_all_params.index(")")]

                # Call function using getattr
                extract_data = getattr(DebugTalk(), func_name)(*func_params.split(',') if func_params else "")

                if extract_data and isinstance(extract_data, list):
                    extract_data = ','.join(e for e in extract_data)

                str_data = str_data.replace(ref_all_params, str(extract_data))

        # Restore to original type
        if data and isinstance(data, dict):
            data = json.loads(str_data)
        else:
            data = str_data

        return data

    def specification_yaml(self, base_info, test_case):
        """
        Main method to handle API requests.
        :param base_info: baseInfo section in YAML
        :param test_case: testCase section in YAML
        """
        try:
            params_type = ['data', 'json', 'params']
            url_host = self.conf.get_section_for_data('api_envi', 'host')

            api_name = base_info['api_name']
            allure.attach(api_name, f'API Name: {api_name}', allure.attachment_type.TEXT)

            url = url_host + base_info['url']
            allure.attach(api_name, f'URL: {url}', allure.attachment_type.TEXT)

            method = base_info['method']
            allure.attach(api_name, f'Method: {method}', allure.attachment_type.TEXT)

            header = self.replace_load(base_info['header'])
            allure.attach(api_name, f'Headers: {header}', allure.attachment_type.TEXT)

            # Handle cookies
            cookie = None
            if base_info.get('cookies') is not None:
                cookie = eval(self.replace_load(base_info['cookies']))

            case_name = test_case.pop('case_name')
            allure.attach(api_name, f'Test Case Name: {case_name}', allure.attachment_type.TEXT)

            # Handle assertions
            val = self.replace_load(test_case.get('validation'))
            test_case['validation'] = val
            validation = eval(test_case.pop('validation'))

            # Handle extraction
            extract = test_case.pop('extract', None)
            extract_list = test_case.pop('extract_list', None)

            # Replace parameters
            for key, value in test_case.items():
                if key in params_type:
                    test_case[key] = self.replace_load(value)

            # Handle file upload
            file, files = test_case.pop('files', None), None
            if file is not None:
                for fk, fv in file.items():
                    allure.attach(json.dumps(file), 'Uploaded File')
                    files = {fk: open(fv, mode='rb')}

            # Send request
            res = self.run.run_main(
                name=api_name, url=url, case_name=case_name,
                header=header, method=method, file=files,
                cookies=cookie, **test_case
            )

            status_code = res.status_code
            allure.attach(self.allure_attach_response(res.json()), 'Response Data', allure.attachment_type.TEXT)

            try:
                res_json = json.loads(res.text)

                # Extraction
                if extract is not None:
                    self.extract_data(extract, res.text)
                if extract_list is not None:
                    self.extract_data_list(extract_list, res.text)

                # Assertions
                self.asserts.assert_result(validation, res_json, status_code)

            except JSONDecodeError as js:
                logs.error('Invalid JSON or request failed!')
                raise js
            except Exception as e:
                logs.error(e)
                raise e

        except Exception as e:
            raise e

    @classmethod
    def allure_attach_response(cls, response):
        """Format response for Allure attachment."""
        if isinstance(response, dict):
            return json.dumps(response, ensure_ascii=False, indent=4)
        return response

    def extract_data(self, testcase_extract, response):
        """
        Extract values from response using regex or JSONPath.
        :param testcase_extract: extract field in YAML
        :param response: raw response string
        """
        try:
            pattern_lst = ['(.*?)', '(.+?)', r'(\d)', r'(\d*)']
            for key, value in testcase_extract.items():

                # Regex extraction
                for pat in pattern_lst:
                    if pat in value:
                        ext_lst = re.search(value, response)
                        if pat in [r'(\d+)', r'(\d*)']:
                            extract_data = {key: int(ext_lst.group(1))}
                        else:
                            extract_data = {key: ext_lst.group(1)}
                        self.read.write_data(extract_data)

                # JSONPath extraction
                if '$' in value:
                    ext_json = jsonpath.jsonpath(json.loads(response), value)[0]
                    if ext_json:
                        extract_data = {key: ext_json}
                    else:
                        extract_data = {key: 'No data extracted!'}
                    logs.info('Extracted Value:', extract_data)
                    self.read.write_data(extract_data)

        except Exception as e:
            logs.error(e)

    def extract_data_list(self, testcase_extract_list, response):
        """
        Extract multiple values (regex or JSONPath). Returns list.
        :param testcase_extract_list: extract_list field in YAML
        :param response: raw response string
        """
        try:
            for key, value in testcase_extract_list.items():

                # Regex multiple extraction
                if "(.+?)" in value or "(.*?)" in value:
                    ext_list = re.findall(value, response, re.S)
                    if ext_list:
                        extract_data = {key: ext_list}
                        logs.info('Regex extracted list: %s' % extract_data)
                        self.read.write_data(extract_data)

                # JSONPath list extraction
                if "$" in value:
                    ext_json = jsonpath.jsonpath(json.loads(response), value)
                    if ext_json:
                        extract_data = {key: ext_json}
                    else:
                        extract_data = {key: "No data extracted (response may be empty)"}
                    logs.info('JSON extracted list: %s' % extract_data)
                    self.read.write_data(extract_data)

        except:
            logs.error('Extraction error! Check extract_list expression.')


