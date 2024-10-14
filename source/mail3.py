import mysql.connector
import hashlib
import socket
from tkinter import *
from tkinter import messagebox
from datetime import datetime


def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="090104",
        database="MailServer",
        port=3306
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


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def update_user_status(username, status):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_status (username, status) VALUES (%s, %s) ON DUPLICATE KEY UPDATE status=%s",
                   (username, status, status))
    conn.commit()
    conn.close()


def register_user():
    username = reg_username_entry.get()
    password = reg_password_entry.get()
    password_hash = hash_password(password)

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cursor.fetchone():
        messagebox.showerror("Error", "Username already exists!")
    else:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
        conn.commit()
        messagebox.showinfo("Success", "Account created successfully!")

    conn.close()


current_user = None  # Global variable to store logged-in user
sent_email_list = None
received_email_list = None

def send_email(sender_email, receiver_email, content):
    global sent_email_list, received_email_list  # Access global lists

    if not sender_email or not receiver_email or not content.strip():
        messagebox.showerror("Error", "All fields are required!")
        return

    hostname = socket.gethostname()
    sender_ip = socket.gethostbyname(hostname)

    message = f"From: {sender_email}\nTo: {receiver_email}\nContent: {content}\nIP: {sender_ip}\nTime: {datetime.now()}"
    send_message_to_server(message)

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO emails (sender_email, receiver_email, content, sender_ip) VALUES (%s, %s, %s, %s)",
                   (sender_email, receiver_email, content, sender_ip))
    conn.commit()
    conn.close()

    messagebox.showinfo("Success", "Email sent successfully!")
    load_emails(sent_email_list, received_email_list)

def send_message_to_server(message):
    try:
        # Replace 'server_ip_address' with the actual server's IP address
        server_ip_address = socket.gethostbyname(socket.gethostname())  # Use your server's local IP
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((server_ip_address, 12345))
            client_socket.sendall(message.encode('utf-8'))
    except Exception as e:
        print(f"Error sending message to server: {e}")
        messagebox.showerror("Error", "Could not send message to the server.")

def login_user():
    global current_user
    username = login_username_entry.get()
    password = login_password_entry.get()
    password_hash = hash_password(password)

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=%s AND password_hash=%s", (username, password_hash))
    if cursor.fetchone():
        messagebox.showinfo("Success", "Login successful!")
        current_user = username  # Store logged-in account
        update_user_status(current_user, "online")  # Update user status to online
        open_main_interface()  # Open main interface on successful login
    else:
        messagebox.showerror("Error", "Invalid username or password")

    conn.close()
def logout_user():
    global current_user
    if current_user:
        update_user_status(current_user, "offline")  # Update user status to offline
        current_user = None  # Clear the current user
        messagebox.showinfo("Info", "You have logged out successfully.")
        root.quit()  # Close the application or redirect to the login screen

