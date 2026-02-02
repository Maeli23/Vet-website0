from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from flask_socketio import SocketIO, emit
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
socketio = SocketIO(app)

ADMIN_SECRET_CODE = 'dCcP'

DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db():
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                is_locked BOOLEAN NOT NULL DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                credentials TEXT NOT NULL,
                achievements TEXT NOT NULL,
                contact TEXT,
                location TEXT,
                image TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                content BLOB NOT NULL,
                is_deleted BOOLEAN NOT NULL DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vet_id INTEGER,
                date TEXT,
                time TEXT,
                notes TEXT    
            )
        """)
        conn.commit()

@app.before_request
def before_request():
    create_tables()
    if 'user_id' in session:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
        user = cur.fetchone()
        if user and user['is_locked']:
            session.clear()
            flash('Your account is locked. Please contact admin.')
            return redirect(url_for('login'))

@app.route('/')
def home():
    return redirect(url_for('Index'))
@app.route('/user_home')
def user_home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('user_home.html')

@app.route('/Index')
def Index():
    return render_template('Index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        flash('Thank you for your message!', 'success')
        return redirect(url_for('Index'))
    return render_template('contact.html')

@app.route('/vets', methods=['GET', 'POST'])
def vets():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    vets = cur.fetchall()
    return render_template('vets.html', vets=vets)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        try:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                            (username, email, password))
                conn.commit()
                flash('Registration successful! Please login.')
                return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()

        if user:
            if user['is_locked']:
                flash('Your account is locked. Please contact admin.')
                return redirect(url_for('login'))

            if check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash('Login successful!')
                return redirect(url_for('user_home'))
        
        flash('Invalid credentials')
        return redirect(url_for('login'))
    return render_template('login.html')
        

@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        secret_code = request.form['secret_code']
        
        if secret_code != ADMIN_SECRET_CODE:
            flash('Invalid secret code!', 'danger')
            return redirect(url_for('admin_register'))
        try:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO admins (username, email, password) VALUES (?, ?, ?)",
                            (username, email, password))
                conn.commit()
                flash('Admin registration successful! Please login.')
                return redirect(url_for('admin_login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.')
            return redirect(url_for('admin_register'))
    return render_template('admin_register.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == ('POST'):
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM admins WHERE username = ?", (username,))
        admin = cur.fetchone()

        if admin and check_password_hash(admin['password'], password):
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            flash('Admin login successful!')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('admin_login'))
    return render_template('admin_login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin_logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cur.fetchone()
    if user and user['is_locked']:
        session.clear()
        flash('Your account is locked. Please contact admin.')
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_username' not in session:
        return redirect(url_for('admin_login'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    return render_template('admin_dashboard.html', users=users)

@app.route('/add_user', methods=['POST'])
def add_user():
    if 'admin_username' not in session:
        return redirect(url_for('admin_login'))

    username = request.form['username']
    email = request.form['email']
    password = generate_password_hash(request.form['password'])

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                        (username, email, password))
            conn.commit()
            flash('User added successfully!')
    except sqlite3.IntegrityError:
        flash('Username or email already exists.')

    return redirect(url_for('admin_dashboard'))

@app.route('/lock_user/<int:user_id>')
def lock_user(user_id):
    if 'admin_username' not in session:
        return redirect(url_for('admin_login'))

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_locked = 1 WHERE id = ?", (user_id,))
        conn.commit()
    flash('User locked successfully.')
    return redirect(url_for('admin_dashboard'))

@app.route('/unlock_user/<int:user_id>')
def unlock_user(user_id):
    if 'admin_username' not in session:
        return redirect(url_for('admin_login'))

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_locked = 0 WHERE id = ?", (user_id,))
        conn.commit()
    flash('User unlocked successfully.')
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'admin_username' not in session:
        return redirect(url_for('admin_login'))

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    flash('User deleted successfully.')
    return redirect(url_for('admin_dashboard'))

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    message = request.json.get('message')
    return jsonify({'message': message})

@app.route('/chart_data')
def chart_data():
    if 'username' not in session:
        return redirect(url_for('login'))

    data = {
        "labels": ["January", "February", "March", "April", "May"],
        "datasets": [{
            "label": "Sales",
            "data": [12, 19, 3, 5, 2],
        }]
    }
    return jsonify(data)

@app.route('/notifications')
def notifications():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM notifications ORDER BY timestamp DESC")
    notifications = cur.fetchall()
    return jsonify([dict(notification) for notification in notifications])

@app.route('/appointments')
def appointments():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM appointments ORDER BY date, time")
    appointments = cur.fetchall()
    return jsonify([dict(appointment) for appointment in appointments])

@app.route('/health_records')
def health_records():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM health_records ORDER BY date DESC")
    health_records = cur.fetchall()
    return jsonify([dict(record) for record in health_records])

@app.route('/faq')
def faq():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM faq")
    faq = cur.fetchall()
    return jsonify([dict(item) for item in faq])

if __name__ == '__main__':
    socketio.run(app, debug=True)
