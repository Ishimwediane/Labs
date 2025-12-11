import csv
import os
from resilient_importer.exceptions import EmptyFileError, InvalidCSVError



def read_csv_file(filename):
    """Read a CSV file and returns a list of dictionaries."""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File '{filename}' not found.")
    with open(filename, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        row=list(reader)
        
        if not row:
            raise EmptyFileError(f"File '{filename}' is empty.")
        return row
        


def main():
    print("welcome")
    filename=input("Enter CSV file name: ")
    
    try:
        data=read_csv_file(filename)
        print(data)
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except EmptyFileError as e:
        print(f"Error: {e}")
    except InvalidCSVError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")