from flask import render_template, request, redirect, url_for, abort
import sqlite3


def init_routes(app):
    @app.route('/')
    def home():
        return render_template('home.html')

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
