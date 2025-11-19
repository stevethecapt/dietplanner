from flask import Flask, render_template, request, redirect, url_for, flash

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
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # Dummy authentication logic
        if email == 'admin' and password == 'admin':
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
        if password != confirm:
            flash('Password dan konfirmasi tidak sama.')
        else:
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
if __name__ == '__main__':
    app.secret_key = 'dietplanner-secret-key'
    app.run(debug=True)