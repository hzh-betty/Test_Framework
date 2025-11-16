import os
import shutil
from common.record_log import logs


def remove_files(directory: str, extensions: list):
    """
    Remove files in a directory based on file extensions.

    :param directory: Target directory path
    :param extensions: Extensions to delete, e.g. ['json', 'txt', 'attach']
    """
    try:
        # Ensure the path exists; create it if missing
        if not os.path.exists(directory):
            os.makedirs(directory)
            return

        # Validate input type
        if not isinstance(extensions, list):
            raise TypeError("Parameter 'extensions' must be a list")

        # List all items in the directory
        for file_name in os.listdir(directory):
            file_path = os.path.join(directory, file_name)

            # Skip directories
            if not os.path.isfile(file_path):
                continue

            # Delete files that match the target extensions
            for ext in extensions:
                if file_name.endswith(ext):
                    os.remove(file_path)

    except Exception as e:
        logs.error(f"Error removing files: {e}")


def remove_directory(path: str):
    """
    Remove an entire directory.

    :param path: Directory path to remove
    """
    try:
        if os.path.exists(path):
            # Use rmtree to remove a directory and its contents
            shutil.rmtree(path)
    except Exception as e:
        logs.error(f"Error removing directory: {e}")
