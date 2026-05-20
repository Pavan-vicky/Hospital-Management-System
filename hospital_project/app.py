from flask import Flask, render_template, request, session, redirect, jsonify, send_file
import mysql.connector
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "hospital_secret_key"

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="pavanlakshmi8901234",
        database="hospital_db",
        port=3307
    )

# ---------------- LOGIN ----------------

@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/login_check', methods=['POST'])
def login_check():
    db = get_db()
    cursor = db.cursor()

    username = request.form['username']
    password = request.form['password']

    cursor.execute(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (username, password)
    )
    user = cursor.fetchone()

    db.close()

    if user:
        session['user'] = username
        return redirect('/')
    else:
        return render_template('login.html', error="Invalid Username or Password")


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')


# ---------------- DASHBOARD ----------------

@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM patients")
    patients = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM doctors")
    doctors = cursor.fetchone()[0]

    db.close()

    return render_template('index.html', patients=patients, doctors=doctors)


# ---------------- PATIENTS ----------------

@app.route('/patients')
def show_patients():
    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM patients")
    data = cursor.fetchall()
    db.close()

    return render_template('patients.html', patients=data)


@app.route('/add_patient', methods=['POST'])
def add_patient():
    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    name = request.form['name']
    age = request.form['age']
    gender = request.form['gender']

    cursor.execute(
        "INSERT INTO patients (name, age, gender) VALUES (%s, %s, %s)",
        (name, age, gender)
    )

    db.commit()
    db.close()

    return redirect('/patients')


@app.route('/delete_patient/<int:id>')
def delete_patient(id):
    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM patients WHERE patient_id=%s", (id,))
    db.commit()
    db.close()

    return redirect('/patients')


@app.route('/edit_patient/<int:id>')
def edit_patient(id):
    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM patients WHERE patient_id=%s", (id,))
    data = cursor.fetchone()
    db.close()

    return render_template("edit.html", patient=data)


@app.route('/update_patient/<int:id>', methods=['POST'])
def update_patient(id):
    if 'user' not in session:
        return redirect('/login')

    name = request.form['name']
    age = request.form['age']
    gender = request.form['gender']

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE patients
        SET name=%s, age=%s, gender=%s
        WHERE patient_id=%s
    """, (name, age, gender, id))

    db.commit()
    db.close()

    return redirect('/patients')


# ---------------- DOCTORS ----------------

@app.route('/doctors')
def show_doctors():
    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM doctors")
    data = cursor.fetchall()
    db.close()

    return render_template('doctors.html', doctors=data)


@app.route('/add_doctor', methods=['POST'])
def add_doctor():
    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    name = request.form['name']
    specialization = request.form['specialization']
    phone = request.form['phone']

    cursor.execute(
        "INSERT INTO doctors (name, specialization, phone) VALUES (%s, %s, %s)",
        (name, specialization, phone)
    )

    db.commit()
    db.close()

    return redirect('/doctors')


# ---------------- APPOINTMENTS ----------------

@app.route('/appointments')
def appointments():
    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT patient_id, name FROM patients")
    patients = cursor.fetchall()

    cursor.execute("SELECT doctor_id, name FROM doctors")
    doctors = cursor.fetchall()

    cursor.execute("""
        SELECT a.appointment_id, p.name, d.name, a.appointment_date, a.reason
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
    """)

    data = cursor.fetchall()
    db.close()

    return render_template("appointments.html",
                           patients=patients,
                           doctors=doctors,
                           appointments=data)


@app.route('/add_appointment', methods=['POST'])
def add_appointment():
    if 'user' not in session:
        return redirect('/login')

    patient_id = request.form['patient_id']
    doctor_id = request.form['doctor_id']
    date = request.form['date']
    reason = request.form['reason']

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO appointments (patient_id, doctor_id, appointment_date, reason)
        VALUES (%s, %s, %s, %s)
    """, (patient_id, doctor_id, date, reason))

    db.commit()
    db.close()

    return redirect('/appointments')


@app.route('/delete_appointment/<int:id>')
def delete_appointment(id):
    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM appointments WHERE appointment_id=%s", (id,))
    db.commit()
    db.close()

    return redirect('/appointments')


# ---------------- BILLING ----------------

@app.route('/billing')
def billing():
    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT patient_id, name FROM patients")
    patients = cursor.fetchall()

    cursor.execute("""
        SELECT b.bill_id, p.name, b.total_amount, b.payment_status
        FROM billing b
        JOIN patients p ON b.patient_id = p.patient_id
    """)

    bills = cursor.fetchall()
    db.close()

    return render_template('billing.html', patients=patients, bills=bills)


