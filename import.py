import csv
import json
import psycopg2

commands = (
    """CREATE TABLE books (
        isbn CHAR(10) PRIMARY KEY,
        title VARCHAR,
        author_names text ARRAY,
        year INTEGER
    )
    """,
    """CREATE TABLE authors (
        author_name text PRIMARY KEY,
        isbn_books CHAR(10) ARRAY
    )
    """
)

try:
    # Connecting to the PostgreSQL database
    conn = psycopg2.connect(user = "postgres",
                            password = "saybacorp",
                            host = "localhost",
                            port = "5432",
                            database = "postgres")
                        
    # Create a cursor
    cur = conn.cursor()

    # Create table one by one
    for command in commands:
        cur.execute(command)
    
    # Read file row by row and insert into database
    with open('books.csv', newline='') as csvfile:
        bookreader = csv.reader(csvfile)
        line_count = 0
        for row in bookreader:
            if line_count>0:
                # Format syntax data syntax to allow legal insert
                isbn = row[0]
                title = row[1].replace("'", "''")
                # split authors on commas, replace with escape characters, strip quotations
                authors = json.dumps(row[2].split(", ")).replace("'", "''")[1:-1]
                year = row[3]

                book_insert = "INSERT INTO books (isbn, title, author_names, year) " \
                    f"VALUES('{isbn}', '{title}', '{{{authors}}}', {year})"
                # print("\n", book_insert)
                cur.execute(book_insert)
                
                authors_list = row[2].split(", ")
                for auth in authors_list:
                    auth = auth.replace("'", "''")
                    auth_insert = f"INSERT INTO authors (author_name, isbn_books) " \
                        f"VALUES ('{auth}', '{{\"{isbn}\"}}') ON CONFLICT(author_name) " \
                        f"DO UPDATE SET isbn_books = array_append(authors.isbn_books, '{isbn}')"
                    # print(auth_insert)
                    cur.execute(auth_insert)

            line_count += 1
    
    cur.execute("SELECT * FROM authors")
    for table in cur.fetchall():
        print(table)
    
    # Close the communication with the PostgreSQL
    cur.close()
except (Exception, psycopg2.Error) as error :
    print (error)
finally:
    if conn is not None:
        conn.close()
    print('Database connection closed.')