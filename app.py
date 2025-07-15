from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'delligence_academy_secret_key_2025'

# Upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------- Initialize Database --------------------
def init_db():
    con = sqlite3.connect("school.db")
    cur = con.cursor()

    # Students Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            marks INTEGER NOT NULL
        )
    """)

    # Contacts Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Fees Table (Monthly)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            month TEXT NOT NULL,
            year TEXT NOT NULL,
            date TEXT DEFAULT (datetime('now', 'localtime')),
            UNIQUE(student_id, month, year),
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    # Tests Table (Test-wise marks)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            test_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            marks INTEGER NOT NULL,
            max_marks INTEGER NOT NULL,
            test_date TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    # Homework Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS homework (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            book_page TEXT,
            photo_url TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    con.commit()
    con.close()

# -------------------- Get Next Available Student ID --------------------
def get_next_available_id():
    con = sqlite3.connect("school.db")
    cur = con.cursor()
    cur.execute("SELECT id FROM students ORDER BY id ASC")
    ids = [row[0] for row in cur.fetchall()]
    con.close()

    for i in range(len(ids)):
        if ids[i] != i + 1:
            return i + 1
    return len(ids) + 1

# -------------------- Routes --------------------

@app.route("/")
def index():
    # Check if user is logged in and user type or admin access
    if 'user_type' not in session:
        # Check for admin access from login page
        admin_access = request.args.get('admin', False)
        if not admin_access:
            return redirect(url_for('login'))
        else:
            # Set admin session
            session['user_type'] = 'admin'
            session['user_info'] = {'id': 'admin', 'name': 'Administrator'}
    
    con = sqlite3.connect("school.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM students ORDER BY id")
    students = cur.fetchall()
    con.close()
    
    user_type = session.get('user_type')
    user_info = session.get('user_info', {})
    
    return render_template("index.html", students=students, user_type=user_type, user_info=user_info)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_type = request.form["user_type"]
        
        if user_type == "student":
            student_id = request.form["student_id"]
            student_name = request.form["student_name"]
            
            # Verify student exists in database
            con = sqlite3.connect("school.db")
            cur = con.cursor()
            cur.execute("SELECT id, name FROM students WHERE id = ? AND name = ?", (student_id, student_name))
            student = cur.fetchone()
            con.close()
            
            if student:
                session['user_type'] = 'student'
                session['user_info'] = {'id': student[0], 'name': student[1]}
                return redirect(url_for('index'))
            else:
                return render_template("login.html", msg="❌ Invalid student credentials!")
        
        elif user_type == "teacher":
            teacher_id = request.form["teacher_id"]
            teacher_password = request.form["teacher_password"]
            
            # Simple teacher authentication (you can enhance this)
            if teacher_id == "teacher123" and teacher_password == "delligence123":
                session['user_type'] = 'teacher'
                session['user_info'] = {'id': teacher_id, 'name': 'Teacher'}
                return redirect(url_for('index'))
            else:
                return render_template("login.html", msg="❌ Invalid teacher credentials!")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/add", methods=["POST"])
def add_student():
    # Only allow admin (with password) or logged in users to add students
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    name = request.form["name"]
    marks = request.form["marks"]
    student_id = get_next_available_id()

    con = sqlite3.connect("school.db")
    cur = con.cursor()
    cur.execute("INSERT INTO students (id, name, marks) VALUES (?, ?, ?)", (student_id, name, marks))
    con.commit()
    con.close()
    return redirect("/")

@app.route("/delete/<int:id>")
def delete_student(id):
    con = sqlite3.connect("school.db")
    cur = con.cursor()
    cur.execute("DELETE FROM students WHERE id = ?", (id,))
    con.commit()
    con.close()
    return redirect("/")

@app.route("/about")
def about():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    user_type = session.get('user_type')
    user_info = session.get('user_info', {})
    return render_template("about.html", user_type=user_type, user_info=user_info)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    user_type = session.get('user_type')
    user_info = session.get('user_info', {})
    
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        message = request.form["message"]

        con = sqlite3.connect("school.db")
        cur = con.cursor()
        cur.execute("INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)", (name, email, message))
        con.commit()
        con.close()

        return render_template("contact.html", success=True, user_type=user_type, user_info=user_info)

    return render_template("contact.html", success=False, user_type=user_type, user_info=user_info)

@app.route("/messages")
def messages():
    con = sqlite3.connect("school.db")
    cur = con.cursor()
    cur.execute("SELECT name, email, message, timestamp FROM contacts ORDER BY timestamp DESC")
    messages = cur.fetchall()
    con.close()
    return render_template("messages.html", messages=messages)

@app.route("/fees", methods=["GET", "POST"])
def fees():
    con = sqlite3.connect("school.db")
    cur = con.cursor()
    msg = None

    if request.method == "POST":
        student_id = request.form["student_id"]
        amount = request.form["amount"]
        month = request.form["month"]
        year = request.form["year"]

        try:
            cur.execute("""
                INSERT INTO fees (student_id, amount, month, year)
                VALUES (?, ?, ?, ?)
            """, (student_id, amount, month, year))
            con.commit()
            msg = "✅ Fee recorded successfully."
        except sqlite3.IntegrityError:
            msg = "⚠️ Fee already submitted for this month."

    cur.execute("SELECT id, name FROM students ORDER BY id")
    students = cur.fetchall()

    cur.execute("""
        SELECT students.name, fees.amount, fees.month, fees.year, fees.date
        FROM fees
        JOIN students ON students.id = fees.student_id
        ORDER BY fees.year DESC, fees.month DESC
    """)
    fee_records = cur.fetchall()
    con.close()
    return render_template("fees.html", students=students, fee_records=fee_records, msg=msg)

@app.route("/tests", methods=["GET", "POST"])
def tests():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    user_type = session.get('user_type')
    user_info = session.get('user_info', {})
    
    # Only teachers can access tests
    if user_type != 'teacher':
        return redirect(url_for('index'))
    
    con = sqlite3.connect("school.db")
    cur = con.cursor()
    msg = None

    if request.method == "POST":
        student_id = request.form["student_id"]
        test_name = request.form["test_name"]
        subject = request.form["subject"]
        marks = request.form["marks"]
        max_marks = request.form["max_marks"]

        try:
            cur.execute("""
                INSERT INTO tests (student_id, test_name, subject, marks, max_marks)
                VALUES (?, ?, ?, ?, ?)
            """, (student_id, test_name, subject, marks, max_marks))
            con.commit()
            msg = "✅ Test marks added successfully."
        except Exception as e:
            msg = f"⚠️ Error adding test marks: {str(e)}"

    # Get all students for dropdown
    cur.execute("SELECT id, name FROM students ORDER BY id")
    students = cur.fetchall()

    # Get all test records with student names
    cur.execute("""
        SELECT students.name, tests.test_name, tests.subject, tests.marks, tests.max_marks, tests.test_date
        FROM tests
        JOIN students ON students.id = tests.student_id
        ORDER BY tests.test_date DESC, students.name
    """)
    test_records = cur.fetchall()

    # Get test records grouped by student
    cur.execute("""
        SELECT students.id, students.name, tests.test_name, tests.subject, tests.marks, tests.max_marks, tests.test_date
        FROM tests
        JOIN students ON students.id = tests.student_id
        ORDER BY students.name, tests.test_date DESC
    """)
    student_tests = cur.fetchall()

    con.close()
    return render_template("tests.html", students=students, test_records=test_records, student_tests=student_tests, msg=msg, user_type=user_type, user_info=user_info)

@app.route("/homework", methods=["GET", "POST"])
def homework():
    if 'user_type' not in session:
        return redirect(url_for('login'))
    
    user_type = session.get('user_type')
    user_info = session.get('user_info', {})
    
    con = sqlite3.connect("school.db")
    cur = con.cursor()
    msg = None

    # Only teachers can add homework
    if request.method == "POST" and user_type == 'teacher':
        date = request.form["date"]
        subject = request.form["subject"]
        description = request.form["description"]
        book_page = request.form["book_page"]
        
        # Handle file upload
        photo_url = ""
        if 'photo_file' in request.files:
            file = request.files['photo_file']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to filename to avoid conflicts
                import time
                timestamp = str(int(time.time()))
                name, ext = os.path.splitext(filename)
                unique_filename = f"{name}_{timestamp}{ext}"
                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(file_path)
                photo_url = f"uploads/{unique_filename}"
            elif file and file.filename != '':
                msg = "⚠️ Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WEBP files only."

        try:
            if not msg:  # Only proceed if no file error
                cur.execute("""
                    INSERT INTO homework (date, subject, description, book_page, photo_url)
                    VALUES (?, ?, ?, ?, ?)
                """, (date, subject, description, book_page, photo_url))
                con.commit()
                msg = "✅ Homework added successfully."
        except Exception as e:
            msg = f"⚠️ Error adding homework: {str(e)}"

    # Get all homework records
    cur.execute("""
        SELECT date, subject, description, book_page, photo_url, created_at
        FROM homework
        ORDER BY date DESC, created_at DESC
    """)
    homework_records = cur.fetchall()

    con.close()
    return render_template("homework.html", homework_records=homework_records, msg=msg, user_type=user_type, user_info=user_info)

@app.route("/validate-password", methods=["POST"])
def validate_password():
    data = request.get_json()
    entered_password = data.get('password', '')

    # Get password from environment variable (set in Replit Secrets)
    correct_password = os.environ.get('ADMIN_PASSWORD', 'delligence123')

    if entered_password == correct_password:
        return jsonify({'valid': True})
    else:
        return jsonify({'valid': False})

@app.route("/admin")
def admin_panel():
    # Direct admin access - set admin session
    session['user_type'] = 'admin'
    session['user_info'] = {'id': 'admin', 'name': 'Administrator'}
    return redirect(url_for('index'))

# -------------------- Main Entry Point --------------------
if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=int(__import__('os').environ.get('PORT', 5000)))