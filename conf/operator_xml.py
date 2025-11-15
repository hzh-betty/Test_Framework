import os.path
import xml.etree.ElementTree as et
import setting
from common.record_log import logs


def get_sub_element_text(parent_element, sub_element_tag):
    """Get the text content of a sub-element"""
    if parent_element is None:
        logs.error('Parent element is None, cannot get sub-element text')
        return None
    sub_element = parent_element.find(sub_element_tag)
    if sub_element is not None:
        text = sub_element.text
        logs.debug(f'Sub-element "{sub_element_tag}" text: {text}')
        return text
    else:
        logs.error(f'Sub-element "{sub_element_tag}" not found')
        return None


class OperatorXml:
    def __init__(self, file_path=None):
        # 1. Determine the XML file path
        if file_path is None:
            logs.error("file_path is None")
            return
        else:
            self.__file_path = file_path

        # 2. Parse the XML file
        try:
            self.__tree = et.parse(self.__file_path)
            self.__root = self.__tree.getroot()
            logs.debug(f'XML file {self.__file_path} successfully parsed')
        except et.ParseError as e:
            logs.error(f'Error parsing XML file {self.__file_path}: {e}')
            self.__tree = None
            self.__root = None

    def get_elements_by_tag(self, tag_name):
        """Get all elements with the specified tag name"""
        if self.__root is None:
            logs.error('XML root is None, cannot get elements')
            return []
        elements = self.__root.findall(tag_name)
        logs.debug(f'Found {len(elements)} elements with tag name "{tag_name}"')
        return elements

    @staticmethod
    def get_element_attribute(element, attribute_name):
        """Get the value of the specified attribute from an element"""
        if element is None:
            logs.error('Element is None, cannot get attribute')
            return None
        value = element.get(attribute_name)
        logs.debug(f'Element attribute "{attribute_name}" value: {value}')
        return value


if '__main__' == __name__:
    xml_operator = OperatorXml(os.path.join(setting.ROOT_DIR, "envir.xml"))
    elements = xml_operator.get_elements_by_tag('parameter')
    for elem in elements:
        name = get_sub_element_text(elem, 'key')
        value = get_sub_element_text(elem, 'value')
        print(f'Parameter name: {name}, value: {value}')
