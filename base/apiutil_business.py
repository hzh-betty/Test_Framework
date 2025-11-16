from common.send_request import SendRequest
from common.operator_yaml import OperatorYaml
from common.record_log import logs
from conf.operator_config import OperatorConfig
from common.assertions import Assertions
from common.debugtalk import DebugTalk
import allure
import json
import jsonpath
import re
import traceback
from json.decoder import JSONDecodeError

assert_res = Assertions()


class RequestBase(object):
    def __init__(self):
        self.run = SendRequest()
        self.read = OperatorYaml()
        self.conf = OperatorConfig()

    @staticmethod
    def handler_yaml_list(data_dict):
        """Handle list-type parameters in YAML and convert them to a list format"""
        try:
            for key, value in data_dict.items():
                if isinstance(value, list):
                    value_lst = ','.join(value).split(',')
                    data_dict[key] = value_lst
                return data_dict
        except Exception:
            logs.error(str(traceback.format_exc()))

    def replace_load(self, data):
        """Replace dynamic expressions in YAML using DebugTalk functions"""
        str_data = data
        if not isinstance(data, str):
            str_data = json.dumps(data, ensure_ascii=False)
        for i in range(str_data.count('${')):
            if '${' in str_data and '}' in str_data:
                start_index = str_data.index('$')
                end_index = str_data.index('}', start_index)
                ref_all_params = str_data[start_index:end_index + 1]

                # extract function name
                func_name = ref_all_params[2:ref_all_params.index("(")]
                # extract parameters
                func_params = ref_all_params[ref_all_params.index("(") + 1:ref_all_params.index(")")]

                extract_data = getattr(DebugTalk(), func_name)(*func_params.split(',') if func_params else "")
                if extract_data and isinstance(extract_data, list):
                    extract_data = ','.join(e for e in extract_data)
                str_data = str_data.replace(ref_all_params, str(extract_data))

        # restore original type
        if data and isinstance(data, dict):
            data = json.loads(str_data)
            self.handler_yaml_list(data)
        else:
            data = str_data
        return data

    def specification_yaml(self, case_info):
        """
        Normalize YAML test case format
        :param case_info: list type, case_info[0] → dict
        """
        params_type = ['params', 'data', 'json']
        cookie = None
        try:
            base_url = self.conf.get_section_for_data('api_envi', 'host')
            url = base_url + case_info["baseInfo"]["url"]
            allure.attach(url, f'API URL：{url}')

            api_name = case_info["baseInfo"]["api_name"]
            allure.attach(api_name, f'API Name：{api_name}')

            method = case_info["baseInfo"]["method"]
            allure.attach(method, f'Request Method：{method}')

            header = self.replace_load(case_info["baseInfo"]["header"])
            allure.attach(str(header), 'Request Headers', allure.attachment_type.TEXT)

            try:
                cookie = self.replace_load(case_info["baseInfo"]["cookies"])
                allure.attach(str(cookie), 'Cookie', allure.attachment_type.TEXT)
            except:
                pass

            for tc in case_info["testCase"]:
                case_name = tc.pop("case_name")
                allure.attach(case_name, f'Test Case Name：{case_name}', allure.attachment_type.TEXT)

                # parse validation field
                val = self.replace_load(tc.get('validation'))
                tc['validation'] = val

                validation = eval(tc.pop('validation'))
                allure_validation = str([str(list(i.values())) for i in validation])
                allure.attach(allure_validation, "Expected Result", allure.attachment_type.TEXT)

                extract = tc.pop('extract', None)
                extract_lst = tc.pop('extract_list', None)

                # parse params, data, json fields
                for key, value in tc.items():
                    if key in params_type:
                        tc[key] = self.replace_load(value)

                file, files = tc.pop("files", None), None
                if file is not None:
                    for fk, fv in file.items():
                        allure.attach(json.dumps(file), 'Uploaded File')
                        files = {fk: open(fv, 'rb')}

                res = self.run.run_main(
                    name=api_name,
                    url=url,
                    case_name=case_name,
                    header=header,
                    cookies=cookie,
                    method=method,
                    file=files, **tc
                )

                res_text = res.text
                allure.attach(res_text, 'Response Text', allure.attachment_type.TEXT)
                status_code = res.status_code
                allure.attach(self.allure_attach_response(res.json()), 'Formatted Response', allure.attachment_type.TEXT)

                try:
                    res_json = json.loads(res_text)

                    # parameter extraction
                    if extract is not None:
                        self.extract_data(extract, res_text)
                    if extract_lst is not None:
                        self.extract_data_list(extract_lst, res_text)

                    # perform assertions
                    assert_res.assert_result(validation, res_json, status_code)

                except JSONDecodeError as js:
                    logs.error("System error or invalid API response!")
                    raise js
                except Exception as e:
                    logs.error(str(traceback.format_exc()))
                    raise e

        except Exception as e:
            logs.error(e)
            raise e

    @classmethod
    def allure_attach_response(cls, response):
        """Format response for Allure reporting"""
        if isinstance(response, dict):
            allure_response = json.dumps(response, ensure_ascii=False, indent=4)
        else:
            allure_response = response
        return allure_response

    def extract_data(self, testcase_extract, response):
        """
        Extract a single parameter using regex or JSONPath
        :param testcase_extract: extract field in YAML
        :param response: API response string
        """
        pattern_lst = ['(.+?)', '(.*?)', r'(\d+)', r'(\d*)']
        try:
            for key, value in testcase_extract.items():
                # regex extraction
                for pat in pattern_lst:
                    if pat in value:
                        ext_list = re.search(value, response)
                        if pat in [r'(\d+)', r'(\d*)']:
                            extract_date = {key: int(ext_list.group(1))}
                        else:
                            extract_date = {key: ext_list.group(1)}
                        logs.info('Regex extracted: %s' % extract_date)
                        self.read.write_data(extract_date)

                # jsonpath extraction
                if "$" in value:
                    ext_json = jsonpath.jsonpath(json.loads(response), value)[0]
                    if ext_json:
                        extract_date = {key: ext_json}
                    else:
                        extract_date = {key: "No data extracted, response may be empty"}
                    logs.info('JSONPath extracted: %s' % extract_date)
                    self.read.write_data(extract_date)
        except:
            logs.error('Extraction failed, please check extract expression in YAML!')

    def extract_data_list(self, testcase_extract_list, response):
        """
        Extract multiple parameters using regex or JSONPath
        :param testcase_extract_list: extract_list in YAML
        :param response: API response string
        """
        try:
            for key, value in testcase_extract_list.items():
                # regex list extraction
                if "(.+?)" in value or "(.*?)" in value:
                    ext_list = re.findall(value, response, re.S)
                    if ext_list:
                        extract_date = {key: ext_list}
                        logs.info('Regex extracted list: %s' % extract_date)
                        self.read.write_data(extract_date)

                # JSONPath list extraction
                if "$" in value:
                    ext_json = jsonpath.jsonpath(json.loads(response), value)
                    if ext_json:
                        extract_date = {key: ext_json}
                    else:
                        extract_date = {key: "No data extracted, response may be empty"}
                    logs.info('JSONPath extracted list: %s' % extract_date)
                    self.read.write_data(extract_date)
        except:
            logs.error('List extraction failed, check extract_list expression in YAML!')
