import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
import MySQLdb
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv

# Gemini API (google-generativeai)
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# --- Inisialisasi Flask ---
app = Flask(__name__)
app.secret_key = 'dietplanner-secret-key'

# Load .env for Gemini API key
load_dotenv()
# Gemini API key setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "ISI_API_KEY_GEMINI")
if genai and GEMINI_API_KEY and GEMINI_API_KEY != "ISI_API_KEY_GEMINI":
    genai.configure(api_key=GEMINI_API_KEY)

# Endpoint untuk menampilkan daftar model Gemini yang tersedia
@app.route('/api/list_models', methods=['GET'])
def list_gemini_models():
    if not genai:
        return jsonify({'error': 'google-generativeai library not installed'}), 500
    if not GEMINI_API_KEY or GEMINI_API_KEY == "ISI_API_KEY_GEMINI":
        return jsonify({'error': 'Gemini API key not set'}), 500
    try:
        models = []
        for m in genai.list_models():
            models.append({
                'name': getattr(m, 'name', str(m)),
                'description': getattr(m, 'description', ''),
                'supported_methods': getattr(m, 'supported_generation_methods', [])
            })
        return jsonify({'models': models})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

app = Flask(__name__)
app.secret_key = 'dietplanner-secret-key'

# Load .env for Gemini API key
load_dotenv()
# Gemini API key setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "ISI_API_KEY_GEMINI")
if genai and GEMINI_API_KEY and GEMINI_API_KEY != "ISI_API_KEY_GEMINI":
    genai.configure(api_key=GEMINI_API_KEY)
# ---------------------------------------------------------
# ROUTE: Gemini Chatbot API
# ---------------------------------------------------------
@app.route('/api/chatbot', methods=['POST'])
def api_chatbot():
    if not genai:
        return jsonify({'error': 'google-generativeai library not installed'}), 500
    if not GEMINI_API_KEY or GEMINI_API_KEY == "ISI_API_KEY_GEMINI":
        return jsonify({'error': 'Gemini API key not set'}), 500
    data = request.get_json()
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': 'Pertanyaan kosong'}), 400
    # Restrict chatbot to diet planner topics only
    system_instruction = (
        "Anda adalah asisten diet planner. Jawab hanya pertanyaan seputar diet, nutrisi, pola makan sehat, fitur aplikasi dietplanner, dan kesehatan terkait makanan. "
        "Jika pertanyaan di luar topik diet, nutrisi, atau aplikasi dietplanner, jawab dengan sopan: 'Maaf, saya hanya dapat membantu pertanyaan seputar diet, nutrisi, dan fitur aplikasi dietplanner.'"
    )
    full_prompt = f"{system_instruction}\n\nPertanyaan pengguna: {question}"
    try:
        # Gunakan model Gemini versi terbaru yang valid
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        response = model.generate_content(full_prompt)
        answer = response.text if hasattr(response, 'text') else str(response)
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Konfigurasi MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '' 
app.config['MYSQL_DB'] = 'dietplanner'

mysql = MySQL(app)

# Pastikan tabel progress_history ada
def create_progress_table():
    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS progress_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                bmi FLOAT,
                daily_calories INT,
                goal_key VARCHAR(32),
                goal_calories INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB;
            """
        )
        mysql.connection.commit()
    finally:
        try:
            cursor.close()
        except Exception:
            pass

# Pastikan tabel food_log ada
def create_foodlog_table():
    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS food_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                food_name VARCHAR(100),
                calories INT,
                log_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB;
            """
        )
        mysql.connection.commit()
    finally:
        try:
            cursor.close()
        except Exception:
            pass

