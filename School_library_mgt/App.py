from flask import Flask, jsonify, redirect, request, render_template, url_for
import mysql.connector
from datetime import date, timedelta
import io
import csv
from datetime import date, timedelta
from flask import make_response, request, jsonify, flash, redirect, url_for

app = Flask(__name__)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',  # Replace with your MySQL username
    'password': 'Bloom123@fidey',  # Replace with your MySQL password
    'database': 'SchoolLibrary'
}

# Function to get a connection to the database
def get_db_connection():
    return mysql.connector.connect(**db_config)

# Function to create tables in the database if they don't exist
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Students (
            StudentID INT AUTO_INCREMENT PRIMARY KEY,
            FirstName VARCHAR(100),
            LastName VARCHAR(100),
            Email VARCHAR(100) UNIQUE,
            RegistrationNumber VARCHAR(50) UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Books (
            BookID INT AUTO_INCREMENT PRIMARY KEY,
            Title VARCHAR(255),
            Author VARCHAR(255),
            Genre VARCHAR(100),
            PublishedYear INT,
            Quantity INT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS borrowed_books (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_name VARCHAR(100) NOT NULL,
            book_title VARCHAR(200) NOT NULL,
            borrow_date DATE NOT NULL,
            return_date DATE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS returns (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_name VARCHAR(100) NOT NULL,
            book_title VARCHAR(200) NOT NULL,
            borrow_date DATE NOT NULL,
            return_date DATE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Borrowing (
            BorrowID INT AUTO_INCREMENT PRIMARY KEY,
            StudentID INT,
            BookID INT,
            BorrowDate DATE,
            ReturnDate DATE,
            Returned BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
            FOREIGN KEY (BookID) REFERENCES Books(BookID)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Staff (
            StaffID INT AUTO_INCREMENT PRIMARY KEY,
            Name VARCHAR(255),
            Role VARCHAR(100),
            Email VARCHAR(100) UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Fines (
            FineID INT AUTO_INCREMENT PRIMARY KEY,
            BorrowID INT,
            Amount DECIMAL(10,2),
            Paid BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (BorrowID) REFERENCES Borrowing(BorrowID)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
@app.route('/borrowed-books')
def borrowed_books():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM borrowed_books")
    borrowed = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('borrowed_books.html', borrowed_books=borrowed)

@app.route('/')
def home():
    # Get dashboard statistics
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Book statistics
    cursor.execute("SELECT COUNT(*) as total FROM Books")
    book_stats = cursor.fetchone()
    
    # Get books added this month
    cursor.execute("""
        SELECT COUNT(*) as added_this_month 
        FROM Books 
        WHERE BookID IN (
            SELECT MAX(BookID) FROM Books
            GROUP BY Title, Author
            HAVING MAX(BookID) > (SELECT MAX(BookID) - 50 FROM Books)
        )
    """)
    books_added = cursor.fetchone()
    book_stats.update(books_added)
    
    # Student statistics
    cursor.execute("SELECT COUNT(*) as total FROM Students")
    student_stats = cursor.fetchone()
    
    # Get new registrations (assumed to be last 10 registrations)
    cursor.execute("""
        SELECT COUNT(*) as new_registrations 
        FROM Students 
        WHERE StudentID > (SELECT MAX(StudentID) - 10 FROM Students)
    """)
    new_registrations = cursor.fetchone()
    student_stats.update(new_registrations)
    
    # Borrowing statistics
    cursor.execute("""
        SELECT COUNT(*) as total 
        FROM Borrowing 
        WHERE Returned = FALSE
    """)
    borrow_stats = cursor.fetchone()
    
    # Books borrowed this week
    today = date.today()
    one_week_ago = today - timedelta(days=7)
    cursor.execute("""
        SELECT COUNT(*) as this_week 
        FROM Borrowing 
        WHERE BorrowDate >= %s
    """, (one_week_ago,))
    borrowed_this_week = cursor.fetchone()
    borrow_stats.update(borrowed_this_week)
    
    # Overdue books - Using ReturnDate field for due date calculation
    # Assume books are overdue if the ReturnDate (expected return) is before today
    # and they haven't been returned yet
    cursor.execute("""
        SELECT COUNT(*) as total 
        FROM Borrowing 
        WHERE ReturnDate < %s AND Returned = FALSE
    """, (today,))
    overdue_stats = cursor.fetchone()
    
    # Books due today
    cursor.execute("""
        SELECT COUNT(*) as due_today 
        FROM Borrowing 
        WHERE ReturnDate = %s AND Returned = FALSE
    """, (today,))
    due_today = cursor.fetchone()
    overdue_stats.update(due_today)
    
    cursor.close()
    conn.close()
    
    return render_template('index.html', 
                          book_stats=book_stats,
                          student_stats=student_stats,
                          borrow_stats=borrow_stats,
                          overdue_stats=overdue_stats)

# --- Student Routes ---
@app.route('/students')
def view_students():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Students")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_students.html', students=students)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    message = ""
    if request.method == 'POST':
        # Use correct field names from the form
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        reg_no = request.form['registration_number']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO Students (FirstName, LastName, Email, RegistrationNumber) VALUES (%s, %s, %s, %s)",
                (first_name, last_name, email, reg_no)
            )
            conn.commit()
            message = "Student added successfully!"
        except mysql.connector.Error as err:
            message = f"Error: {err}"
        finally:
            cursor.close()
            conn.close()
    
    return render_template('add_student.html', message=message)




        # 3. Insert into the database
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
            cursor.execute("INSERT INTO Books (Title, Author, Genre, PublishedYear, Quantity) VALUES (%s, %s, %s, %s, %s)",
                        (title, author, genre, published_year, quantity))
            conn.commit()
            message = "Book added successfully!"
    except mysql.connector.Error as err:
            message = f"Error: {err}"
            print(f"Error: {err}")  # Debugging
    finally:
            cursor.close()
            conn.close()

@app.route('/borrow_book', methods=['GET', 'POST'])
def borrow_book():
    message = ""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT StudentID, CONCAT(FirstName, ' ', LastName, ' (', RegistrationNumber, ')') as StudentName FROM Students")
    students = cursor.fetchall()

    cursor.execute("SELECT BookID, CONCAT(Title, ' by ', Author) as BookName, Quantity FROM Books WHERE Quantity > 0")
    available_books = cursor.fetchall()

    if request.method == 'POST':
        student_id = request.form['student_id']
        book_id = request.form['book_id']
        borrow_date = request.form['borrow_date'] or date.today()
        return_date = date.fromisoformat(borrow_date) + timedelta(days=14)

        print("Borrowing BookID:", book_id, "for StudentID:", student_id)

        cursor.execute("SELECT Quantity FROM Books WHERE BookID = %s", (book_id,))
        book = cursor.fetchone()

        if book and book['Quantity'] > 0:
            try:
                cursor.execute("""
                    INSERT INTO Borrowing (StudentID, BookID, BorrowDate, ReturnDate, Returned)
                    VALUES (%s, %s, %s, %s, %s)
                """, (student_id, book_id, borrow_date, return_date, False))

                cursor.execute("UPDATE Books SET Quantity = Quantity - 1 WHERE BookID = %s", (book_id,))
                conn.commit()

                message = "Book borrowed successfully!"

                # Refresh book list
                cursor.execute("SELECT BookID, CONCAT(Title, ' by ', Author) as BookName, Quantity FROM Books WHERE Quantity > 0")
                available_books = cursor.fetchall()
            except mysql.connector.Error as err:
                message = f"Error: {err}"
        else:
            message = "Book is not available."

    cursor.close()
    conn.close()

    return render_template('borrow_book.html', students=students, available_books=available_books, message=message)


@app.route('/return_book', methods=['GET', 'POST'])
def return_book():
    message = ""
    fine_amount = 0
    
    # Fetch current borrows
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT b.BorrowID, 
               CONCAT(s.FirstName, ' ', s.LastName) as StudentName, 
               bk.Title as BookTitle,
               b.BorrowDate, 
               b.ReturnDate as DueDate
        FROM Borrowing b
        JOIN Students s ON b.StudentID = s.StudentID
        JOIN Books bk ON b.BookID = bk.BookID
        WHERE b.Returned = FALSE
    """)
    active_borrows = cursor.fetchall()
    
    if request.method == 'POST':
        borrow_id = request.form['borrow_id']
        
        # Get the borrowing record
        cursor.execute("SELECT BookID, ReturnDate as DueDate FROM Borrowing WHERE BorrowID = %s", (borrow_id,))
        borrow = cursor.fetchone()
        
        if borrow:
            try:
                # Update the borrowing record
                cursor.execute("UPDATE Borrowing SET Returned = TRUE WHERE BorrowID = %s", (borrow_id,))
                
                # Update book quantity
                cursor.execute("UPDATE Books SET Quantity = Quantity + 1 WHERE BookID = %s", (borrow['BookID'],))
                
                # Check if the book is overdue and create a fine if needed
                today = date.today()
                if today > borrow['DueDate']:
                    days_overdue = (today - borrow['DueDate']).days
                    fine_amount = days_overdue * 5.00  # $5 per day
                    cursor.execute("INSERT INTO Fines (BorrowID, Amount) VALUES (%s, %s)", 
                                (borrow_id, fine_amount))
                    message = f"Book returned with a fine of ${fine_amount:.2f}"
                else:
                    message = "Book returned successfully!"
                
                conn.commit()
                
                # Refresh the active borrows list
                cursor.execute("""
                    SELECT b.BorrowID, 
                           CONCAT(s.FirstName, ' ', s.LastName) as StudentName, 
                           bk.Title as BookTitle,
                           b.BorrowDate, 
                           b.ReturnDate as DueDate
                    FROM Borrowing b
                    JOIN Students s ON b.StudentID = s.StudentID
                    JOIN Books bk ON b.BookID = bk.BookID
                    WHERE b.Returned = FALSE
                """)
                active_borrows = cursor.fetchall()
            except mysql.connector.Error as err:
                message = f"Error: {err}"
        else:
            message = "Borrowing record not found."
    
    cursor.close()
    conn.close()
    
    return render_template('return_book.html', 
                          borrows=active_borrows, 
                          message=message, 
                          fine_amount=fine_amount)
@app.route('/return_simple/<int:book_id>', methods=['POST'])
def return_simple(book_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    from datetime import date
    cursor.execute("""
        UPDATE borrowed_books
        SET return_date = %s
        WHERE id = %s
    """, (date.today(), book_id))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('return_view'))  # Or borrowed_books view

@app.route('/returns')
def return_view():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT b.BorrowID, 
               CONCAT(s.FirstName, ' ', s.LastName) as StudentName, 
               bk.Title as BookTitle,
               b.BorrowDate, 
               b.ReturnDate as DueDate
        FROM Borrowing b
        JOIN Students s ON b.StudentID = s.StudentID
        JOIN Books bk ON b.BookID = bk.BookID
        WHERE b.Returned = FALSE
    """)
    borrowed_books = cursor.fetchall()

    # Calculate overdue days
    for book in borrowed_books:
        # Convert string dates to datetime objects
        borrow_date = datetime.strptime(book['BorrowDate'], '%Y-%m-%d')  # Adjust format if needed
        due_date = datetime.strptime(book['DueDate'], '%Y-%m-%d')  # Adjust format if needed
        
        # Calculate overdue days (if any)
        overdue_days = (datetime.now() - due_date).days  # You can also compare with the borrow date if needed
        book['overdue_days'] = overdue_days  # Add the overdue days to the book entry

    cursor.close()
    conn.close()

    return render_template('returns.html', borrowed_books=borrowed_books)


  

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Tstaff")
    staff_list = cursor.fetchall()
    conn.close()
    print("--- Staff Data from / route ---")
    for staff_member in staff_list:
        print(staff_member)
    print("--- End of Staff Data ---")
    return render_template('staff.html', staff=staff_list)

from flask import redirect, url_for, render_template, flash

@app.route('/add_staff', methods=['GET', 'POST'])
def add_staff():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone_number = request.form['phone_number']
        email = request.form['email']
        role = request.form['role']
        
        # Add the staff to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Tstaff (first_name, last_name, phone_number, email, role) VALUES (%s, %s, %s, %s, %s)",
                       (first_name, last_name, phone_number, email, role))
        conn.commit()
        cursor.close()
        conn.close()
        
        # Pass success message to the template
        return render_template('add_staff.html', success_message="Tstaff member added successfully!")
    
    return render_template('add_staff.html')


@app.route('/edit/<int:staff_id>', methods=['GET', 'POST'])
def edit_staff(staff_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        cursor.execute("SELECT * FROM Tstaff WHERE staff_id = %s", (staff_id,))
        staff_member = cursor.fetchone()
        conn.close()
        if staff_member:
            return render_template('edit_staff.html', staff=staff_member)
        else:
            return redirect(url_for('view_staff'))

    elif request.method == 'POST':
        first = request.form['first_name']
        last = request.form['last_name']
        phone = request.form['phone_number']
        email = request.form['email']
        role = request.form['role']

        cursor.execute("""
            UPDATE Tstaff
            SET first_name=%s, last_name=%s, phone_number=%s, email=%s, role=%s
            WHERE staff_id=%s
        """, (first, last, phone, email, role, staff_id))
        conn.commit()
        conn.close()
        return redirect(url_for('view_staff'))

@app.route('/delete/<int:staff_id>')
def delete_staff(staff_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Tstaff WHERE staff_id=%s", (staff_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('view_staff'))


@app.route('/view_staff')
def view_staff():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Tstaff")
    staff_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('view_staff.html', staff=staff_list)

# Example dashboard route
@app.route('/')
def dashboard():
    return '''
        <div style="text-align:center; padding:30px;">
            <h1>Welcome to the Dashboard</h1>
            <a href="/view_staff" style="padding:10px 20px; background:#007bff; color:white; text-decoration:none; border-radius:5px;">
                View Staff
            </a>
        </div>
    '''



# --- API Routes (Keep these for potential future use) ---
@app.route('/api/students', methods=['POST'])
def add_student_api():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Students (FirstName, LastName, Email, RegistrationNumber) VALUES (%s, %s, %s, %s)",
                    (data['FirstName'], data['LastName'], data['Email'], data['RegistrationNumber']))
        conn.commit()
        response = {"message": "Student added successfully."}
    except mysql.connector.Error as err:
        response = {"error": str(err)}
    finally:
        cursor.close()
        conn.close()
    return jsonify(response)

@app.route('/api/borrow', methods=['POST'])
def borrow_book_api():
    data = request.json
    borrow_date = date.today()
    return_date = borrow_date + timedelta(days=14)  # This is actually the due date
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Quantity FROM Books WHERE BookID = %s", (data['BookID'],))
        book = cursor.fetchone()
        
        if book and book[0] > 0:
            cursor.execute("""
                INSERT INTO Borrowing (StudentID, BookID, BorrowDate, ReturnDate, Returned)
                VALUES (%s, %s, %s, %s, %s)
            """, (data['StudentID'], data['BookID'], borrow_date, return_date, False))
            
            cursor.execute("UPDATE Books SET Quantity = Quantity - 1 WHERE BookID = %s", (data['BookID'],))
            conn.commit()
            response = {"message": "Book borrowed successfully."}
        else:
            response = {"error": "Book is not available for borrowing."}
    except mysql.connector.Error as err:
        response = {"error": str(err)}
    finally:
        cursor.close()
        conn.close()
    return jsonify(response)

@app.route('/api/return', methods=['POST'])
def return_book_api():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM Borrowing WHERE BorrowID = %s", (data['BorrowID'],))
        borrow = cursor.fetchone()
        
        if not borrow:
            return jsonify({"error": "Borrow record not found."}), 404
        
        cursor.execute("UPDATE Borrowing SET Returned = TRUE WHERE BorrowID = %s", (data['BorrowID'],))
        cursor.execute("UPDATE Books SET Quantity = Quantity + 1 WHERE BookID = %s", (borrow['BookID'],))
        
        response = {"message": "Book returned successfully."}
        
        # Calculate fine if book is overdue
        today = date.today()
        if today > borrow['ReturnDate']:  # ReturnDate here is actually the due date
            days_overdue = (today - borrow['ReturnDate']).days
            fine_amount = days_overdue * 5.00
            cursor.execute("INSERT INTO Fines (BorrowID, Amount) VALUES (%s, %s)", 
                          (data['BorrowID'], fine_amount))
            response["fine"] = {"amount": fine_amount, "days_overdue": days_overdue}
        
        conn.commit()
    except mysql.connector.Error as err:
        response = {"error": str(err)}
    finally:
        cursor.close()
        conn.close()
    
    return jsonify(response)

@app.route('/api/staff', methods=['POST'])
def add_staff_api():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Staff (Name, Role, Email) VALUES (%s, %s, %s)",
                    (data['Name'], data['Role'], data['Email']))
        conn.commit()
        response = {"message": "Staff added successfully."}
    except mysql.connector.Error as err:
        response = {"error": str(err)}
    finally:
        cursor.close()
        conn.close()
    return jsonify(response)

#reports route 
@app.route('/reports')
def reports():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Total books
    cursor.execute("SELECT COUNT(*) as total_books FROM Books")
    total_books = cursor.fetchone()['total_books']
    
    # 2. Total students
    cursor.execute("SELECT COUNT(*) as total_students FROM Students")
    total_students = cursor.fetchone()['total_students']
    
    # 3. Total borrowed books
    cursor.execute("SELECT COUNT(*) as total_borrowed FROM Borrowing WHERE Returned = FALSE")
    total_borrowed = cursor.fetchone()['total_borrowed']
    
    # 4. Total fines (unpaid and paid)
    cursor.execute("SELECT SUM(Amount) as total_fines FROM Fines")
    total_fines = cursor.fetchone()['total_fines'] or 0.00
    
    cursor.execute("SELECT SUM(Amount) as unpaid_fines FROM Fines WHERE Paid = FALSE")
    unpaid_fines = cursor.fetchone()['unpaid_fines'] or 0.00
    
    cursor.execute("SELECT SUM(Amount) as paid_fines FROM Fines WHERE Paid = TRUE")
    paid_fines = cursor.fetchone()['paid_fines'] or 0.00
    
    # 5. Weekly borrowing stats
    one_week_ago = date.today() - timedelta(days=7)
    cursor.execute("""
        SELECT COUNT(*) as borrowed_this_week
        FROM Borrowing
        WHERE BorrowDate >= %s
    """, (one_week_ago,))
    borrowed_this_week = cursor.fetchone()['borrowed_this_week']
    
    # 6. Monthly borrowing trends (last 6 months)
    six_months_ago = date.today() - timedelta(days=180)
    cursor.execute("""
        SELECT 
            YEAR(BorrowDate) as year, 
            MONTH(BorrowDate) as month, 
            COUNT(*) as monthly_borrows
        FROM Borrowing
        WHERE BorrowDate >= %s
        GROUP BY YEAR(BorrowDate), MONTH(BorrowDate)
        ORDER BY YEAR(BorrowDate), MONTH(BorrowDate)
    """, (six_months_ago,))
    monthly_trends = cursor.fetchall()
    
    # 7. Book categories distribution
    cursor.execute("""
        SELECT Genre, COUNT(*) as count
        FROM Books
        GROUP BY Genre
        ORDER BY count DESC
        LIMIT 6
    """)
    category_distribution = cursor.fetchall()
    
    # 8. Recent borrowing activity
    cursor.execute("""
        SELECT 
            b.BorrowID,
            bk.Title,
            CONCAT(s.FirstName, ' ', s.LastName) as StudentName,
            b.BorrowDate,
            DATE_ADD(b.BorrowDate, INTERVAL 14 DAY) as DueDate,
            b.Returned,
            CASE
                WHEN b.Returned = TRUE THEN 'Returned'
                WHEN DATE_ADD(b.BorrowDate, INTERVAL 14 DAY) < CURDATE() THEN 'Overdue'
                ELSE 'Active'
            END as Status
        FROM Borrowing b
        JOIN Books bk ON b.BookID = bk.BookID
        JOIN Students s ON b.StudentID = s.StudentID
        ORDER BY b.BorrowDate DESC
        LIMIT 10
    """)
    recent_activity = cursor.fetchall()
    
    # 9. Overdue books
    cursor.execute("""
        SELECT 
            b.BorrowID,
            bk.Title,
            CONCAT(s.FirstName, ' ', s.LastName) as StudentName,
            b.BorrowDate,
            DATE_ADD(b.BorrowDate, INTERVAL 14 DAY) as DueDate,
            DATEDIFF(CURDATE(), DATE_ADD(b.BorrowDate, INTERVAL 14 DAY)) as DaysOverdue,
            COALESCE(f.Amount, 0) as FineAmount
        FROM Borrowing b
        JOIN Books bk ON b.BookID = bk.BookID
        JOIN Students s ON b.StudentID = s.StudentID
        LEFT JOIN Fines f ON b.BorrowID = f.BorrowID
        WHERE 
            b.Returned = FALSE AND 
            DATE_ADD(b.BorrowDate, INTERVAL 14 DAY) < CURDATE()
        ORDER BY DaysOverdue DESC
        LIMIT 10
    """)
    overdue_books = cursor.fetchall()
    
    # 10. Return rate
    cursor.execute("""
        SELECT 
            COUNT(*) as total_returns,
            SUM(CASE WHEN ReturnDate <= DATE_ADD(BorrowDate, INTERVAL 14 DAY) THEN 1 ELSE 0 END) as on_time,
            SUM(CASE 
                WHEN ReturnDate > DATE_ADD(BorrowDate, INTERVAL 14 DAY) AND 
                     ReturnDate <= DATE_ADD(BorrowDate, INTERVAL 21 DAY) THEN 1 
                ELSE 0 
            END) as late,
            SUM(CASE WHEN ReturnDate > DATE_ADD(BorrowDate, INTERVAL 21 DAY) THEN 1 ELSE 0 END) as very_late
        FROM Borrowing
        WHERE Returned = TRUE AND ReturnDate IS NOT NULL
    """)
    return_stats = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return render_template('reports.html',
                          total_books=total_books,
                          total_students=total_students,
                          total_borrowed=total_borrowed,
                          total_fines=total_fines,
                          unpaid_fines=unpaid_fines,
                          paid_fines=paid_fines,
                          borrowed_this_week=borrowed_this_week,
                          monthly_trends=monthly_trends,
                          category_distribution=category_distribution,
                          recent_activity=recent_activity,
                          overdue_books=overdue_books,
                          return_stats=return_stats)

@app.route('/api/report_data', methods=['GET'])
def report_data():
    try:
        date_range = request.args.get('date_range', '30')  # Default to 30 days
        category = request.args.get('category', 'all')
        status = request.args.get('status', 'all')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Convert date_range to datetime
        if date_range != 'all':
            filter_date = date.today() - timedelta(days=int(date_range))
            date_condition = "b.BorrowDate >= %s"
            date_params = (filter_date,)
        else:
            date_condition = "1=1"  # No date filtering
            date_params = ()
        
        # Category filtering
        if category != 'all':
            category_condition = "bk.Genre = %s"
            category_params = (category,)
        else:
            category_condition = "1=1"  # No category filtering
            category_params = ()
        
        # Status filtering
        if status == 'borrowed':
            status_condition = "b.Returned = FALSE AND DATE_ADD(b.BorrowDate, INTERVAL 14 DAY) >= CURDATE()"
        elif status == 'returned':
            status_condition = "b.Returned = TRUE"
        elif status == 'overdue':
            status_condition = "b.Returned = FALSE AND DATE_ADD(b.BorrowDate, INTERVAL 14 DAY) < CURDATE()"
        else:
            status_condition = "1=1"  # No status filtering
        
        # Query with all filters
        query = f"""
            SELECT 
                b.BorrowID,
                bk.Title,
                bk.Genre,
                CONCAT(s.FirstName, ' ', s.LastName) as StudentName,
                b.BorrowDate,
                b.ReturnDate,
                DATE_ADD(b.BorrowDate, INTERVAL 14 DAY) as DueDate,
                b.Returned,
                CASE
                    WHEN b.Returned = TRUE THEN 'Returned'
                    WHEN DATE_ADD(b.BorrowDate, INTERVAL 14 DAY) < CURDATE() THEN 'Overdue'
                    ELSE 'Active'
                END as Status,
                COALESCE(f.Amount, 0) as FineAmount
            FROM Borrowing b
            JOIN Books bk ON b.BookID = bk.BookID
            JOIN Students s ON b.StudentID = s.StudentID
            LEFT JOIN Fines f ON b.BorrowID = f.BorrowID
            WHERE {date_condition} AND {category_condition} AND {status_condition}
            ORDER BY b.BorrowDate DESC
            LIMIT 100
        """
        
        # Combine parameters
        params = date_params + category_params
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Get summary statistics
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_records,
                SUM(CASE WHEN b.Returned = FALSE THEN 1 ELSE 0 END) as active_borrows,
                SUM(CASE WHEN b.Returned = TRUE THEN 1 ELSE 0 END) as returned,
                SUM(CASE WHEN b.Returned = FALSE AND DATE_ADD(b.BorrowDate, INTERVAL 14 DAY) < CURDATE() THEN 1 ELSE 0 END) as overdue,
                SUM(COALESCE(f.Amount, 0)) as total_fines
            FROM Borrowing b
            JOIN Books bk ON b.BookID = bk.BookID
            LEFT JOIN Fines f ON b.BorrowID = f.BorrowID
            WHERE {date_condition} AND {category_condition}
        """, date_params + category_params)
        summary = cursor.fetchone()
        
        # Category distribution
        cursor.execute(f"""
            SELECT 
                bk.Genre,
                COUNT(*) as count
            FROM Borrowing b
            JOIN Books bk ON b.BookID = bk.BookID
            WHERE {date_condition}
            GROUP BY bk.Genre
            ORDER BY count DESC
        """, date_params)
        categories = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': results,
            'summary': summary,
            'categories': categories
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
@app.route('/api/export_csv', methods=['POST'])
def export_csv():
    try:
        date_range = request.form.get('date_range', 'all')
        category = request.form.get('category', 'all')
        status = request.form.get('status', 'all')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Build filter conditions similar to report_data endpoint
        if date_range != 'all':
            filter_date = date.today() - timedelta(days=int(date_range))
            date_condition = "b.BorrowDate >= %s"
            date_params = (filter_date,)
        else:
            date_condition = "1=1"
            date_params = ()
            
        if category != 'all':
            category_condition = "bk.Genre = %s"
            category_params = (category,)
        else:
            category_condition = "1=1"
            category_params = ()
            
        if status == 'borrowed':
            status_condition = "b.Returned = FALSE AND DATE_ADD(b.BorrowDate, INTERVAL 14 DAY) >= CURDATE()"
        elif status == 'returned':
            status_condition = "b.Returned = TRUE"
        elif status == 'overdue':
            status_condition = "b.Returned = FALSE AND DATE_ADD(b.BorrowDate, INTERVAL 14 DAY) < CURDATE()"
        else:
            status_condition = "1=1"
            
        # Execute query with filters
        query = f"""
            SELECT 
                bk.Title,
                bk.Author,
                bk.Genre,
                s.FirstName,
                s.LastName,
                s.Email,
                s.RegistrationNumber,
                b.BorrowDate,
                b.ReturnDate,
                DATE_ADD(b.BorrowDate, INTERVAL 14 DAY) as DueDate,
                CASE
                    WHEN b.Returned = TRUE THEN 'Returned'
                    WHEN DATE_ADD(b.BorrowDate, INTERVAL 14 DAY) < CURDATE() THEN 'Overdue'
                    ELSE 'Active'
                END as Status,
                COALESCE(f.Amount, 0) as FineAmount,
                CASE WHEN f.Paid = TRUE THEN 'Yes' WHEN f.Paid = FALSE THEN 'No' ELSE 'N/A' END as FinePaid
            FROM Borrowing b
            JOIN Books bk ON b.BookID = bk.BookID
            JOIN Students s ON b.StudentID = s.StudentID
            LEFT JOIN Fines f ON b.BorrowID = f.BorrowID
            WHERE {date_condition} AND {category_condition} AND {status_condition}
            ORDER BY b.BorrowDate DESC
        """
        
        # Combine parameters
        params = date_params + category_params
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Create a StringIO object for the CSV data
        csv_data = io.StringIO()
        csv_writer = csv.writer(csv_data)
        
        # Write headers
        if results:
            headers = results[0].keys()
            csv_writer.writerow(headers)
            
            # Write data rows
            for row in results:
                csv_writer.writerow(row.values())
        
        # Create response
        response = make_response(csv_data.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=library_report.csv"
        response.headers["Content-type"] = "text/csv"
        
        return response
        
    except Exception as e:
        # If error, return to reports page with error message
        flash(f"Error exporting data: {str(e)}", "error")
        return redirect(url_for('reports'))


if __name__ == '__main__':
    create_tables()  # Create tables if they don't exist
    app.run(debug=True)