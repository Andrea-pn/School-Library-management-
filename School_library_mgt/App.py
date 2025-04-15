from flask import Flask, jsonify, redirect, request, render_template, url_for
import mysql.connector
from datetime import date, timedelta

app = Flask(__name__)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',  # Replace with your MySQL username
    'password': '343434',  # Replace with your MySQL password
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

# --- Book Routes ---
@app.route('/books')
def view_books():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Books")
    books = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_books.html', books=books)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    message = ""
    if request.method == 'POST':
        # 1. Get form data
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']
        published_year = request.form['published_year']
        quantity = request.form['quantity']

        print(f"Title: {title}, Author: {author}, Genre: {genre}, Published Year: {published_year}, Quantity: {quantity}")  # Debugging

        # 2. Validate year and quantity as integers
        try:
            published_year = int(published_year)
            quantity = int(quantity)
        except ValueError:
            message = "Year and Quantity must be valid numbers."
            return render_template('add_book.html', message=message)

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
    return render_template('add_book.html', message=message)


# --- Borrowing Routes ---
@app.route('/borrow_book', methods=['GET', 'POST'])
def borrow_book():
    message = ""
    # Fetch students and books for dropdowns
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT StudentID, CONCAT(FirstName, ' ', LastName, ' (', RegistrationNumber, ')') as StudentName FROM Students")
    students = cursor.fetchall()
    
    cursor.execute("SELECT BookID, CONCAT(Title, ' by ', Author) as BookName, Quantity FROM Books WHERE Quantity > 0")
    available_books = cursor.fetchall()
    
    if request.method == 'POST':
        student_id = request.form['student_id']
        book_id = request.form['book_id']
        borrow_date = date.today()
        return_date = borrow_date + timedelta(days=14)  # 2 weeks loan period
        
        # Check if the book is available
        cursor.execute("SELECT Quantity FROM Books WHERE BookID = %s", (book_id,))
        book = cursor.fetchone()
        
        if book and book['Quantity'] > 0:
            try:
                # Insert borrow record
                cursor.execute("""
                    INSERT INTO Borrowing (StudentID, BookID, BorrowDate, ReturnDate, Returned)
                    VALUES (%s, %s, %s, %s, %s)
                """, (student_id, book_id, borrow_date, return_date, False))
                
                # Update book quantity
                cursor.execute("UPDATE Books SET Quantity = Quantity - 1 WHERE BookID = %s", (book_id,))
                conn.commit()
                message = "Book borrowed successfully!"
                
                # Refresh the available books list
                cursor.execute("SELECT BookID, CONCAT(Title, ' by ', Author) as BookName, Quantity FROM Books WHERE Quantity > 0")
                available_books = cursor.fetchall()
            except mysql.connector.Error as err:
                message = f"Error: {err}"
        else:
            message = "Book is not available for borrowing."
    
    cursor.close()
    conn.close()
    
    return render_template('borrow_book.html', 
                          students=students, 
                          books=available_books, 
                          message=message)

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

# --- Staff Routes ---
@app.route('/view_staff')
def view_staff():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Staff")
    staff = cursor.fetchall()
    cursor.close()
    conn.close()

    # Debugging: Check the staff data
    print("Staff data:", staff)

    return render_template('view_staff.html', staff=staff)


@app.route('/add_staff', methods=['GET', 'POST'])
def add_staff():
    message = ""
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        email = request.form['email']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO Staff (Name, Role, Email) VALUES (%s, %s, %s)",
                        (name, role, email))
            conn.commit()
            message = "Staff member added successfully!"
        except mysql.connector.Error as err:
            message = f"Error: {err}"
        finally:
            cursor.close()
            conn.close()
    
    return render_template('add_staff.html', message=message)

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

if __name__ == '__main__':
    create_tables()  # Create tables if they don't exist
    app.run(debug=True)