# Pastikan tabel users ada (jika belum dibuat oleh migrasi lain)
def create_users_table():
    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fullname VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                username VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;
            """
        )
        mysql.connection.commit()
    finally:
        try:
            cursor.close()
        except Exception:
            pass


# -------------------------
# Validation helpers
# -------------------------
def is_valid_email(email: str) -> bool:
    if not email:
        return False
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) is not None

def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default

def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default
# Panggil pembuatan tabel sekali saat aplikasi start (jika koneksi tersedia)
with app.app_context():
    try:
        # Ensure users table exists before progress_history which references it
        create_users_table()
        create_progress_table()
        create_foodlog_table()
    except Exception:
        # jika DB belum siap atau tidak terhubung saat import, lewati - akan dibuat saat runtime
        pass

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

        if not login_input or not password_input:
            flash('Email/username dan password wajib diisi.', 'error')
            return render_template('login.html')

        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                'SELECT * FROM users WHERE email = %s OR username = %s',
                (login_input, login_input)
            )
            user = cursor.fetchone()
        except MySQLdb.Error as e:
            app.logger.error('DB error on login: %s', e)
            flash('Terjadi kesalahan server. Coba lagi nanti.', 'error')
            user = None
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

        # Basic validation
        if not fullname or not email or not username or not password:
            flash('Semua field wajib diisi.', 'error')
            return render_template('signup.html')
        if not is_valid_email(email):
            flash('Format email tidak valid.', 'error')
            return render_template('signup.html')
        if password != confirm_password:
            flash('Password dan konfirmasi tidak sama.', 'error')
            return render_template('signup.html')

        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
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
                except MySQLdb.Error as e:
                    app.logger.error('DB error on signup insert: %s', e)
                    flash('Terjadi kesalahan pada database. Coba lagi nanti.', 'error')
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
        if not username:
            flash('Masukkan username atau email untuk reset password.', 'error')
            return render_template('resetpassword.html')
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
        weight = safe_float(request.form.get('weight'))
        height = safe_float(request.form.get('height'))
        age = safe_int(request.form.get('age'))
        gender = request.form.get('gender')
        activity = request.form.get('activity')
        goal = request.form.get('goal')

        # Basic input validation
        if weight <= 0 or height <= 0 or age <= 0:
            flash('Masukkan nilai berat, tinggi, dan umur yang valid.', 'error')
            return render_template('dietplanner.html', result=None)

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

        # Simpan ke tabel history jika user login
        try:
            if session.get('id'):
                cursor = mysql.connection.cursor()
                try:
                    cursor.execute(
                        "INSERT INTO progress_history (user_id, bmi, daily_calories, goal_key, goal_calories) VALUES (%s, %s, %s, %s, %s)",
                        (session.get('id'), bmi, daily_calories, result.get('goal_key'), int(result.get('goal_calories')))
                    )
                    mysql.connection.commit()
                finally:
                    try:
                        cursor.close()
                    except Exception:
                        pass
        except Exception as e:
            app.logger.error('Gagal menyimpan history: %s', e)
            # do not expose DB errors to users
            flash('Gagal menyimpan riwayat. Lanjutkan tanpa menyimpan.', 'warning')

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
    try:
        cursor.execute("""
            SELECT id, fullname, email, created_at
            FROM users
            WHERE username = %s
        """, (session['username'],))
        user = cursor.fetchone()

        if not user:
            return {"error": "User not found"}, 404

        # try to fetch latest progress for this user
        cursor.execute(
            "SELECT bmi, daily_calories, goal_key, goal_calories, created_at "
            "FROM progress_history WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
            (user['id'],),
        )
        latest = cursor.fetchone()

        data = {
            'fullname': user.get('fullname'),
            'email': user.get('email'),
            'created_at': user.get('created_at')
        }

        if latest:
            data.update({
                'bmi': latest.get('bmi'),
                'daily_calories': latest.get('daily_calories'),
                'goal_calories': latest.get('goal_calories'),
                'goal_key': latest.get('goal_key'),
                'latest_at': latest.get('created_at')
            })

            # compute a simple progress percent (how close daily_calories is to goal_calories)
            try:
                gc = float(latest.get('goal_calories') or 0)
                dc = float(latest.get('daily_calories') or 0)
                if gc > 0 and dc > 0:
                    ratio = min(dc, gc) / max(dc, gc)
                    pct = int(ratio * 100)
                    data['progress_percent'] = pct
                else:
                    data['progress_percent'] = None
            except Exception:
                data['progress_percent'] = None

        return data
    finally:
        try:
            cursor.close()
        except Exception:
            pass


# ---------------------------------------------------------
# ROUTE: History (user-specific)
@app.route('/food_log', methods=['GET', 'POST'])
def food_log():
    if not session.get('loggedin'):
        flash('Silakan login untuk mengakses food log.', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        food_name = request.form.get('food_name', '').strip()
        calories = request.form.get('calories', '').strip()
        log_date = request.form.get('log_date', '').strip()
        if not food_name or not calories or not log_date:
            flash('Semua field wajib diisi.', 'error')
        else:
            try:
                cursor = mysql.connection.cursor()
                cursor.execute(
                    "INSERT INTO food_log (user_id, food_name, calories, log_date) VALUES (%s, %s, %s, %s)",
                    (session.get('id'), food_name, int(calories), log_date)
                )
                mysql.connection.commit()
                flash('Log makanan berhasil disimpan.', 'success')
            except Exception as e:
                app.logger.error('Gagal simpan food log: %s', e)
                flash('Gagal menyimpan log makanan.', 'error')
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
        return redirect(url_for('food_log'))
    # GET: tampilkan log makanan user
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute(
            "SELECT id, food_name, calories, log_date FROM food_log WHERE user_id = %s ORDER BY log_date DESC, id DESC LIMIT 100",
            (session.get('id'),)
        )
        logs = cursor.fetchall()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
    return render_template('food_log.html', logs=logs)

# ROUTE: Delete food log entry
@app.route('/delete_food_log/<int:log_id>', methods=['POST'])
def delete_food_log(log_id):
    if not session.get('loggedin'):
        flash('Silakan login untuk menghapus log makanan.', 'error')
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            'DELETE FROM food_log WHERE id = %s AND user_id = %s',
            (log_id, session.get('id'))
        )
        mysql.connection.commit()
        flash('Log makanan berhasil dihapus.', 'success')
    except Exception as e:
        app.logger.error('Gagal hapus food log: %s', e)
        flash('Gagal menghapus log makanan.', 'error')
    finally:
        try:
            cursor.close()
        except Exception:
            pass
    return redirect(url_for('food_log'))


# ROUTE: Update food log entry
@app.route('/update_food_log/<int:log_id>', methods=['POST'])
def update_food_log(log_id):
    if not session.get('loggedin'):
        flash('Silakan login untuk mengubah log makanan.', 'error')
        return redirect(url_for('login'))

    food_name = request.form.get('food_name', '').strip()
    calories = request.form.get('calories', '').strip()
    log_date = request.form.get('log_date', '').strip()

    if not food_name or not calories or not log_date:
        flash('Semua field wajib diisi untuk memperbarui log.', 'error')
        return redirect(url_for('food_log'))

    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            'UPDATE food_log SET food_name = %s, calories = %s, log_date = %s WHERE id = %s AND user_id = %s',
            (food_name, int(calories), log_date, log_id, session.get('id'))
        )
        mysql.connection.commit()
        # cursor.rowcount tidak selalu tersedia tergantung driver, cek dengan safety
        try:
            updated = cursor.rowcount
        except Exception:
            updated = 1

        if updated:
            flash('Log makanan berhasil diperbarui.', 'success')
        else:
            flash('Tidak ditemukan log atau Anda tidak punya izin untuk mengubahnya.', 'error')
    except Exception as e:
        app.logger.error('Gagal memperbarui food log: %s', e)
        flash('Gagal memperbarui log makanan.', 'error')
    finally:
        try:
            cursor.close()
        except Exception:
            pass

    return redirect(url_for('food_log'))
# ---------------------------------------------------------
@app.route('/history')
def history():
    if not session.get('loggedin'):
        flash('Silakan login untuk melihat riwayat Anda.', 'error')
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute(
            'SELECT id, bmi, daily_calories, goal_key, goal_calories, created_at FROM progress_history WHERE user_id = %s ORDER BY created_at DESC LIMIT 200',
            (session.get('id'),)
        )
        rows = cursor.fetchall()
    finally:
        try:
            cursor.close()
        except Exception:
            pass

    # enhance rows with human-friendly label and progress percent
    for r in rows:
        key = r.get('goal_key')
        if key == 'gain':
            r['goal_label'] = 'Menaikkan'
        elif key == 'maintain':
            r['goal_label'] = 'Mempertahankan'
        elif key == 'lose':
            r['goal_label'] = 'Menurunkan'
        else:
            r['goal_label'] = key or ''

        try:
            gc = float(r.get('goal_calories') or 0)
            dc = float(r.get('daily_calories') or 0)
            if gc > 0 and dc > 0:
                ratio = min(dc, gc) / max(dc, gc)
                r['progress_percent'] = int(ratio * 100)
            else:
                r['progress_percent'] = None
        except Exception:
            r['progress_percent'] = None

    return render_template('history.html', rows=rows)

# ROUTE: Delete history entry
@app.route('/delete_history/<int:history_id>', methods=['POST'])
def delete_history(history_id):
    if not session.get('loggedin'):
        flash('Silakan login untuk menghapus riwayat.', 'error')
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            'DELETE FROM progress_history WHERE id = %s AND user_id = %s',
            (history_id, session.get('id'))
        )
        mysql.connection.commit()
        flash('Riwayat berhasil dihapus.', 'success')
    except Exception as e:
        app.logger.error('Gagal hapus riwayat: %s', e)
        flash('Gagal menghapus riwayat.', 'error')
    finally:
        try:
            cursor.close()
        except Exception:
            pass
    return redirect(url_for('history'))


# ---------------------------------------------------------
# RUN SERVER

# Error demo route for testing error handling
@app.route('/error-demo')
def error_demo():
    # This will trigger a 500 error for demonstration
    raise Exception('Contoh error: error handling berhasil!')
# ---------------------------------------------------------


# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404, title='Halaman Tidak Ditemukan', message='Halaman yang Anda minta tidak ditemukan.'), 404


@app.errorhandler(500)
def server_error(e):
    app.logger.error('Internal server error: %s', e)
    return render_template('error.html', code=500, title='Kesalahan Server', message='Terjadi kesalahan pada server. Coba lagi nanti.'), 500


@app.errorhandler(HTTPException)
def handle_http_exception(e):
    # Generic handler for HTTPExceptions
    return render_template('error.html', code=e.code or 500, title=e.name, message=e.description), e.code or 500

if __name__ == '__main__':
    app.run(debug=True)


