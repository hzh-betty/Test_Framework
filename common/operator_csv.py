import pandas as pd
from common.record_log import logs
from conf import setting
class OperatorCsv:
    """Class for handling CSV file operations."""

    def __init__(self, file_path = None,head=None):
        if file_path is None:
            self.__file_path = setting.FILE_PATH['CSV']
        else:
            self.__file_path = file_path
        try:
            self.__data_frame = pd.read_csv(self.__file_path,header=head)
            logs.debug(f'CSV file {self.__file_path} successfully loaded')
        except Exception as e:
            logs.error(f'Error loading CSV file {self.__file_path}: {e}')
            self.__data_frame = None

    def get_rows(self):
        """Get the number of rows in the CSV file."""
        if self.__data_frame is not None:
            return len(self.__data_frame)
        logs.error('Data frame is None, cannot get rows')
        return 0

    def get_cols(self):
        """Get the number of columns in the CSV file."""
        if self.__data_frame is not None:
            return len(self.__data_frame.columns)
        logs.error('Data frame is None, cannot get columns')
        return 0

    def get_cell_value(self, row, col):
        """Get the value of a specific cell."""
        if self.__data_frame is not None:
            try:
                return self.__data_frame.iat[row - 1, col - 1]
            except IndexError:
                logs.error(f'Index out of range: row {row}, col {col}')
                return None
        logs.error('Data frame is None, cannot get cell value')
        return None

    def get_each_line(self, row):
        """Get entire row as a list."""
        if self.__data_frame is not None:
            try:
                return self.__data_frame.iloc[row - 1].tolist()
            except IndexError:
                logs.error(f'Index out of range: row {row}')
                return []
        logs.error('Data frame is None, cannot get row')
        return []

    def get_each_column(self, col):
        """Get entire column as a list."""
        if self.__data_frame is not None:
            try:
                return self.__data_frame.iloc[:, col - 1].tolist()
            except IndexError:
                logs.error(f'Index out of range: col {col}')
                return []
        logs.error('Data frame is None, cannot get column')
        return []

    def get_each_column_by_name(self, col_name):
        """Get entire column by name as a list."""
        if self.__data_frame is not None:
            if col_name in self.__data_frame.columns:
                return self.__data_frame[col_name].tolist()
            else:
                logs.error(f'Column name "{col_name}" not found')
                return []
        logs.error('Data frame is None, cannot get column by name')
        return []
if __name__ == "__main__":
    csv_operator = OperatorCsv()
    print(csv_operator.get_cell_value(1, 2))
    print(csv_operator.get_each_line(1))
    print(csv_operator.get_each_column(1))