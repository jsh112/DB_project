import pandas as pd
import sqlite3
import re


class LibraryDatabase:
    def __init__(self, db_name="library.db", csv_file="library.csv"):
        '''
        Initialize the LibraryDatabase with the database name and CSV file.
        Connects to SQLite and creates the Book table if it doesn't exist.
        Loads data from CSV if the table is empty.
        '''
        self.db_name = db_name
        self.csv_file = csv_file
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

        with self.conn:
            # Book Table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS Book (
                    author TEXT NOT NULL,
                    keyword TEXT,
                    title TEXT NOT NULL,
                    published_year INTEGER NOT NULL,
                    ISBN TEXT PRIMARY KEY,
                    Available_rent INT DEFAULT 1,
                    penalty_date TEXT
                );
            ''')

            # User Table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS User(
                    id TEXT NOT NULL PRIMARY KEY,
                    password TEXT,
                    name TEXT,
                    email TEXT,
                    available INTEGER DEFAULT 1,
                    overdue_count INTEGER DEFAULT 0
                );
            ''')

            # Rental Table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS Rental(
                    RentalID INTEGER PRIMARY KEY AUTOINCREMENT,
                    RentalDate TEXT,
                    Rent_ISBN TEXT NOT NULL,
                    User_ID TEXT NOT NULL,
                    DueDate TEXT NOT NULL,
                    FOREIGN KEY (Rent_ISBN) REFERENCES Book(ISBN),
                    FOREIGN KEY (User_ID) REFERENCES User(id)
                );
            ''')

            # Review Table
            
            self.cursor.execute(''' 
                CREATE TABLE IF NOT EXISTS Review(
                    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    isbn TEXT,
                    rating REAL CHECK(rating >= 1 AND rating <= 5),
                    comment TEXT,
                    create_date TEXT,
                    anonymous_name TEXT,
                    FOREIGN KEY (user_id) REFERENCES User(id),
                    FOREIGN KEY (isbn) REFERENCES Book(ISBN)
                );
            ''')

        # Check if the Book table is populated
        if not self.is_table_populated():
            self.load_data()
        else:
            print("Data already exists in the Book table. Skipping CSV load.")

    def is_table_populated(self):
        '''
        Check if the Book table already has data.
        Returns True if there are records in the table, False otherwise.
        '''
        self.cursor.execute("SELECT COUNT(*) FROM Book")
        count = self.cursor.fetchone()[0]
        return count > 0

    def load_data(self):
        '''
        Load data from the CSV file and insert it into the Book table.
        Preprocesses data by removing non-numeric characters from numeric fields.
        '''
        try:
            # Read CSV data
            df = pd.read_csv(self.csv_file)

            # Clean and preprocess data
            df['published_year'] = df['published_year'].apply(
                lambda x: int(re.sub(r'\D', '', str(x))) if pd.notnull(x) and re.sub(r'\D', '', str(x)) != '' else None)
            df['ISBN'] = df['ISBN'].apply(
                lambda x: re.sub(r'\D', '', str(x)) if pd.notnull(x) else None)

            # Insert data into the Book table
            for _, row in df.iterrows():
                self.cursor.execute('''
                    INSERT OR IGNORE INTO Book (author, keyword, title, published_year, ISBN, Available_rent)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (row['Authors'], row['Keyword'], row['Title'], row['published_year'], row['ISBN'], 1))

            self.conn.commit()
            print(f"Data loaded successfully from {self.csv_file}")

        except FileNotFoundError:
            print(f"Error: The file '{self.csv_file}' was not found.")
        except sqlite3.IntegrityError as e:
            print(f"Error inserting data: {e}")
        finally:
            # Close the database connection
            self.conn.close()
