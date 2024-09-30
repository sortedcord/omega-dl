import unicodedata
import re
import zipfile
import os

def list_files_abs(directory):
    """
    List all files in the given directory with their absolute paths.
    
    :param directory: The directory to list files from
    :return: A list of absolute file paths
    """
    file_list = []
    
    # Convert to absolute path if it's not already
    directory = os.path.abspath(directory)
    
    # Walk through the directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Create absolute file path
            file_path = os.path.join(root, file)
            file_list.append(file_path)
    
    return file_list


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def zip_files(file_paths, output_zip_file):
    """
    Zip the given files into a single zip file.
    
    :param file_paths: List of file paths to be zipped
    :param output_zip_file: Name of the output zip file
    """
    with zipfile.ZipFile(output_zip_file, 'w') as zipf:
        for file in file_paths:
            if os.path.isfile(file):
                zipf.write(file, os.path.basename(file))
            else:
                print(f"Warning: {file} not found or is not a file. Skipping.")
