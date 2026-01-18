import mysql.connector
from datetime import datetime
import os

#==============================DATABASE SETUP=================================
def connect_db(database=None):
    print("Connecting to database...")
    con=mysql.connector.connect(host="localhost",user="root",passwd="")
    cur=con.cursor()
    cur.execute("""
    CREATE DATABASE IF NOT EXISTS KGI_Management_System
    """)
    cur.close()
    con.close()

    print("Connected.")
    cfg = {"host": "localhost", "user": "root", "passwd": ""}
    if database:
        cfg["database"] = database
        print(f"Connecting to database: {database}")
    return mysql.connector.connect(**cfg)

print("Database connection function defined.")

#==============================DATABASE AND TABLE CREATION=================================
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
        password VARCHAR(100) NOT NULL,
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
    con.commit()
    cur.close()
    con.close()
    print("Databases and tables created successfully!")

# Call the function to create databases and tables
if __name__ == "__main__":
    create_databases_and_tables()