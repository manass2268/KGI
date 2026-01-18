import mysql.connector
from datetime import datetime

def connect_db(database=None):
    cfg = {"host": "localhost", "user": "root", "passwd": ""}
    if database:
        cfg["database"] = database
    return mysql.connector.connect(**cfg)

def create_databases_and_tables():
    con = connect_db()
    cur = con.cursor()
    # Create databases
    for db in ("school_students","school_marks","school_attendance","school_fees","school_class"):
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {db}")
    # Create students table (stu_id as primary key)
    cur.execute("USE school_students")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        stu_id VARCHAR(20) PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        class VARCHAR(10) NOT NULL,
        section VARCHAR(10) NOT NULL,
        phone VARCHAR(15),
        address VARCHAR(200),
        email VARCHAR(100),
        dob DATE
    ) ENGINE=InnoDB
    """)
    # Create marks table in separate DB referencing students(stu_id)
    cur.execute("USE school_marks")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS marks (
        id INT AUTO_INCREMENT PRIMARY KEY,
        stu_id VARCHAR(20) NOT NULL,
        subject VARCHAR(50) NOT NULL,
        marks DECIMAL(5,2) NOT NULL,
        exam_date DATE,
        FOREIGN KEY (stu_id) REFERENCES school_students.students(stu_id) ON DELETE CASCADE
    ) ENGINE=InnoDB
    """)
    # Attendance
    cur.execute("USE school_attendance")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INT AUTO_INCREMENT PRIMARY KEY,
        stu_id VARCHAR(20) NOT NULL,
        attendance_date DATE NOT NULL,
        status ENUM('Present','Absent','Late') NOT NULL,
        remarks VARCHAR(200),
        FOREIGN KEY (stu_id) REFERENCES school_students.students(stu_id) ON DELETE CASCADE
    ) ENGINE=InnoDB
    """)
    # Fees
    cur.execute("USE school_fees")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS fees (
        id INT AUTO_INCREMENT PRIMARY KEY,
        stu_id VARCHAR(20) NOT NULL,
        fee_type VARCHAR(50),
        amount DECIMAL(10,2),
        due_date DATE,
        payment_date DATE,
        status ENUM('Paid','Unpaid','Partial'),
        FOREIGN KEY (stu_id) REFERENCES school_students.students(stu_id) ON DELETE CASCADE
    ) ENGINE=InnoDB
    """)
    # Class data
    cur.execute("USE school_class")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS class_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        stu_id VARCHAR(20) NOT NULL,
        class_name VARCHAR(10),
        section VARCHAR(10),
        class_teacher VARCHAR(100),
        academic_year VARCHAR(9),
        FOREIGN KEY (stu_id) REFERENCES school_students.students(stu_id) ON DELETE CASCADE
    ) ENGINE=InnoDB
    """)
    con.commit()
    cur.close()
    con.close()

def generate_student_id():
    con = connect_db("school_students")
    cur = con.cursor()
    year = datetime.now().year
    prefix = f"GNPS{year}"
    cur.execute("SELECT stu_id FROM students WHERE stu_id LIKE %s ORDER BY stu_id DESC LIMIT 1", (prefix+"%",))
    last = cur.fetchone()
    if last:
        suffix = last[0].replace(prefix, "")
        try:
            last_num = int(suffix)
        except ValueError:
            last_num = 0
        new_num = last_num + 1
    else:
        new_num = 1
    stu_id = f"{prefix}{str(new_num).zfill(2)}"
    cur.close()
    con.close()
    return stu_id

def add_student(first_name, last_name, class_, section, phone=None, address=None, email=None, dob=None):
    stu_id = generate_student_id()
    con = connect_db("school_students")
    cur = con.cursor()
    cur.execute("""
        INSERT INTO students (stu_id, first_name, last_name, class, section, phone, address, email, dob)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (stu_id, first_name, last_name, class_, section, phone, address, email, dob))
    con.commit()
    cur.close()
    con.close()
    return stu_id

def add_mark(stu_id, subject, marks, exam_date=None):
    con = connect_db("school_marks")
    cur = con.cursor()
    cur.execute("INSERT INTO marks (stu_id, subject, marks, exam_date) VALUES (%s,%s,%s,%s)",
                (stu_id, subject, marks, exam_date))
    con.commit()
    cur.close()
    con.close()

def add_attendance(stu_id, attendance_date, status, remarks=None):
    con = connect_db("school_attendance")
    cur = con.cursor()
    cur.execute("INSERT INTO attendance (stu_id, attendance_date, status, remarks) VALUES (%s,%s,%s,%s)",
                (stu_id, attendance_date, status, remarks))
    con.commit()
    cur.close()
    con.close()

def add_fee(stu_id, fee_type, amount, due_date=None, payment_date=None, status="Unpaid"):
    con = connect_db("school_fees")
    cur = con.cursor()
    cur.execute("INSERT INTO fees (stu_id, fee_type, amount, due_date, payment_date, status) VALUES (%s,%s,%s,%s,%s,%s)",
                (stu_id, fee_type, amount, due_date, payment_date, status))
    con.commit()
    cur.close()
    con.close()

def add_class_data(stu_id, class_name, section, class_teacher=None, academic_year=None):
    con = connect_db("school_class")
    cur = con.cursor()
    cur.execute("INSERT INTO class_data (stu_id, class_name, section, class_teacher, academic_year) VALUES (%s,%s,%s,%s,%s)",
                (stu_id, class_name, section, class_teacher, academic_year))
    con.commit()
    cur.close()
    con.close()

if __name__ == "__main__":
    # setup databases and tables
    create_databases_and_tables()

    # Manually enter sample data
    # Add a student
    stu = add_student("Amit", "Sharma", "10", "A", phone="9999999999", address="Delhi", email="amit@example.com", dob="2008-05-12")
    print("Inserted student:", stu)

    # Add related records using same stu_id
    add_mark(stu, "Maths", 88.5, exam_date="2025-03-15")
    add_mark(stu, "English", 76.0, exam_date="2025-03-15")
    add_attendance(stu, "2025-09-01", "Present")
    add_fee(stu, "Tuition", 1500.00, due_date="2025-04-01", status="Unpaid")
    add_class_data(stu, "10", "A", class_teacher="Mrs. Verma", academic_year="2025-2026")
    print("Related records inserted for", stu)