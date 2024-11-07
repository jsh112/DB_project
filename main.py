import csv
import sqlite3
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# Function to create tables and load data


def MakeTable():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row  # To access columns by name
    cursor = conn.cursor()

    # Create User table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS User(
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            checkout_books INTEGER,
            overdue Boolean
        )
    ''')

    # Create Book table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Book(
            author TEXT,
            keyword TEXT,
            title TEXT NOT NULL,
            published_year INTEGER,
            ISBN INTEGER PRIMARY KEY
        )
    ''')

    # Load data from CSV file into the Book table
    csv_library = 'library.csv'

    try:
        with open(csv_library, 'r') as file:
            reader = csv.DictReader(file)

            # Insert each row into the Book table
            for row in reader:
                # Check if the row with the same ISBN already exiest
                cursor.execute(
                    "SELECT 1 FROM BOOK WHERE ISBN = ?", (row['ISBN'],))

                exists = cursor.fetchone()

                if not exists:
                    cursor.execute('''
                        INSERT OR IGNORE INTO Book (author, keyword, title, published_year, ISBN) 
                        VALUES (?, ?, ?, ?, ?)
                    ''', (row['Authors'], row['Keyword'], row['Title'], row['published_year'], row['ISBN']))

        print(f"Data loaded successfully from {csv_library}")

    except FileNotFoundError:
        print(f"Error: The file '{csv_library}' was not found.")
    except sqlite3.IntegrityError as e:
        print(f"Error inserting data: {e}")

    # Load data from CSV file into the User table

    conn.commit()
    conn.close()

# Function to print all rows in User and Book tables


def print_db():
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()

    # Print User Table
    print("User Table:")
    cursor.execute('SELECT * FROM User')
    users = cursor.fetchall()
    for user in users:
        print(user)

    # Print Book Table
    print("\nBook Table:")
    cursor.execute('SELECT * FROM Book LIMIT 500')
    books = cursor.fetchall()
    for book in books:
        print(book)

    conn.close()

# Flask route to retrieve Book data as JSON


@app.route('/books', methods=['GET'])
def get_books():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row  # Access columns by name
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Book LIMIT 500')
    rows = cursor.fetchall()

    # Convert rows to a list of dictionaries for JSON conversion
    books = [dict(row) for row in rows]

    conn.close()
    return jsonify(books)

@app.route('/')
def homepage():
    return render_template('home.html')


if __name__ == '__main__':
    # First, create tables and load data from the CSV file
    MakeTable()

    # Run the Flask app
    app.run(debug=True)
