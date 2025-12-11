import csv
import os

def main():
    print("welcome")
    filename=input("Enter CSV file name: ")
    
    if not os.path.exists(filename):
        print("File does not exist")
        return
    print("reading file")
    with open (filename,newline="",encoding="utf-8") as f:  #using newline not r for better getting dictionary format instead of simple text since our file is csv
        reader=csv.DictReader(f)
        for row in reader:
            print(row)
       
        
    