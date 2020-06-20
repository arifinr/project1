import csv
import json
import os
import psycopg2

def create_table(cur):
    '''Create a books and reviews table'''
    create = (
        """CREATE TABLE books (
            isbn CHAR(10) PRIMARY KEY,
            title VARCHAR,
            author_names TEXT ARRAY,
            year SMALLINT
        )
        """,
        """CREATE TABLE reviews (
            id SERIAL PRIMARY KEY,
            reviewer CHAR(20) REFERENCES users(username),
            isbn CHAR(10) REFERENCES books(isbn),
            rating SMALLINT,
            review TEXT
        )
        """,
    )

    # Create table one by one
    for command in create:
        cur.execute(command)


def insert_or_update(cur, row):
    '''For each row of file, insert or update database'''
    # Format syntax data syntax to allow legal insert
    isbn = row[0]
    title = row[1].replace("'", "''")
    # split authors on commas, replace with escape characters, strip quotations
    authors = json.dumps(row[2].split(", ")).replace("'", "''")[1:-1]
    year = row[3]

    book_insert = "INSERT INTO books (isbn, title, author_names, year) " \
        f"VALUES('{isbn}', '{title}', '{{{authors}}}', {year})"
    # print("\n", book_insert)
    print("Inserting", title)
    cur.execute(book_insert)


def read_file(cur):
    '''Read file row by row and insert into database'''
    with open('books.csv', newline='') as csvfile:
        bookreader = csv.reader(csvfile)
        line_count = 0
        for row in bookreader:
            if line_count>0:
                insert_or_update(cur, row)
            line_count += 1


def main():
    '''Connecting to the PostgreSQL database'''
    try:
        # Local database
        # conn = psycopg2.connect(user = "postgres",
        #                         password = "saybacorp",
        #                         host = "localhost",
        #                         port = "5432",
        #                         database = "postgres")

        # Heroku database
        DATABASE_URL = os.environ['DATABASE_URL']

        print('Connecting to the PostgreSQL database')
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                            
        # Create a cursor and tables
        cur = conn.cursor()
        create_table(cur)
        
        read_file(cur)

        # Commiting transactions to database
        conn.commit()
    except (Exception, psycopg2.Error) as error :
        print (error)
    finally:
        if conn is not None:
            # Close the communication with the PostgreSQL
            cur.close()
            conn.close()
        print('Database connection closed.')


if __name__ == "__main__":
    # Execute only if run as a script
    main()