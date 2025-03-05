from flask import Flask, jsonify, request, render_template
import mysql.connector

app = Flask(__name__)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',  # Replace with your MySQL username
    'password': 'precious',  # Replace with your MySQL password
    'database': 'SchoolLibrary'
}

# Connect to MySQL
def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# API to get all books
@app.route('/api/books', methods=['GET'])
def get_books():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Books")
    books = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(books)

# API to add a new book
@app.route('/api/books', methods=['POST'])
def add_book():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Books (Title, Author, Genre, PublishedYear, Quantity) VALUES (%s, %s, %s, %s, %s)",
        (data['Title'], data['Author'], data['Genre'], data['PublishedYear'], data['Quantity'])
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Book added successfully!"})

# Add more APIs for Students and BorrowedBooks as needed

if __name__ == '__main__':
    app.run(debug=True)