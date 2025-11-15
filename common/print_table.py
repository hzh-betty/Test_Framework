from tabulate import tabulate
def print_table(two_dimension_list):
    """Print a two-dimensional list as a formatted table."""
    if not two_dimension_list:
        return

    headers = two_dimension_list[0]

    rows = [
        row for row in two_dimension_list[1:]
        if any(str(cell).strip() for cell in row)
    ]

    print(tabulate(rows, headers=headers, tablefmt="grid", stralign="center"))

if __name__ == "__main__":
    test_list = [
        ['id', 'vehicle_no', 'color', 'address'],
        ["", "", "", ""],
        ['1116016058541708528', '你', 'green', 'beijing'],
        ['1146003998720578844', '好', 'red', 'chengdu'],
        ['1148015232542564762', '好', 'blue', 'guangzhou'],
        ["", "", "", ""]
    ]
    print_table(test_list)
