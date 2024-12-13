# app/__init__.py

from flask import Flask
from .routes import init_routes
from .book_rental_system import LibraryDatabase


def create_app():
    app = Flask(__name__)
    init_routes(app)
    app.secret_key = '1234567890'
    LibraryDatabase("library.db", "library.csv")

    return app
