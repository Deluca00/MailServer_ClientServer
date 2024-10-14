import mysql.connector

def connect_db():
    return mysql.connector.connect(
        host="localhost",  # Thay 'localhost' bằng địa chỉ IP của MySQL nếu cần
        user="root",  # Tài khoản MySQL của bạn
        password="090104",  # Mật khẩu MySQL của bạn
        database="MailServer",  # Tên cơ sở dữ liệu
        port=3306  # Thêm cổng MySQL (mặc định là 3306)
    )

def create_user_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def create_email_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sender_email VARCHAR(255) NOT NULL,
            receiver_email VARCHAR(255) NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            content TEXT NOT NULL,
            sender_ip VARCHAR(45) NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
def create_user_status_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_status (
            username VARCHAR(255) PRIMARY KEY,
            status VARCHAR(10) NOT NULL DEFAULT 'offline'
        )
    ''')
    conn.commit()
    conn.close()

create_user_table()
create_email_table()
create_user_status_table()
