from flask import render_template, request, redirect, url_for, abort, session
import sqlite3



def init_routes(app):
    @app.route('/')
    def home():
        try:
            conn = sqlite3.connect('library.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT author, title, ISBN, available_rent FROM Book LIMIT 10")
            recommended_books = cursor.fetchall()

        except sqlite3.Error as e:
            recommended_books = []
            print(f"Database error: {e}")
        finally:
            conn.close()

        return render_template('home.html', recommended_books=recommended_books)

    @app.route('/search/', methods=['GET', 'POST'])
    def search():
        error = None
        books = []
        query = ''
        page = request.args.get('page', 1, type=int)
        per_page = 50

        if request.method == 'POST':
            query = request.form.get('query', '').strip()
            return redirect(url_for('search', query=query, page=1))

        elif request.method == 'GET':
            query = request.args.get('query', '').strip()

            if not query:
                error = "검색어를 입력하세요."
                return render_template('search.html', error=error, books=books, query=query, page=page, per_page=per_page, total_pages=0)

            try:

                conn = sqlite3.connect('library.db')
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                count_query = "SELECT COUNT(*) FROM Book WHERE title LIKE ?"
                cursor.execute(count_query, ('%' + query + '%',))
                total_results = cursor.fetchone()[0]
                total_pages = total_results // per_page

                offset = (page - 1) * per_page
                sql_query = "SELECT author, keyword, title, published_year, ISBN FROM Book WHERE title LIKE ? LIMIT ? OFFSET ?"
                cursor.execute(
                    sql_query, ('%' + query + '%', per_page, offset))
                books = cursor.fetchall()

            except sqlite3.Error as e:
                error = f"데이터베이스 오류: {e}"
                books = []
                total_pages = 0
            finally:
                conn.close()

            return render_template('search.html', books=books, query=query, error=error, page=page, per_page=per_page, total_pages=total_pages)
        
    @app.route('/login/')
    def login():
        pass

    # 대출 라우트
    @app.route('/rent/<isbn>', methods=['POST'])
    def rent_book(isbn):
        # 사용자 로그인 체크
        user_id = session.get('user_id')  # 세션에서 유저 아이디 가져오기
        if not user_id:
            return "User not logged in", 401
        try:
            conn = sqlite3.connect('library.db')
            cursor = conn.cursor()

            # Check if the book is available
            cursor.execute("SELECT available_rent FROM Book WHERE ISBN = ?", (isbn,))
            result = cursor.fetchone()
            if result and result[0] == 0:
                return "This book is not available for rent.", 400

            # Update Book availability
            cursor.execute("UPDATE Book SET available_rent = 0 WHERE ISBN = ?", (isbn,))

            # Insert into Rental
            user_id = session.get('user_id')  # Use session for the logged-in user ID
            if not user_id:
                return "User not logged in", 401

            rental_date = "2024-11-30"  # Use datetime.now() for the current date
            due_date = "2024-12-07"  # Example: 7 days from rental_date
            cursor.execute('''
                INSERT INTO Rental (RentalDate, Status, Rent_ISBN, User_ID, DueDate)
                VALUES (?, ?, ?, ?, ?)
            ''', (rental_date, "Rented", isbn, user_id, due_date))

            conn.commit()
            return "Book rented successfully!", 200

        except sqlite3.Error as e:
            return f"Database error: {e}", 500
        finally:
            conn.close()


   