def open_main_interface():
    global current_user, sent_email_list, received_email_list  # Add variables here

    login_frame.pack_forget()
    register_frame.pack_forget()

    root.title(f"Email Client - {current_user}")

    main_frame = Frame(root, padx=20, pady=20, bg="#f7f7f7")
    main_frame.pack(pady=20)

    # Online users list
    online_frame = Frame(main_frame, bg="#ffffff", bd=2, relief="groove")
    online_frame.pack(side=LEFT, padx=(0, 20), fill=Y)

    Label(online_frame, text="Online Users:", font=("Arial", 12, "bold"), bg="#ffffff").pack(pady=10)
    online_user_list = Listbox(online_frame, width=30, height=10)
    online_user_list.pack(pady=10)

    load_online_users(online_user_list)

    # Email sending interface
    email_frame = Frame(main_frame, bg="#ffffff", bd=2, relief="groove")
    email_frame.pack(side=LEFT, padx=(20, 0))

    Label(email_frame, text="Send Email", font=("Arial", 12, "bold"), bg="#ffffff").pack(pady=10)

    Label(email_frame, text="Sender Email:", bg="#ffffff").pack()
    sender_entry = Entry(email_frame, width=40)
    sender_entry.pack(pady=5)
    sender_entry.insert(0, current_user)
    sender_entry.config(state='readonly')

    Label(email_frame, text="Receiver Email:", bg="#ffffff").pack()
    receiver_entry = Entry(email_frame, width=40)
    receiver_entry.pack(pady=5)

    Label(email_frame, text="Content:", bg="#ffffff").pack()
    content_entry = Text(email_frame, width=40, height=10)
    content_entry.pack(pady=5)

    send_button = Button(email_frame, text="Send", command=lambda: send_email(sender_entry.get(), receiver_entry.get(),
                                                                              content_entry.get("1.0", END)),
                         bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
    send_button.pack(pady=10)

    # Logout button
    logout_button = Button(email_frame, text="Logout", command=logout_user, bg="#F44336", fg="white",
                           font=("Arial", 10, "bold"))
    logout_button.pack(pady=5)

    # Reload button
    reload_button = Button(email_frame, text="Reload",
                           command=lambda: reload_data(online_user_list, sent_email_list, received_email_list),
                           bg="#FF9800", fg="white", font=("Arial", 10, "bold"))
    reload_button.pack(pady=5)

    # Sent and received emails list
    emails_frame = Frame(main_frame, bg="#ffffff", bd=2, relief="groove")
    emails_frame.pack(side=LEFT, padx=(20, 0))

    Label(emails_frame, text="Your Sent Emails:", font=("Arial", 12, "bold"), bg="#ffffff").pack(pady=10)
    sent_email_list = Listbox(emails_frame, width=60, height=10)  # Gán vào biến toàn cục
    sent_email_list.pack(pady=5)

    Label(emails_frame, text="Your Received Emails:", font=("Arial", 12, "bold"), bg="#ffffff").pack(pady=10)
    received_email_list = Listbox(emails_frame, width=60, height=10)  # Gán vào biến toàn cục
    received_email_list.pack(pady=5)

    load_emails(sent_email_list, received_email_list)
    sent_email_list.bind('<Double-1>', lambda event: show_email_detail(sent_email_list))
    received_email_list.bind('<Double-1>', lambda event: show_email_detail(received_email_list))

    # Thanh trạng thái ở dưới cùng
    status_frame = Frame(root, bg="#f7f7f7")
    status_frame.pack(side=BOTTOM, fill=X)
    Label(status_frame, text="Welcome to the Email Client!", bg="#f7f7f7").pack(pady=5)


def reload_data(online_user_list, sent_email_list, received_email_list):
    # Xóa danh sách cũ
    online_user_list.delete(0, END)
    sent_email_list.delete(0, END)
    received_email_list.delete(0, END)

    # Tải lại dữ liệu mới
    load_online_users(online_user_list)
    load_emails(sent_email_list, received_email_list)

def load_online_users(online_user_list):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM user_status WHERE status='online'")
    online_users = cursor.fetchall()

    for user in online_users:
        online_user_list.insert(END, user[0])

    conn.close()

def load_emails(sent_email_list, received_email_list):
    # Clear the current list
    sent_email_list.delete(0, END)
    received_email_list.delete(0, END)

    conn = connect_db()
    cursor = conn.cursor()

    # Load sent emails
    cursor.execute("SELECT receiver_email, timestamp FROM emails WHERE sender_email=%s", (current_user,))
    sent_emails = cursor.fetchall()
    for email in sent_emails:
        sent_email_list.insert(END, f"To: {email[0]} - {email[1]}")  # Removed email ID

    # Load received emails
    cursor.execute("SELECT sender_email, timestamp FROM emails WHERE receiver_email=%s", (current_user,))
    received_emails = cursor.fetchall()
    for email in received_emails:
        received_email_list.insert(END, f"From: {email[0]} - {email[1]}")  # Removed email ID

    conn.close()

def show_email_detail(email_listbox):
    selected_index = email_listbox.curselection()  # Get selected email index
    if not selected_index:  # If no email is selected, do nothing
        return

    email_info = email_listbox.get(selected_index)  # Get the selected email info
    email_info_parts = email_info.split(" - ")  # Split to get the ID and other details

    email_id = email_info_parts[0].strip()  # Extract the email ID

    conn = connect_db()
    cursor = conn.cursor()

    # Fetch the content of the email using the ID
    cursor.execute("SELECT content FROM emails WHERE id=%s", (email_id,))
    email_content = cursor.fetchone()  # Fetch the email content

    if email_content:
        # Create a new window to display email details
        email_detail_window = Toplevel(root)
        email_detail_window.title("Email Details")
        email_detail_window.geometry("400x300")

        Label(email_detail_window, text="Email Content:", font=("Arial", 14, "bold")).pack(pady=10)
        content_text = Text(email_detail_window, wrap=WORD)
        content_text.insert(END, email_content[0])  # Insert the content into the text box
        content_text.config(state='disabled')  # Make the text box read-only
        content_text.pack(expand=True, fill=BOTH, padx=10, pady=10)

        Button(email_detail_window, text="Close", command=email_detail_window.destroy).pack(pady=10)
    else:
        messagebox.showerror("Error", "Email content not found.")



def show_register_frame():
    login_frame.pack_forget()
    register_frame.pack(pady=20)


def show_login_frame():
    register_frame.pack_forget()
    login_frame.pack(pady=20)


root = Tk()
root.title("Email Client")
root.geometry("600x400")
root.configure(bg="#f7f7f7")  # Thay đổi màu nền của cửa sổ chính
create_user_table()
create_email_table()
create_user_status_table()

# Định nghĩa khung đăng nhập và đăng ký
login_frame = Frame(root, bg="#f7f7f7")
login_frame.pack(pady=20)

Label(login_frame, text="Login", font=("Arial", 16, "bold"), bg="#f7f7f7").pack()
Label(login_frame, text="Username:").pack(pady=5)
login_username_entry = Entry(login_frame)
login_username_entry.pack(pady=5)
Label(login_frame, text="Password:").pack(pady=5)
login_password_entry = Entry(login_frame, show='*')
login_password_entry.pack(pady=5)

Button(login_frame, text="Login", command=login_user).pack(pady=10)
Button(login_frame, text="Register", command=show_register_frame).pack()

# Khung đăng ký
register_frame = Frame(root, bg="#f7f7f7")

Label(register_frame, text="Register", font=("Arial", 16, "bold"), bg="#f7f7f7").pack()
Label(register_frame, text="Username:").pack(pady=5)
reg_username_entry = Entry(register_frame)
reg_username_entry.pack(pady=5)
Label(register_frame, text="Password:").pack(pady=5)
reg_password_entry = Entry(register_frame, show='*')
reg_password_entry.pack(pady=5)

Button(register_frame, text="Register", command=register_user).pack(pady=10)
Button(register_frame, text="Back to Login", command=show_login_frame).pack()

root.mainloop()