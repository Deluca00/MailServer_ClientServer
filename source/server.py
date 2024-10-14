import mysql.connector
import socket
import threading
import hashlib
import re
from datetime import datetime
import logging
import signal
import sys

# Initialize logging
logging.basicConfig(filename='server.log', level=logging.INFO)


# Connection to the database
def connect_db():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="090104",
            database="MailServer",
            port=3306
        )
    except mysql.connector.Error as e:
        logging.error(f"Database connection error: {e}")
        return None


# Create necessary tables
def create_tables():
    conn = connect_db()
    if not conn:
        return
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL
    )''')

    # Create emails table
    cursor.execute('''CREATE TABLE IF NOT EXISTS emails (
        id INT AUTO_INCREMENT PRIMARY KEY,
        sender_email VARCHAR(255) NOT NULL,
        receiver_email VARCHAR(255) NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        content TEXT NOT NULL,
        sender_ip VARCHAR(45) NOT NULL
    )''')

    # Create user status table
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_status (
        username VARCHAR(255) PRIMARY KEY,
        status VARCHAR(10) NOT NULL DEFAULT 'offline'
    )''')

    conn.commit()
    conn.close()


# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Register user
def register_user(username, password):
    conn = connect_db()
    if not conn:
        return "error:Database connection failed."

    cursor = conn.cursor()
    password_hash = hash_password(password)

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cursor.fetchone():
        conn.close()
        return "error:Username already exists!"
    else:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
        conn.commit()
        conn.close()
        return "success:Account created successfully!"


# Login user
def login_user(username, password):
    conn = connect_db()
    if not conn:
        return "error:Database connection failed."

    cursor = conn.cursor()
    password_hash = hash_password(password)

    cursor.execute("SELECT * FROM users WHERE username=%s AND password_hash=%s", (username, password_hash))
    if cursor.fetchone():
        cursor.execute(
            "INSERT INTO user_status (username, status) VALUES (%s, 'online') ON DUPLICATE KEY UPDATE status='online'",
            (username,))
        conn.commit()
        conn.close()
        return "success:Login successful!"
    else:
        conn.close()
        return "error:Invalid username or password."


# Logout user
def logout_user(username):
    conn = connect_db()
    if not conn:
        return "error:Database connection failed."

    cursor = conn.cursor()
    cursor.execute("UPDATE user_status SET status='offline' WHERE username=%s", (username,))
    conn.commit()
    conn.close()
    return "success:Logout successful!"


# Validate email format
def is_valid_email(email):
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email)


# Send email
def send_email(sender_email, receiver_email, content, sender_ip):
    if not is_valid_email(sender_email) or not is_valid_email(receiver_email):
        return "error:Invalid email format."

    conn = connect_db()
    if not conn:
        return "error:Database connection failed."

    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO emails (sender_email, receiver_email, content, sender_ip) VALUES (%s, %s, %s, %s)",
                       (sender_email, receiver_email, content, sender_ip))
        conn.commit()
        return "success:Email sent successfully!"
    except mysql.connector.Error as e:
        return f"error:Database error: {e}"
    finally:
        conn.close()


# Get emails
def get_emails(username):
    conn = connect_db()
    if not conn:
        return "error:Database connection failed."

    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, sender_email, receiver_email, timestamp FROM emails WHERE sender_email=%s OR receiver_email=%s ORDER BY timestamp DESC",
            (username, username))
        emails = cursor.fetchall()
        return emails
    except mysql.connector.Error as e:
        return f"error:Database error: {e}"
    finally:
        conn.close()


# Get email details
# Get email details
def get_email_detail(email_id):
    conn = connect_db()
    if not conn:
        return "error:Database connection failed."

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT sender_email, receiver_email, content, timestamp FROM emails WHERE id=%s", (email_id,))
        email = cursor.fetchone()
        if email:
            sender_email, receiver_email, content, timestamp = email
            content = content.replace("\n", "<newline>")  # Encode newline as <newline> for safe transmission
            return f"success:From: {sender_email}\nTo: {receiver_email}\nAt: {timestamp}\nContent:\n{content}"
        else:
            return "error:Email not found."
    except mysql.connector.Error as e:
        return f"error:Database error: {e}"
    finally:
        conn.close()


# Get online users
def get_online_users():
    conn = connect_db()
    if not conn:
        return "error:Database connection failed."

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username FROM user_status WHERE status='online'")
        online_users = cursor.fetchall()
        return [user[0] for user in online_users]
    except mysql.connector.Error as e:
        return f"error:Database error: {e}"
    finally:
        conn.close()


# Handle client connections
def handle_client(client_socket):
    try:
        while True:
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                break

            # Parse request
            if "|" in data:
                command, params = data.split("|", 1)
            else:
                command = data
                params = ""

            if command == "REGISTER":
                try:
                    username, password = params.split(":")
                    response = register_user(username, password)
                except ValueError:
                    response = "error:Invalid register format."

            elif command == "LOGIN":
                try:
                    username, password = params.split(":")
                    response = login_user(username, password)
                except ValueError:
                    response = "error:Invalid login format."

            elif command == "LOGOUT":
                try:
                    username = params
                    response = logout_user(username)
                except ValueError:
                    response = "error:Invalid logout format."

            elif command == "SEND_EMAIL":
                try:
                    sender_email, receiver_email, content, sender_ip = params.split(":")
                    content = content.replace("<newline>", "\n")
                    response = send_email(sender_email, receiver_email, content, sender_ip)
                except ValueError:
                    response = "error:Invalid send_email format."

            elif command == "GET_EMAILS":
                try:
                    username = params
                    emails = get_emails(username)
                    if isinstance(emails, str) and emails.startswith("error"):
                        response = emails
                    else:
                        email_list = []
                        for email in emails:
                            email_id, sender, receiver, timestamp = email
                            email_list.append(f"{email_id}|From: {sender}|To: {receiver}|{timestamp}")
                        response = "success:" + "\n".join(email_list) if email_list else "success:No emails found."
                except ValueError:
                    response = "error:Invalid get_emails format."

            elif command == "GET_EMAIL_DETAIL":
                try:
                    email_id = params
                    detail = get_email_detail(email_id)
                    response = detail
                except ValueError:
                    response = "error:Invalid get_email_detail format."

            elif command == "GET_ONLINE_USERS":
                online_users = get_online_users()
                response = "success:" + ",".join(online_users)

            else:
                response = "error:Unknown command."

            client_socket.send(response.encode('utf-8'))

    finally:
        client_socket.close()


# Start the server
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local_ip = socket.gethostbyname(socket.gethostname())
    server_socket.bind((local_ip,5555))
    server_socket.listen(5)
    print("Server started and listening on "+local_ip+"port 5000")

    def shutdown(signal, frame):
        logging.info("Shutting down the server...")
        server_socket.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    while True:
        client_socket, addr = server_socket.accept()
        logging.info(f"Accepted connection from {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()


if __name__ == "__main__":
    create_tables()
    start_server()
