from flask import Flask, render_template

# Inisialisasi Aplikasi Flask
# __name__ memberitahu Flask di mana mencari resources seperti template
app = Flask(__name__)

# --- Routes Aplikasi ---

# Route untuk halaman utama (index.html)
# URL: / atau <url_aplikasi>/
@app.route('/')
def index():
    # Merender file 'index.html' yang ada di folder 'templates'
    return render_template('index.html')

# Route untuk halaman Login (login.html)
# URL: /login
@app.route('/login')
def login():
    return render_template('login.html')

# Route untuk halaman Pendaftaran/Sign-up (signup.html)
# URL: /signup
@app.route('/signup')
def signup():
    return render_template('signup.html')

# Route untuk halaman Reset Password (resetpassword.html)
# URL: /reset-password
@app.route('/reset-password')
def reset_password():
    return render_template('resetpassword.html')


# --- Menjalankan Aplikasi ---

# Bagian ini akan dieksekusi ketika Anda menjalankan file app.py secara langsung
if __name__ == '__main__':
    # app.run() menjalankan server pengembangan. 
    # debug=True memungkinkan mode debugging dan auto-reload.
    app.run(debug=True)