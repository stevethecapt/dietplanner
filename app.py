from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from werkzeug.security import generate_password_hash, check_password_hash

# Inisialisasi Aplikasi Flask
app = Flask(__name__)
app.secret_key = 'dietplanner-secret-key'

# Konfigurasi MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # jika MySQL pakai password, isi di sini
app.config['MYSQL_DB'] = 'dietplanner'

mysql = MySQL(app)

# ---------------------------------------------------------
# ROUTE: Home Page
# ---------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')


# ---------------------------------------------------------
# ROUTE: Login
# ---------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        login_input = request.form.get('email')  # bisa berisi email atau username
        password_input = request.form.get('password')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Ambil user berdasarkan email atau username
        cursor.execute(
            'SELECT * FROM users WHERE email = %s OR username = %s',
            (login_input, login_input)
        )
        user = cursor.fetchone()

        # Validasi login
        if user and check_password_hash(user['password_hash'], password_input):
            session['loggedin'] = True
            session['id'] = user['id']
            session['username'] = user['username']
            flash('Login berhasil!')
            return redirect(url_for('index'))
        else:
            flash('Email/Username atau password salah.')

    return render_template('login.html')

# ---------------------------------------------------------
# ROUTE: Signup / Register
# ---------------------------------------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':

        fullname = request.form.get('name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Cek apakah email sudah terdaftar
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()

        if account:
            flash('Email sudah terdaftar!')
        elif password != confirm_password:
            flash('Password dan konfirmasi tidak sama.')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Format email tidak valid.')
        elif not fullname or not username or not password:
            flash('Semua field wajib diisi.')
        else:
            # Hash password
            hashed_pw = generate_password_hash(password)

            cursor.execute(
                'INSERT INTO users (fullname, email, username, password_hash) '
                'VALUES (%s, %s, %s, %s)',
                (fullname, email, username, hashed_pw)
            )

            mysql.connection.commit()
            flash('Registrasi berhasil! Silakan login.')
            return redirect(url_for('login'))

    return render_template('signup.html')


# ---------------------------------------------------------
# ROUTE: Reset Password (Dummy)
# ---------------------------------------------------------
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form.get('username')
        flash(f'Instruksi reset password telah dikirim ke {username}. (simulasi)')
        return redirect(url_for('login'))
    return render_template('resetpassword.html')


# ---------------------------------------------------------
# ROUTE: Diet 21 Hari (protected)
# ---------------------------------------------------------
@app.route('/diet21hari')
def diet21hari():
    if not session.get('loggedin'):
        flash("Silakan login terlebih dahulu.")
        return redirect(url_for('login'))

    return render_template("diet21hari.html")


# ---------------------------------------------------------
# ROUTE: Logout
# ---------------------------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Anda telah logout.")
    return redirect(url_for('index'))


# ---------------------------------------------------------
# RUN SERVER
# ---------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