@app.route('/add_bill', methods=['POST'])
def add_bill():
    if 'user' not in session:
        return redirect('/login')

    patient_id = request.form['patient_id']
    amount = request.form['amount']
    status = request.form['status']

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO billing (patient_id, total_amount, payment_status)
        VALUES (%s, %s, %s)
    """, (patient_id, amount, status))

    db.commit()
    db.close()

    return redirect('/billing')


@app.route('/delete_bill/<int:id>')
def delete_bill(id):
    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM billing WHERE bill_id=%s", (id,))
    db.commit()
    db.close()

    return redirect('/billing')


# ✅ DOWNLOAD BILL
@app.route('/download_bill/<int:id>')
def download_bill(id):

    if 'user' not in session:
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT b.bill_id, p.name, b.total_amount, 
               b.payment_status, b.bill_date
        FROM billing b
        JOIN patients p ON b.patient_id = p.patient_id
        WHERE b.bill_id=%s
    """, (id,))

    bill = cursor.fetchone()
    db.close()

    if not bill:
        return "Bill not found"

    file_path = f"bill_{id}.pdf"

    c = canvas.Canvas(file_path)

    # ✅ OUTER BORDER
    c.rect(40, 40, 520, 760)

    # ✅ HOSPITAL NAME
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(300, 770, "NATURAL CARE")

    # ✅ SUBTITLE
    c.setFont("Times-Roman", 14)
    c.drawCentredString(300, 745, "Multi Speciality Hospital")

    # ✅ ADDRESS
    c.setFont("Times-Roman", 11)
    c.drawCentredString(
        300,
        725,
        "Bangalore | Phone: 9876543210 | Email: naturalcare@gmail.com"
    )

    # ✅ LINE
    c.line(60, 710, 540, 710)

    # ✅ BILL TITLE
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(300, 680, "HOSPITAL BILL RECEIPT")

    # ✅ BILL DETAILS
    c.setFont("Times-Roman", 14)

    c.drawString(80, 620, f"Bill ID")
    c.drawString(220, 620, f": {bill[0]}")

    c.drawString(80, 580, f"Patient Name")
    c.drawString(220, 580, f": {bill[1]}")

    c.drawString(80, 540, f"Total Amount")
    c.drawString(220, 540, f": ₹ {bill[2]}")

    c.drawString(80, 500, f"Payment Status")
    c.drawString(220, 500, f": {bill[3]}")

    c.drawString(80, 460, f"Bill Date")
    c.drawString(220, 460, f": {bill[4]}")

    # ✅ LINE
    c.line(60, 420, 540, 420)

    # ✅ THANK YOU MESSAGE
    c.setFont("Helvetica-Oblique", 13)
    c.drawCentredString(
        300,
        380,
        "Thank You For Choosing Natural Care Hospital"
    )

    # ✅ SIGNATURE
    c.setFont("Times-Roman", 12)
    c.drawString(400, 180, "Authorized Signature")

    c.line(390, 200, 520, 200)

    # ✅ FOOTER
    c.setFont("Times-Italic", 10)
    c.drawCentredString(
        300,
        80,
        "Get Well Soon • Stay Healthy"
    )

    c.save()

    return send_file(file_path, as_attachment=True)


# ✅ ADD REVIEW
@app.route('/add_review', methods=['POST'])
def add_review():

    if 'user' not in session:
        return redirect('/login')

    name = request.form.get('name')
    review = request.form.get('review')
    rating = request.form.get('rating')

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO reviews (name, review, rating) VALUES (%s, %s, %s)",
        (name, review, rating)
    )

    db.commit()
    db.close()

    return redirect('/')


# ✅ VLOG PAGE
@app.route('/vlog')
def vlog():

    if 'user' not in session:
        return redirect('/login')

    return render_template('vlog.html')


# ✅ EMERGENCY PAGE
@app.route('/emergency')
def emergency():

    if 'user' not in session:
        return redirect('/login')

    return render_template('emergency.html')


# ✅ REQUEST AMBULANCE
@app.route('/request_ambulance', methods=['POST'])
def request_ambulance():

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO emergency_requests(type) VALUES(%s)",
        ('ambulance',)
    )

    db.commit()
    db.close()

    return "🚑 Ambulance is on the way!"


# ✅ SEND LOCATION
@app.route('/send_location', methods=['POST'])
def send_location():

    data = request.get_json()

    lat = data.get("lat")
    lng = data.get("lng")

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO emergency_requests(type, latitude, longitude)
        VALUES(%s,%s,%s)
    """, ('location', lat, lng))

    db.commit()
    db.close()

    return "📍 Location sent successfully!"


# ---------------- RUN ----------------

if __name__ == '__main__':
    app.run(debug=True)