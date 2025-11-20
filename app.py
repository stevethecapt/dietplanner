from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

# Inisialisasi Aplikasi Flask
# __name__ memberitahu Flask di mana mencari resources seperti template
app = Flask(__name__)
app.secret_key = 'dietplanner-secret-key'

# Konfigurasi MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Ganti dengan password MySQL Anda
app.config['MYSQL_DB'] = 'dietplanner'
mysql = MySQL(app)

# --- Routes Aplikasi ---

# Route untuk halaman utama (index.html)
# URL: / atau <url_aplikasi>/
@app.route('/')
def index():
    # Merender file 'index.html' yang ada di folder 'templates'
    return render_template('index.html')

# Route untuk halaman Login (login.html)
# URL: /login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['id'] = user['id']
            session['username'] = user['username']
            flash('Login berhasil!')
            return redirect(url_for('index'))
        else:
            flash('Login gagal. Cek email/username dan password.')
    return render_template('login.html')

# Route untuk halaman Pendaftaran/Sign-up (signup.html)
# URL: /signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm-password')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            flash('Email sudah terdaftar!')
        elif password != confirm:
            flash('Password dan konfirmasi tidak sama.')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Email tidak valid!')
        elif not name or not username or not password:
            flash('Lengkapi semua data!')
        else:
            cursor.execute('INSERT INTO users (name, email, username, password) VALUES (%s, %s, %s, %s)', (name, email, username, password))
            mysql.connection.commit()
            flash('Registrasi berhasil!')
            return redirect(url_for('login'))
    return render_template('signup.html')

# Route untuk halaman Reset Password (resetpassword.html)
# URL: /reset-password
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form.get('username')
        flash(f'Instruksi reset password telah dikirim ke {username}.')
        return redirect(url_for('login'))
    return render_template('resetpassword.html')


# --- Menjalankan Aplikasi ---

# Bagian ini akan dieksekusi ketika Anda menjalankan file app.py secara langsung
def create_db():
    cursor = mysql.connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        username VARCHAR(100) NOT NULL,
        password VARCHAR(100) NOT NULL
    )''')
    mysql.connection.commit()

if __name__ == '__main__':
    with app.app_context():
        create_db()
    app.run(debug=True)