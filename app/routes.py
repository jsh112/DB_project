from flask import render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime, timedelta

db = 'library.db'

def init_routes(app):
    @app.route('/')
    def home():
        user_id = session.get('user_id')
        
        try:
            with sqlite3.connect(db) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 랜덤으로 도서 추천
                cursor.execute(
                    'SELECT author, title, ISBN, available_rent FROM Book  \
                    ORDER BY RANDOM() LIMIT 10'
                )
                recommended_books = cursor.fetchall()
                
            # 로그인 상태와 렌더링 하자.
            return render_template('home.html', recommended_books=recommended_books, user_id=user_id)
                
        except sqlite3.Error as e:
            print(f'DataBase error : {e}')        

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

                conn = sqlite3.connect(db)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                count_query = "SELECT COUNT(*) FROM Book WHERE title LIKE ?"
                cursor.execute(count_query, ('%' + query + '%',))
                total_results = cursor.fetchone()[0]
                total_pages = total_results // per_page

                offset = (page - 1) * per_page
                sql_query = "SELECT author, keyword, title, published_year, ISBN, Available_rent FROM Book WHERE title LIKE ? LIMIT ? OFFSET ?"
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
        
    # 로그인
    @app.route('/login/', methods=['GET', 'POST'])
    def login():
        # POST -> 서버의 리소스를 업데이트하는 경우
        if request.method == 'POST':
            _id = request.form.get('ID')
            password = request.form.get('password')
            
            try:
                with sqlite3.connect(db) as conn:
                    cursor = conn.cursor()
                    
                    # 받아온 ID와 pw가 db에 있는지 확인
                    cursor.execute('SELECT id, name FROM User WHERE id = ? AND password = ?', (_id, password))
                    user = cursor.fetchone()
                    
                if user:
                    # 사용자 ID를 session에 저장
                    session['user_id'] = user[0]
                    session['name'] = user[1]
                    # url_for -> 함수 이름을 사용하자.
                    return redirect(url_for('home'))
                else:
                    return render_template('login.html', error="ID와 비밀번호를 다시 입력해 주세요.")
            except sqlite3.Error as e:
                print(f'Database error : {e}')
        return render_template('login.html')
    
    # 로그아웃
    @app.route('/logout/', methods=['POST'])
    def logout():
        session.clear()
        return '', 204
    
    # 회원가입 기능
    @app.route('/signup/', methods=['GET', 'POST'])
    def signup():
        # html에 있는 박스칸에 작성한 데이터를 가져옴
        if request.method == 'POST':
            _id = request.form['ID']
            password = request.form['password']
            name = request.form['name']
            email = request.form['email']
            
            try:
                conn = sqlite3.connect(db)
                cursor = conn.cursor
                
                # 회원가입 한 정보를 쿼리에 넣어야함
                cursor.execute(
                    "INSERT INTO User \
                    (id, password, name, email, avaiable, overdue_count) \
                    VALUES (?, ?, ?, ?, ?, ?)", (_id, password, name, email, 1, 0)
                )
                
                conn.commit()
            except sqlite3.Error as e:
                print(f'DataBase error : {e}')
                return e

            finally:
                conn.close()
                
            return redirect(url_for('login'))
        
        return render_template('signup.html')

    # 내 정보 보는 dashboard 기능 생성
    @app.route('/dashboard/', methods=['GET'])
    def dashboard():
        user_id = session.get('user_id')
        
        # 로그인하지 않은 경우
        if not user_id:
            return render_template(url_for('login'))
        
        try:
            with sqlite3.connect(db) as conn:
                conn.row_factory = sqlite3.Row  # 결과를 dict 형태로 반환
                cursor = conn.cursor()
                
                # 대출한 책 정보 가져오기
                cursor.execute("""
    SELECT Rental.RentalID, Book.title, Rental.RentalDate, Rental.DueDate
    FROM Rental
    JOIN Book ON Rental.Rent_ISBN = Book.ISBN
    WHERE Rental.User_id = ?;
""", (user_id,))

                rentals = cursor.fetchall()
                
            return render_template('dashboard.html', rentals=rentals, user_id=user_id)
                
        except sqlite3.Error as e:
            print(f'Database error : {e}')
            return e
        
    # 책 대출 기능
    @app.route('/borrow/<isbn>', methods=['POST'])
    def borrow(isbn):
        user_id = session.get('user_id')
        
        if not user_id:
            return redirect(url_for('login'))

        # 대출 날짜와 기한 계산
        rentdate = datetime.now()
        duedate = (rentdate + timedelta(days=1)).strftime('%Y-%m-%d')
        rentdate = rentdate.strftime('%Y-%m-%d')

        
        try:
            # 1단계 : 책의 대출 가능 상태를 업데이트
            with sqlite3.connect(db) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE Book SET available_rent = 0
                    WHERE ISBN = ?
                """, (isbn,))
                conn.commit() # 첫번째 단계 종료,
                
            # 2단계: 대출 정보를 기록
            with sqlite3.connect(db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(RentalID) FROM Rental")
                max_rental_id = cursor.fetchone()[0]
                rent_idx = max_rental_id + 1 if max_rental_id else 1

                cursor.execute("""
                    INSERT INTO Rental (RentalID, RentalDate, Rent_ISBN, User_ID, DueDate) 
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (rent_idx, rentdate, isbn, user_id, duedate)
                    )
                conn.commit()  # 두 번째 트랜잭션 종료
            
            return redirect(url_for('home'))
            
        except sqlite3.Error as e:
            print(f'Database error : {e}')
            return e
    
    # 책 반납 기능
    @app.route('/return/<rent_id>', methods=['POST'])
    def return_book(rent_id):
        try:
            with sqlite3.connect(db) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM Rental WHERE Rental.RentalID = ?
                """, (rent_id,))
                
                conn.commit()
                
            return redirect(url_for('dashboard'))
    
        except sqlite3.Error as e:
            print(f'Database error : {e}')
            return str(e), 500