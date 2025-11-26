from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import MySQLdb
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
        try:
            # Ambil user berdasarkan email atau username
            cursor.execute(
                'SELECT * FROM users WHERE email = %s OR username = %s',
                (login_input, login_input)
            )
            user = cursor.fetchone()
        finally:
            try:
                cursor.close()
            except Exception:
                pass

        # Validasi login
        if user and check_password_hash(user['password_hash'], password_input):
            session['loggedin'] = True
            session['id'] = user['id']
            session['username'] = user['username']
            flash('Login berhasil!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email atau password salah.', 'error')

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
        try:
            # Cek apakah email atau username sudah terdaftar
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            account_email = cursor.fetchone()
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            account_username = cursor.fetchone()

            if account_email:
                flash('Email sudah terdaftar!', 'error')
            elif account_username:
                flash('Username sudah terdaftar!', 'error')
            elif password != confirm_password:
                flash('Password dan konfirmasi tidak sama.', 'error')
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                flash('Format email tidak valid.', 'error')
            elif not fullname or not username or not password:
                flash('Semua field wajib diisi.', 'error')
            else:
                # Hash password
                hashed_pw = generate_password_hash(password)

                try:
                    cursor.execute(
                        'INSERT INTO users (fullname, email, username, password_hash) '
                        'VALUES (%s, %s, %s, %s)',
                        (fullname, email, username, hashed_pw)
                    )
                    mysql.connection.commit()
                    flash('Registrasi berhasil! Silakan login.', 'success')
                    return redirect(url_for('login'))
                except MySQLdb.IntegrityError as ie:
                    # This handles unique constraint violations that may happen due to race conditions
                    errstr = str(ie)
                    if 'email' in errstr.lower():
                        flash('Gagal: Email sudah terdaftar (konkurensi).', 'error')
                    elif 'username' in errstr.lower():
                        flash('Gagal: Username sudah terdaftar (konkurensi).', 'error')
                    else:
                        flash('Gagal registrasi: data sudah ada.', 'error')
                except Exception as e:
                    app.logger.error('Error saat mendaftar user: %s', e)
                    flash('Terjadi kesalahan saat registrasi. Coba lagi nanti.', 'error')
        finally:
            try:
                cursor.close()
            except Exception:
                pass

    return render_template('signup.html')


# ---------------------------------------------------------
# ROUTE: Reset Password (Dummy)
# ---------------------------------------------------------
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form.get('username')
        flash(f'Instruksi reset password telah dikirim ke {username}. (simulasi)', 'info')
        return redirect(url_for('login'))
    return render_template('resetpassword.html')


