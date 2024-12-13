from flask import render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime, timedelta

db = 'library.db'

def get_dates():
    rentdate = datetime.now()
    duedate = rentdate + timedelta(days=1)
    return rentdate.strftime("%Y-%m-%d"), duedate.strftime('%Y-%m-%d')

def init_routes(app):
    @app.route('/')
    def home():
        user_id = session.get('user_id')
        
        try:
            with sqlite3.connect(db) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 랜덤으로 도서 추천
                cursor.execute("""
                    SELECT author, title, ISBN, available_rent
                    FROM Book
                    WHERE available_rent = 1  
                    ORDER BY RANDOM() LIMIT 10
                """)
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
                    
                    # 로그인 때마다 연체 여부를 갱신하자.
                    today, _ = get_dates()
                    query = """
                        SELECT User_ID
                        FROM Rental
                        WHERE (DATE(DueDate) < DATE(?) OR (SELECT COUNT(*) FROM Rental WHERE User_ID = ?) >= 3)
                        AND User_ID = ?;
                    """
                    cursor.execute(query, (today, _id,_id))
                    result = cursor.fetchall()
                    
                    # query가 없으면 [] 반환 -> if not으로 확인
                    # 쿼리가 없다(연체가 없다) -> 1 반환
                    # 쿼리가 있다 -> 0 반환
                    available_status = 1 if not result else 0
                    # 연체한 경우
                    if not available_status:
                        # 최대 연체일을 User Table에 업데이트
                        overdue_query = """
                            UPDATE User
                            SET overdue_count = (
                                SELECT 
                                    COALESCE(MAX(JULIANDAY(?) - JULIANDAY(DueDate)), 0)
                                FROM Rental
                                WHERE User_ID = ?
                                AND JULIANDAY(DueDate) < JULIANDAY(?)
                            )
                            WHERE id = ?;
                        """
                        cursor.execute(overdue_query, (today, user[0], today, user[0]))
                    
                        
                    cursor.execute("""
                        UPDATE User
                        SET available = ?
                        WHERE id = ?;
                    """, (available_status, user[0]))
                        
                    conn.commit()
                    
                    # url_for -> 함수 이름을 사용하자.
                    return redirect(url_for('home'))
                
                else:
                    return render_template('login.html', error="ID와 비밀번호를 다시 입력해 주세요.")
            except sqlite3.Error as e:
                conn.rollback()
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
                cursor = conn.cursor()
                
                # 회원가입 한 정보를 쿼리에 넣어야함
                cursor.execute("""
                    INSERT INTO User
                    (id, password, name, email, available, overdue_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (_id, password, name, email, 1, 0))
                
                conn.commit()
            except sqlite3.Error as e:
                print(f'DataBase error : {e}')
                return e
                
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
                
                # html에 연체인 경우를 다르게 띄워주기 위해서
                cursor.execute("""
                    SELECT available
                    FROM User
                    WHERE id = ?;
                """, (user_id,))
                
                avail = cursor.fetchone()[0]
                
                # 대출한 책 정보 가져오기
                cursor.execute("""
                    SELECT Rental.RentalID, Book.title, Rental.RentalDate, Rental.DueDate
                    FROM Rental
                    JOIN Book ON Rental.Rent_ISBN = Book.ISBN
                    WHERE Rental.User_id = ?;
                """, (user_id,))

                rentals = cursor.fetchall()
                
                # 대시보드에서 로그인한 사람 정보 출력
                cursor.execute(""" 
                    SELECT name
                    FROM User
                    WHERE id = ?
                """, (user_id,))
                
                user_name = cursor.fetchone()[0]
                
                # 연체일 계산
                rental_data = []
                for rental in rentals:
                    due_date = rental['DueDate']
                    due_date = datetime.strptime(due_date, '%Y-%m-%d')
                    
                    rent_date = rental['RentalDate']
                    rent_date = datetime.strptime(rent_date, '%Y-%m-%d')
                    overdue_days = (datetime.now() - due_date).days if datetime.now() > due_date else 0
                    rental_data.append({
                        'RentalID' : rental['RentalID'],
                        'title' : rental['title'],
                        'RentalDate' : rent_date.strftime('%Y-%m-%d'),
                        'DueDate' : due_date.strftime('%Y-%m-%d'),
                        'overdue_days' : overdue_days
                    })
                
                # 대출한 책 개수 확인
                cursor.execute("""
                    SELECT COUNT(*) FROM Rental WHERE User_ID = ?;
                """, (user_id,))
                borrowed_count = cursor.fetchone()[0]

                # 대출 가능한 권수 계산
                max_allowed = 3
                remaining_borrow = max(0, max_allowed - borrowed_count)
                
            return render_template(
                'dashboard.html', 
                rentals=rental_data, 
                user_id=user_id,
                available=avail,
                user_name = user_name,
                remaining_borrow=remaining_borrow)
                
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
        rentdate, duedate = get_dates()
        
        try:
            with sqlite3.connect(db) as conn:
                cursor = conn.cursor()
            
                # 1단계: 대출 권수 확인
                cursor.execute("""
                    SELECT COUNT(*) FROM Rental WHERE User_ID = ?;
                """, (user_id,))
                borrow_cnt = cursor.fetchone()[0]
                
                # 2단계 : available 확인
                
                cursor.execute("""
                    SELECT available
                    FROM User
                    WHERE id = ?
                """, (user_id,))
                
                can_rent = cursor.fetchone()[0]
                not_available = 1 if not can_rent else 0
                
                if borrow_cnt >= 3:
                    return f"""
                    <script>
                        alert("최대 대출권수 3권을 초과할 수 없습니다.\\n책을 반납해주신 후 다시 대출해 주세요.");
                        window.location.href = "{request.referrer}";
                    </script>
                    """
                    
                if not_available:
                    return f"""
                    <script>
                        alert("현재 연체중입니다.");
                        window.location.href = "{request.referrer}";
                    </script>
                    """
                
                query = """ 
                    UPDATE User
                    SET available = CASE
                        WHEN (
                            (SELECT COUNT(*) FROM Rental WHERE User_ID = ?) >= 2
                            OR
                            (SELECT COUNT(*) FROM Rental WHERE User_ID = ? AND JULIANDAY(DueDate) < JULIANDAY(?)) > 0
                        ) THEN 0
                        ELSE 1
                    END
                    WHERE id = ?;
                """
                
                cursor.execute(query, (user_id, user_id, rentdate, user_id))
                
                conn.commit()
                
                # 3단계: 책 대출 가능 상태 업데이트
                cursor.execute("""
                    UPDATE Book SET available_rent = 0 WHERE ISBN = ?;
                """, (isbn,))
                
                conn.commit()
                
                # 4단계: 대출 정보 삽입
                cursor.execute("SELECT MAX(RentalID) FROM Rental;")
                max_rental_id = cursor.fetchone()[0]
                rent_idx = max_rental_id + 1 if max_rental_id else 1

                cursor.execute("""
                    INSERT INTO Rental (RentalID, RentalDate, Rent_ISBN, User_ID, DueDate) 
                    VALUES (?, ?, ?, ?, ?);
                """, (rent_idx, rentdate, isbn, user_id, duedate))
                
                conn.commit()
                
                
            return redirect(url_for('home'))
            
        except sqlite3.Error as e:
            print(f'Database error : {e}')
            conn.rollback()
            return e
    
    # 책 반납 기능
    @app.route('/return/<rent_id>', methods=['POST'])
    def return_book(rent_id):
        user_id = session.get('user_id')
        
        try:
            with sqlite3.connect(db) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT Rent_ISBN FROM Rental WHERE RentalID = ?;
                """, (rent_id,))
                isbn = cursor.fetchone()
                isbn = isbn[0]
                
                # 대출 기록 삭제
                cursor.execute("""
                    DELETE FROM Rental WHERE RentalID = ?;
                """, (rent_id,))
                
                cursor.execute("""
                    UPDATE Book SET Available_rent = 1 WHERE ISBN = ?;
                """, (isbn,))

                # 대출 기록 남아 있는지 확인 후 사용자 상태 업데이트
                cursor.execute("""
                    SELECT COUNT(*) FROM Rental WHERE User_ID = ?;
                """, (user_id,))
                remaining_rentals = cursor.fetchone()[0]

                if remaining_rentals != 0:
                    cursor.execute("""
                        UPDATE User SET available = 1 WHERE id = ?;
                    """, (user_id,))

                
                conn.commit()
            return redirect(url_for('dashboard'))

    
        except sqlite3.Error as e:
            print(f'Database error : {e}')
            # 실패 시 rollback
            conn.rollback()
            return str(e), 500
        
    # 회원탈퇴 기능
    """ 
        만약 연체된 기록이 있거나 현재 책을 대출중이라면 회원탈퇴가 불가능.
        책을 빌린 흔적이 없다면 User Table에서 삭제시킨다.
    """
    @app.route('/withdraw', methods=['POST'])
    def withdraw_account():
        
        user_id = session.get('user_id')
        # print(f'{user_id}')
        try:
            with sqlite3.connect(db) as conn:
                cursor = conn.cursor()
                """
                    1. 책을 빌린 사람
                    2. 연체된 사람
                    -> COUNT가 0이 아니면 탈퇴 불가능
                """
                today, _ = get_dates()
                query = """
                    SELECT COUNT(*)
                    FROM Rental
                    WHERE User_ID = ?
                    AND (
                        JULIANDAY(DueDate) < JULIANDAY(?, 'localtime') -- 연체 상태
                        OR JULIANDAY(DueDate) >= JULIANDAY(?, 'localtime') -- 책을 빌린 상태 (반납 기한이 지나지 않음)
                    );
                """
                cursor.execute(query, (user_id, today, today))
                not_withdraw = cursor.fetchone()[0]
                # print(f'{not_withdraw}')
                
                # 탈퇴 불가능한 상태
                if not_withdraw != 0:
                    return f"""
                    <script>
                        alert("탈퇴가 불가능합니다.");
                        window.location.href = "{url_for('home')}";
                    </script>
                    """
                else:
                    cursor.execute("""
                        DELETE FROM User WHERE id = ?
                    """, (user_id,))
                    conn.commit()
                
                    # 세션 초기화
                    session.clear()
                    return f"""
                    <script>
                        alert("회원탈퇴가 성공적으로 완료되었습니다.");
                        window.location.href = "{url_for('home')}";
                    </script>
                    """
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            
    @app.route('/reservation/<isbn>', methods=['GET', 'POST'])
    # hi
    def reservation(isbn):
        pass
    
    
