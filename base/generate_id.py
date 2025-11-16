def generate_module_id():
    """
    Generate sequential module IDs to keep Allure report order
    consistent with the execution order in pytest.
    """
    for i in range(1, 1000):
        module_id = 'M' + str(i).zfill(2) + '_'
        yield module_id


def generate_testcase_id():
    """
    Generate sequential test case IDs.
    """
    for i in range(1, 10000):
        case_id = 'C' + str(i).zfill(2) + '_'
        yield case_id


m_id = generate_module_id()
c_id = generate_testcase_id()
