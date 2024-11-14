import pandas as pd
import sqlite3
import re
from flask import Flask, jsonify, render_template
from book_rental_system import LibraryDatabase

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == "__main__":
    # First, create tables and load data from the CSV file
    
    LibraryDatabase(db_name="library.db", csv_file="library.csv")
    
    app.run(debug=True)
