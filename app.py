import email
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# MySQL connection with URL-encoded password (if it has special characters)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Bloom123%40fidey@localhost/student_booking_system'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Staff(db.Model):
    staff_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)

# Redirect root (/) to /staff
@app.route('/')
def home():
    return redirect(url_for('staff'))

@app.route('/staff')
def staff():
    staff_members = Staff.query.all()
    return render_template('staff.html', staff=staff_members)

@app.route('/add_staff', methods=['GET', 'POST'])
def add_staff():
    if request.method == 'POST':
        # Get data from the form
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone_number = request.form['phone_number']
        email = request.form['email']
        role = request.form['role']

        # Create a new staff member and add to the database
        new_staff = Staff(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            email=email,
            role=role
        )
        db.session.add(new_staff)
        db.session.commit()

        # Redirect to the staff list page
        return redirect('/staff')

    # If GET request, display the add staff form
    return render_template('add_staff.html')

@app.route('/edit_staff/<int:staff_id>', methods=['GET', 'POST'])
def edit_staff(staff_id):
    staff_member = Staff.query.get(staff_id)
    if request.method == 'POST':
        staff_member.first_name = request.form['first_name']
        staff_member.last_name = request.form['last_name']
        staff_member.phone_number = request.form['phone_number']
        staff_member.email = request.form['email']
        staff_member.role = request.form['role']

        db.session.commit()
        return redirect(url_for('staff'))

    return render_template('edit_staff.html', staff=staff_member)

@app.route('/delete_staff/<int:staff_id>', methods=['GET'])
def delete_staff(staff_id):
    staff_member = Staff.query.get(staff_id)
    if staff_member:
        db.session.delete(staff_member)
        db.session.commit()
    return redirect('/staff')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
