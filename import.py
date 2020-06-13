import csv
import psycopg2

def read_and_insert_data():
    with open('books.csv', newline='') as csvfile:
        bookreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        line_count = 0
        for row in bookreader:
            if line_count>0:
                print(f'Column names are {", ".join(row)}')
            line_count += 1

def create_tables():
    commands = (
        """CREATE TABLE books (
            isbn INTEGER PRIMARY KEY,
            title VARCHAR,
            author_names VARCHAR ARRAY,
            year INTEGER
        )
        """,
        """CREATE TABLE authors (
            author_name VARCHAR PRIMARY KEY,
            isbn_books INTEGER ARRAY
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
        
        # Close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.Error) as error :
        print (error)
    finally:
        if conn is not None:
            conn.close()
        print('Database connection closed.')



if __name__ == '__main__':
    create_tables()