import csv
import os
from resilient_importer.exceptions import EmptyFileError, InvalidCSVError
from resilient_importer.csv_parser import parse_csv_to_users


def main():
    print("welcome")
    filename=input("Enter CSV file name: ")
    
    try:
        users=parse_csv_to_users(filename)
        for u in users:
            print(u)
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except EmptyFileError as e:
        print(f"Error: {e}")
    except InvalidCSVError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")