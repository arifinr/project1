import csv
from sqlalchemy import create_engine

engine = create_engine('postgresql://arifin:saybacorp@localhost:62310/mydatabase')
with open('books.csv', newline='') as csvfile:
    bookreader = csv.reader(csvfile, delimiter=',', quotechar='|')
    line_count = 0
    for row in bookreader:
        if line_count==0:
            print(f'Column names are {", ".join(row)}')
        line_count += 1
    print(f"{line_count} lines")
