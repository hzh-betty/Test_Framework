import yaml
import os
from record_log import logs
from conf.setting import FILE_PATH
from conf.operator_config import OperatorConfig

class OperatorYaml:
    def __init__(self, file_path=None):
        # 1. Determine the YAML file path
        if file_path is None:
            self.__file_path = FILE_PATH['YAML']
        else:
            self.__file_path = file_path

        # 2. Load the YAML file
        try:
            with open(self.__file_path, 'r', encoding='utf-8') as file:
                self.__data = yaml.safe_load(file)
            logs.debug(f"YAML file {self.__file_path} successfully loaded")
        except Exception as e:
            logs.error(f"Error loading YAML file {self.__file_path}: {e}")
            self.__data = None

        self.__conf = OperatorConfig()

    def get_data(self):
        """Get the entire data from the YAML file"""
        return self.__data

    def get_value(self, key_path):
        """Get a value from the YAML data using a list of keys representing the path"""
        if self.__data is None:
            logs.error(f"YAML file {self.__file_path} has not been loaded")
            return None

        data = self.__data
        try:
            for key in key_path:
                data = data[key]
            logs.debug(f"YAML file {self.__file_path} data successfully loaded")
            return data
        except KeyError:
            logs.error(f'Key path {key_path} not found in YAML data')
            return None
    def write_data(self, data):
        """Write data to the YAML file"""
        if not isinstance(data, dict):
            logs.error(f"Data type {type(data)} not supported")
            return
        try:
            with open(self.__file_path, 'w', encoding='utf-8') as file:
                yaml.safe_dump(data, file, allow_unicode=True,sort_keys=False)
            logs.debug(f"YAML file {self.__file_path} successfully written")
        except Exception as e:
            logs.error(f"Error writing to YAML file {self.__file_path}: {e}")
    def clear_data(self):
        """Clear all data in the YAML file"""
        try:
            with open(self.__file_path, 'w', encoding='utf-8') as file:
                file.truncate()
            logs.debug(f"YAML file {self.__file_path} successfully cleared")
        except Exception as e:
            logs.error(f"Error clearing YAML file {self.__file_path}: {e}")

    def get_extract_yaml(self, node_name, second_node_name=None):
        if os.path.exists(FILE_PATH['EXTRACT']):
            pass
        else:
            logs.error(f'extract.yaml not found at {FILE_PATH["EXTRACT"]}')
        try:
                if second_node_name is None:
                    return self.__data[node_name]
                else:
                    return self.__data[node_name][second_node_name]
        except Exception as e:
                logs.error(f'Error retrieving data from extract.yaml: {e}')
                return None

if '__main__' == __name__:
    oy = OperatorYaml()
    data = oy.get_data()
    print(data)
    value = oy.get_value(['goodsIds'])
    print(value)