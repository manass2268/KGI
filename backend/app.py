import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import datetime
  # To check for SSL certificate file

app = Flask(__name__)
CORS(app)

# --- AIVEN CLOUD CONFIGURATION ---
# Yahan apni Aiven details bharein
DB_HOST = "kgi-erp-db-kgikanpur.i.aivencloud.com"  # Aiven Host Address
DB_PORT = 28446                                  # Aiven Port (Number only)
DB_USER = "avnadmin"                             # Aiven User
DB_PASS = os.getenv("DB_PASS")             # Aiven Password
DB_NAME = "defaultdb"                            # Aiven Database Name
SSL_CERT = "C:\Users\manas\OneDrive\Desktop\School Managemnt  (KGI)\\backend\ca certificate.pem"                              # CA Certificate File Name

# --- 1. AUTO DATABASE & TABLE SETUP ---
def init_db():
    print("--- SYSTEM CHECKING AIVEN DATABASE ---")
    
    # Check if CA Certificate exists
    if not os.path.exists(SSL_CERT):
        print(f"❌ ERROR: '{SSL_CERT}' file nahi mili! Ise folder mein rakhein.")
        return

    try:
        # Connect to Aiven
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            ssl_ca=SSL_CERT,     # SSL Certificate Path
            ssl_disabled=False   # Enforce SSL
        )
        cursor = conn.cursor()
        
        # Note: Aiven par DB pehle se bana hota hai ('defaultdb'), so we directly create tables.
        
        # 1. Students Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                roll_no VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                password VARCHAR(100) NOT NULL,
                course VARCHAR(50),
                branch VARCHAR(50),
                semester VARCHAR(10),
                section VARCHAR(10),
                mobile VARCHAR(15),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Employees Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INT AUTO_INCREMENT PRIMARY KEY,
                emp_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                password VARCHAR(100) NOT NULL,
                designation VARCHAR(100),
                department VARCHAR(100),
                mobile VARCHAR(15),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. System Settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INT PRIMARY KEY,
                show_results TINYINT(1) DEFAULT 1,
                show_fees TINYINT(1) DEFAULT 1,
                allow_reg TINYINT(1) DEFAULT 1,
                maintenance TINYINT(1) DEFAULT 0,
                message TEXT
            )
        """)
        # Check if settings exist, if not insert default
        cursor.execute("SELECT count(*) FROM system_settings")
        if cursor.fetchone()[0] == 0:
             cursor.execute("INSERT INTO system_settings (id, show_results, show_fees, allow_reg, maintenance, message) VALUES (1, 1, 1, 1, 0, '')")

        # 4. Attendance Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                roll_no VARCHAR(50),
                student_name VARCHAR(100),
                subject VARCHAR(100),
                branch VARCHAR(50),
                status VARCHAR(10), 
                date DATE,
                marked_by VARCHAR(50)
            )
        """)

        # 5. Timetable Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timetable (
                id INT AUTO_INCREMENT PRIMARY KEY,
                emp_id VARCHAR(50),
                day VARCHAR(20),
                time_slot VARCHAR(50),
                subject VARCHAR(100),
                branch VARCHAR(50),
                room VARCHAR(20)
            )
        """)

        # 6. Admissions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admissions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fullname VARCHAR(100),
                fathername VARCHAR(100),
                email VARCHAR(100),
                mobile VARCHAR(15),
                course VARCHAR(50),
                address TEXT,
                apply_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        print("✔ Aiven Database Connected & Tables Ready.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ AIVEN CONNECTION ERROR: {e}")
        print("Tip: Check Host, Port, Password and make sure 'ca.pem' is in the folder.")

# Helper to get connection
def get_db():
    try:
        return mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            ssl_ca=SSL_CERT,
            ssl_disabled=False
        )
    except Exception as e:
        print(f"⚠️ Connection Failed: {e}")
        return None

# --- API ROUTES ---

# --- ADMISSION PORTAL ---
@app.route('/api/admission/apply', methods=['POST'])
def apply_admission():
    data = request.json
    conn = get_db()
    if not conn: return jsonify({"status": "error", "message": "Database disconnected. Check Server."})
    
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO admissions (fullname, fathername, email, mobile, course, address) VALUES (%s, %s, %s, %s, %s, %s)"
        val = (data['fullname'], data['fathername'], data['email'], data['mobile'], data['course'], data['address'])
        cursor.execute(sql, val)
        conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    finally:
        conn.close()

@app.route('/api/admissions', methods=['GET'])
def get_admissions():
    conn = get_db()
    if not conn: 
        print("Error: Could not connect to DB for Admissions")
        return jsonify([]) 

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admissions ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route('/api/admission/delete', methods=['POST'])
def delete_admission():
    data = request.json
    conn = get_db()
    if not conn: return jsonify({"status": "error", "message": "Database disconnected"})

    cursor = conn.cursor()
    cursor.execute("DELETE FROM admissions WHERE id = %s", (data['id'],))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})


# --- CONFIGURATION ---
@app.route('/api/config', methods=['GET'])
def get_config():
    conn = get_db()
    if not conn: return jsonify({"showResults": True, "showFees": True, "allowReg": True, "maintenance": False, "message": "DB Error"})
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM system_settings WHERE id=1")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify({
            "showResults": bool(row['show_results']),
            "showFees": bool(row['show_fees']),
            "allowReg": bool(row['allow_reg']),
            "maintenance": bool(row['maintenance']),
            "message": row['message']
        })
    return jsonify({}) # Fallback

@app.route('/api/config/update', methods=['POST'])
def update_config():
    data = request.json
    conn = get_db()
    if not conn: return jsonify({"status": "error", "message": "DB Error"})

    cursor = conn.cursor()
    sql = "UPDATE system_settings SET show_results=%s, show_fees=%s, allow_reg=%s, maintenance=%s, message=%s WHERE id=1"
    val = (data['showResults'], data['showFees'], data['allowReg'], data['maintenance'], data['message'])
    cursor.execute(sql, val)
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

# --- READ DATA (Students/Employees) ---
@app.route('/api', methods=['GET'])
def read_data():
    conn = get_db()
    if not conn: 
        print("Error: Could not connect to DB for Read Data")
        return jsonify([])

    cursor = conn.cursor(dictionary=True)
    table = "students" if request.args.get('type') == 'student' else "employees"
    cursor.execute(f"SELECT * FROM {table} ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

# --- SAVE DATA ---
@app.route('/api/save', methods=['POST'])
def save_data():
    conn = get_db()
    if not conn: return jsonify({"status":"error", "message":"DB Connection Failed"})
    
    try:
        data = request.json
        cursor = conn.cursor()

        if data['type'] == 'student':
            if data['isEdit']:
                sql = "UPDATE students SET name=%s, roll_no=%s, password=%s, mobile=%s, course=%s, branch=%s, semester=%s, section=%s WHERE roll_no=%s"
                val = (data['name'], data['id'], data['pass'], data['mobile'], data.get('course'), data.get('branch'), data.get('sem'), data.get('sec'), data['oldId'])
            else:
                cursor.execute("SELECT * FROM students WHERE roll_no=%s", (data['id'],))
                if cursor.fetchone(): return jsonify({"status":"error", "message":"Roll No Exists"})
                sql = "INSERT INTO students (name, roll_no, password, mobile, course, branch, semester, section) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                val = (data['name'], data['id'], data['pass'], data['mobile'], data.get('course'), data.get('branch'), data.get('sem'), data.get('sec'))
        
        elif data['type'] == 'employee':
            if data['isEdit']:
                sql = "UPDATE employees SET name=%s, emp_id=%s, password=%s, mobile=%s, designation=%s, department=%s WHERE emp_id=%s"
                val = (data['name'], data['id'], data['pass'], data['mobile'], data.get('desig'), data.get('dept'), data['oldId'])
            else:
                cursor.execute("SELECT * FROM employees WHERE emp_id=%s", (data['id'],))
                if cursor.fetchone(): return jsonify({"status":"error", "message":"Emp ID Exists"})
                sql = "INSERT INTO employees (name, emp_id, password, mobile, designation, department) VALUES (%s, %s, %s, %s, %s, %s)"
                val = (data['name'], data['id'], data['pass'], data['mobile'], data.get('desig'), data.get('dept'))
        
        cursor.execute(sql, val)
        conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    finally:
        if conn: conn.close()

@app.route('/api/delete', methods=['POST'])
def delete_data():
    data = request.json
    conn = get_db()
    if not conn: return jsonify({"status": "error", "message": "DB Error"})
    
    cursor = conn.cursor()
    table = "students" if data['type'] == 'student' else "employees"
    col = "roll_no" if data['type'] == 'student' else "emp_id"
    cursor.execute(f"DELETE FROM {table} WHERE {col} = %s", (data['id'],))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

# --- ATTENDANCE & TIMETABLE ---
@app.route('/api/attendance/save', methods=['POST'])
def save_attendance():
    data = request.json
    conn = get_db()
    if not conn: return jsonify({"status": "error", "message": "DB Error"})
    
    cursor = conn.cursor()
    try:
        today = datetime.date.today()
        cursor.execute("DELETE FROM attendance WHERE subject=%s AND branch=%s AND date=%s", 
                       (data[0]['subject'], data[0]['branch'], today))
        sql = "INSERT INTO attendance (roll_no, student_name, subject, branch, status, date, marked_by) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        values = [(r['roll_no'], r['name'], r['subject'], r['branch'], r['status'], today, r['teacher']) for r in data]
        cursor.executemany(sql, values)
        conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    finally:
        conn.close()

@app.route('/api/timetable', methods=['GET'])
def get_timetable():
    emp_id = request.args.get('emp_id')
    conn = get_db()
    if not conn: return jsonify([])

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM timetable WHERE emp_id=%s ORDER BY day, time_slot", (emp_id,))
    rows = cursor.fetchall()
    
    if not rows:
        dummy = [
            (emp_id, 'Monday', '10:00 AM - 11:00 AM', 'Data Structures', 'CSE', 'LH-101'),
            (emp_id, 'Monday', '02:00 PM - 03:00 PM', 'Python Lab', 'CSE', 'LAB-1'),
            (emp_id, 'Wednesday', '09:00 AM - 10:00 AM', 'Operating Sys', 'IT', 'LH-205'),
            (emp_id, 'Friday', '11:00 AM - 12:00 PM', 'Project Review', 'CSE', 'Conf Room')
        ]
        cursor.executemany("INSERT INTO timetable (emp_id, day, time_slot, subject, branch, room) VALUES (%s, %s, %s, %s, %s, %s)", dummy)
        conn.commit()
        cursor.execute("SELECT * FROM timetable WHERE emp_id=%s ORDER BY day", (emp_id,))
        rows = cursor.fetchall()

    conn.close()
    return jsonify(rows)

if __name__ == '__main__':
    init_db()
    # Note: Use port 5000 locally. On Render/Cloud, it uses Environment Port.
    app.run(debug=True, port=5000)