# ---------------------------------------------------------
# ROUTE: Diet Planner (protected)
# ---------------------------------------------------------
@app.route('/dietplanner', methods=['GET', 'POST'])
def dietplanner():
    if not session.get('loggedin'):
        flash("Silakan login terlebih dahulu.", 'error')
        return redirect(url_for('login'))

    result = None
    if request.method == 'POST':
        # Ambil data dari form
        weight = float(request.form.get('weight', 0))
        height = float(request.form.get('height', 0))
        age = int(request.form.get('age', 0))
        gender = request.form.get('gender')
        activity = request.form.get('activity')
        goal = request.form.get('goal')

        # Hitung BMI
        height_m = height / 100
        bmi = round(weight / (height_m * height_m), 1)

        # Status BMI (DITAMBAHKAN sesuai permintaan)
        if bmi < 16:
            bmi_status = "Sangat Kurus"
        elif 16 <= bmi < 18.5:
            bmi_status = "Kurus"
        elif 18.5 <= bmi < 22:
            bmi_status = "Normal"
        elif 22 <= bmi < 25:
            bmi_status = "Ideal"
        elif 25 <= bmi < 27:
            bmi_status = "Gemuk"
        elif 27 <= bmi < 30:
            bmi_status = "Sangat Gemuk"
        else:
            bmi_status = "Obesitas"

        # Hitung BMR
        if gender == 'male':
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)

        # Faktor aktivitas
        activity_factors = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9
        }
        factor = activity_factors.get(activity, 1.2)
        daily_calories = int(bmr * factor)

        # Rekomendasi otomatis berdasarkan BMI (Bahasa Indonesia)
        if bmi_status in ["Sangat Kurus", "Kurus"]:
            system_recommendation = "Kekurangan gizi. Direkomendasikan menaikkan berat badan dengan asupan kalori lebih tinggi dan latihan penguatan otot."
            deposit_calories = daily_calories + 400
            # for underweight, suggest calorie-dense healthy foods
            food = "Susu penuh lemak, telur, daging tanpa lemak, roti gandum, selai kacang, alpukat, pisang"
            exercise = "Latihan kekuatan ringan, peningkatan frekuensi makan: 3-4x/ hari"
        elif bmi_status in ["Normal", "Ideal"]:
            # Provide maintenance recommendations in Indonesian
            system_recommendation = (
                "Berat badan dalam kisaran normal. Untuk mempertahankan berat badan, "
                "pertahankan asupan kalori seimbang, porsi terkontrol, dan olahraga teratur."
            )
            deposit_calories = daily_calories
            # maintenance suggestions
            food = "Porsi seimbang: karbohidrat kompleks, sumber protein, sayur, buah; batasi gula dan gorengan."
            exercise = "Olahraga teratur 3–5x/minggu (cardio ringan + kekuatan ringan)."
        elif bmi_status in ["Overweight", "Obesitas"]:
            system_recommendation = "Kelebihan berat badan. Direkomendasikan program diet seimbang dan peningkatan aktivitas fisik."
            deposit_calories = daily_calories - 400
            food = "Sayur, ikan, dada ayam tanpa kulit, oatmeal, apel, almond, yogurt rendah lemak"
            exercise = "Cardio teratur, latihan kekuatan, pengurangan asupan kalori." 
        else:
            system_recommendation = "Perlu konsultasi lebih detail dengan profesional kesehatan."
            deposit_calories = daily_calories

        # Rekomendasi olahraga
        exercise_map = {
            'None': 'Tidak Pernah Olahraga',
            'sedentary': 'Jalan kaki ringan, stretching',
            'light': 'Jogging, yoga, bersepeda santai',
            'moderate': 'Renang, gym, aerobik',
            'active': 'HIIT, lari, olahraga tim',
            'very_active': 'Crossfit, olahraga kompetitif'
        }
        exercise = exercise_map.get(activity, 'Jalan kaki ringan')

        # Rekomendasi makanan berdasarkan status BMI
        if bmi_status in ["Sangat Kurus", "Kurus"]:
            food = "Susu, telur, daging, roti gandum, selai kacang, alpukat, pisang"
        elif bmi_status in ["Overweight", "Obesitas"]:
            food = "Sayur, ikan, dada ayam, oatmeal, apel, almond, yogurt low-fat"
        else:
            food = "Menjaga porsi seimbang: karbohidrat, protein, serat, vitamin"

        # ---------------------------------------------------------
        # ✨ LOGIKA TAMBAHAN: Protein Harian
        # ---------------------------------------------------------
        protein_per_kg = 1.5
        protein_grams = round(weight * protein_per_kg, 1)  # default

        # Inisialisasi goal
        goal_calories = deposit_calories
        goal_food = food
        goal_exercise = exercise
        goal_protein = protein_grams

        # Match form option values: 'gain_weight', 'maintain_weight', 'lose_weight'
        if goal in ("gain_weight", "gain"):
            goal_calories = deposit_calories + 300
            goal_food = "Kalori tinggi sehat: daging, susu penuh lemak, kacang-kacangan, alpukat, pisang, nasi merah."
            goal_exercise = "Latihan angkat beban 3–4x/minggu dan fokus pada progresif overload."
            goal_protein = round(weight * 1.8, 1)

        elif goal in ("maintain_weight", "maintain"):
            goal_calories = deposit_calories
            goal_food = "Porsi seimbang: protein sedang, karbohidrat kompleks, banyak sayur dan buah, batasi gula olahan."
            goal_exercise = "Olahraga teratur 3–5x/minggu (kombinasi cardio & kekuatan)."
            goal_protein = protein_grams

        elif goal in ("lose_weight", "loss"):
            goal_calories = deposit_calories - 300
            goal_food = "Defisit kalori: dada ayam, ikan, brokoli, oatmeal, apel, yogurt rendah lemak."
            goal_exercise = "Cardio + latihan kekuatan 4–5x/minggu dengan defisit kalori moderat."
            goal_protein = round(weight * 1.2, 1)

        result = {
            'bmi': bmi,
            'bmi_status': bmi_status,
            'system_recommendation': system_recommendation,
            'daily_calories': daily_calories,
            'deposit_calories': deposit_calories,
            'exercise': exercise,
            'food': food,
            'protein': protein_grams,
            'goal_calories': goal_calories,
            'goal_food': goal_food,
            'goal_exercise': goal_exercise,
            'goal_protein': goal_protein
        }
        # Normalized goal key for templating (gain / maintain / lose)
        if goal in ('gain_weight', 'gain'):
            result['goal_key'] = 'gain'
        elif goal in ('maintain_weight', 'maintain'):
            result['goal_key'] = 'maintain'
        else:
            result['goal_key'] = 'lose'

    return render_template("dietplanner.html", result=result)


# ---------------------------------------------------------
# ROUTE: Logout
# ---------------------------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Anda telah logout.", 'info')
    return redirect(url_for('index'))

# ---------------------------------------------------------
# USER INFO (harus sebelum app.run)
# ---------------------------------------------------------
@app.route('/user_info')
def user_info():
    if 'username' not in session:
        return {"error": "Not logged in"}, 403

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT fullname, email, created_at
        FROM users
        WHERE username = %s
    """, (session['username'],))
    
    data = cursor.fetchone()
    return data


# ---------------------------------------------------------
# RUN SERVER
# ---------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)


