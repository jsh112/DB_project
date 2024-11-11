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

        # Create Book table
        with self.conn:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS Book (
                    author TEXT,
                    keyword TEXT,
                    title TEXT NOT NULL,
                    published_year INTEGER,
                    ISBN INTEGER PRIMARY KEY
                )
            ''')

        # Check if the Book table is populated
        if not self.is_table_populated():
            self.load_data_with_pandas()
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

    def load_data_with_pandas(self):
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
                lambda x: int(re.sub(r'\D', '', str(x))) if pd.notnull(x) and re.sub(r'\D', '', str(x)) != '' else None)

            # Insert data into the Book table
            for _, row in df.iterrows():
                self.cursor.execute('''
                    INSERT OR IGNORE INTO Book (author, keyword, title, published_year, ISBN)
                    VALUES (?, ?, ?, ?, ?)
                ''', (row['Authors'], row['Keyword'], row['Title'], row['published_year'], row['ISBN']))

            self.conn.commit()
            print(f"Data loaded successfully from {self.csv_file}")

        except FileNotFoundError:
            print(f"Error: The file '{self.csv_file}' was not found.")
        except sqlite3.IntegrityError as e:
            print(f"Error inserting data: {e}")
        finally:
            # Close the database connection
            self.conn.close()
