import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="tiger",   # your MySQL password
        database="academic_portal"
    )
