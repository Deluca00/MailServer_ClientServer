# client.py
import socket
import tkinter as tk
from tkinter import messagebox, END, Toplevel, Text, WORD

# Hàm gửi yêu cầu đến server
def send_request(request):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        local_ip = socket.gethostbyname(socket.gethostname())
        client.connect((local_ip, 5555))
        client.send(request.encode('utf-8'))
        response = client.recv(4096).decode('utf-8')
        client.close()
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None




def logout_user():
    global current_user
    if current_user:
        response = send_request(f"LOGOUT|{current_user}")
        if response and response.startswith("success"):
            current_user = None
            messagebox.showinfo("Info", "You have logged out successfully.")
            root.quit()  # Quay lại màn hình đăng nhập
        else:
            messagebox.showerror("Error", "Logout failed. No response from server.")





main_frame = None

# Đăng ký tài khoản
def register_user():
    username = reg_username_entry.get()
    password = reg_password_entry.get()
    if not username or not password:
        messagebox.showerror("Error", "Username and password are required")
        return

    response = send_request(f"REGISTER|{username}:{password}")
    if response:
        if response.startswith("success"):
            messagebox.showinfo("Success", response.split(":",1)[1])
            show_login_frame()
        else:
            messagebox.showerror("Error", response.split(":",1)[1])
    else:
        messagebox.showerror("Error", "No response from server.")

# Đăng nhập
def login_user():
    global current_user
    username = login_username_entry.get()
    password = login_password_entry.get()
    if not username or not password:
        messagebox.showerror("Error", "Username and password are required")
        return
    response = send_request(f"LOGIN|{username}:{password}")
    if response:
        if response.startswith("success"):
            messagebox.showinfo("Success", response.split(":",1)[1])
            current_user = username
            open_main_interface()
        else:
            messagebox.showerror("Error", response.split(":",1)[1])
    else:
        messagebox.showerror("Error", "No response from server.")

# Đăng xuất


# Gửi email
def send_email(sender_email, receiver_email, content):
    sender_ip = socket.gethostbyname(socket.gethostname())  # Lấy IP local

    if not receiver_email or not content.strip():
        messagebox.showerror("Error", "Receiver and content are required")
        return

    # Thay thế các ký tự xuống dòng để tránh vấn đề phân tích lệnh
    content = content.replace("\n", "<newline>")
    response = send_request(f"SEND_EMAIL|{sender_email}:{receiver_email}:{content}:{sender_ip}")
    if response:
        if response.startswith("success"):
            messagebox.showinfo("Success", response.split(":",1)[1])
            load_emails(sent_email_list, received_email_list)
        else:
            messagebox.showerror("Error", response.split(":",1)[1])
    else:
        messagebox.showerror("Error", "No response from server.")

        # Gửi email và sau đó cập nhật danh sách email
        response = send_request(
                            f"SEND_EMAIL|{sender}|{receiver}|{content}|{socket.gethostbyname(socket.gethostname())}")
        if response.startswith("success"):
            messagebox.showinfo("Success", "Email sent successfully!")
            load_emails(sent_email_list, received_email_list)  # Cập nhật lại danh sách email
        else:
            messagebox.showerror("Error", response.split(":", 1)[1])
# Lấy danh sách email


# Reload dữ liệu
def reload_data(online_user_list, sent_email_list, received_email_list):
    load_online_users(online_user_list)
    load_emails(sent_email_list, received_email_list)

# Lấy danh sách người dùng online
def load_online_users(online_user_list):
    response = send_request("GET_ONLINE_USERS|")
    if response:
        if response.startswith("success"):
            online_users = response.split(":",1)[1]
            online_user_list.delete(0, END)
            if online_users != "No users online.":
                for user in online_users.split(","):
                    online_user_list.insert(END,user)
        else:
            messagebox.showerror("Error", response.split(":",1)[1])
    else:
        messagebox.showerror("Error", "No response from server.")

# Hiển thị giao diện chính sau khi đăng nhập
# Hiển thị giao diện chính sau khi đăng nhập
def open_main_interface():
    global current_user, sent_email_list, received_email_list

    login_frame.pack_forget()
    register_frame.pack_forget()

    root.title(f"Email Client - {current_user}")

    main_frame = tk.Frame(root, padx=20, pady=20, bg="#f7f7f7")  # Initialize main_frame here
    main_frame.pack(pady=20, fill=tk.BOTH, expand=True)

    # Online users list
    online_frame = tk.Frame(main_frame, bg="#ffffff", bd=2, relief="groove")
    online_frame.pack(side=tk.LEFT, padx=(0, 20), fill=tk.Y)

    tk.Label(online_frame, text="Online Users:", font=("Arial", 12, "bold"), bg="#ffffff").pack(pady=10)
    online_user_list = tk.Listbox(online_frame, width=30, height=10)
    online_user_list.pack(pady=10)

    load_online_users(online_user_list)

    # Email sending interface
    email_frame = tk.Frame(main_frame, bg="#ffffff", bd=2, relief="groove")
    email_frame.pack(side=tk.LEFT, padx=(20, 0))

    tk.Label(email_frame, text="Send Email", font=("Arial", 12, "bold"), bg="#ffffff").pack(pady=10)

    tk.Label(email_frame, text="Sender Email:", bg="#ffffff").pack()
    sender_entry = tk.Entry(email_frame, width=40)
    sender_entry.pack(pady=5)
    sender_entry.insert(0, current_user)
    sender_entry.config(state='readonly')

    tk.Label(email_frame, text="Receiver Email:", bg="#ffffff").pack()
    receiver_entry = tk.Entry(email_frame, width=40)
    receiver_entry.pack(pady=5)

    tk.Label(email_frame, text="Content:", bg="#ffffff").pack()
    content_entry = tk.Text(email_frame, width=40, height=10)
    content_entry.pack(pady=5)

    send_button = tk.Button(email_frame, text="Send", command=lambda: send_email(sender_entry.get(), receiver_entry.get(), content_entry.get("1.0", END)),
                            bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
    send_button.pack(pady=10)

    # Logout button
    logout_button = tk.Button(email_frame, text="Logout", command=logout_user, bg="#F44336", fg="white",
                               font=("Arial", 10, "bold"))
    logout_button.pack(pady=5)

    # Reload button
    reload_button = tk.Button(email_frame, text="Reload",
                               command=lambda: reload_data(online_user_list, sent_email_list, received_email_list),
                               bg="#FF9800", fg="white", font=("Arial", 10, "bold"))
    reload_button.pack(pady=5)

    # Phần hiển thị danh sách email đã gửi và nhận
    emails_frame = tk.Frame(main_frame, bg="#ffffff", bd=2, relief="groove")
    emails_frame.pack(side=tk.LEFT, padx=(20, 0))

    tk.Label(emails_frame, text="Your Sent Emails:", font=("Arial", 12, "bold"), bg="#ffffff").pack(pady=10)
    sent_email_list = tk.Listbox(emails_frame, width=60, height=10)  # Gán vào biến toàn cục
    sent_email_list.pack(pady=5)

    tk.Label(emails_frame, text="Your Received Emails:", font=("Arial", 12, "bold"), bg="#ffffff").pack(pady=10)
    received_email_list = tk.Listbox(emails_frame, width=60, height=10)  # Gán vào biến toàn cục
    received_email_list.pack(pady=5)

    # Gọi hàm load_emails để cập nhật danh sách email ngay khi mở giao diện
    load_emails(sent_email_list, received_email_list)

    sent_email_list.bind('<Double-1>', lambda event: show_email_detail(sent_email_list))
    received_email_list.bind('<Double-1>', lambda event: show_email_detail(received_email_list))

    # Thanh trạng thái ở dưới cùng
    status_frame = tk.Frame(root, bg="#f7f7f7")
    status_frame.pack(side=tk.BOTTOM, fill=tk.X)
    tk.Label(status_frame, text="Welcome to the Email Client!", bg="#f7f7f7").pack(pady=5)




def load_emails(sent_email_list, received_email_list):
    if not current_user:
        return

    response = send_request(f"GET_EMAILS|{current_user}")
    if response:
        print("Response from server:", response)  # Debugging line

        if response.startswith("success"):
            emails_data = response.split(":", 1)[1]
            print("Emails data received:", emails_data)  # Debugging line

            sent_email_list.delete(0, END)
            received_email_list.delete(0, END)

            # Process email data
            parts = emails_data.replace('\n', '|').split("|")
            print("Parts after splitting:", parts)  # Debugging line

            # Iterate through parts (4 phần cho mỗi email)
            for i in range(0, len(parts), 4):
                try:
                    id = parts[i]  # ID của email
                    sender = parts[i + 1]  # "From: khanh@gmail.com"
                    receiver = parts[i + 2]  # "To: khanh1@gmail.com"
                    timestamp = parts[i + 3]  # "2024-10-14 22:33:57"

                    # Insert into the appropriate listbox
                    if sender == f"From: {current_user}":
                        sent_email_list.insert(END, f"{id}|To: {receiver} - {timestamp}")
                    elif receiver == f"To: {current_user}":
                        received_email_list.insert(END, f"{id}|From: {sender} - {timestamp}")
                except IndexError:
                    messagebox.showerror("Error", "Error processing email data.")
                    break
        else:
            messagebox.showerror("Error", response.split(":", 1)[1])
    else:
        messagebox.showerror("Error", "No response from server.")

# Hiển thị chi tiết email
def show_email_detail(email_listbox):
    selected = email_listbox.curselection()
    if not selected:
        return
    selected_text = email_listbox.get(selected[0])
    print(f"Selected email text: {selected_text}")  # Debugging line

    # Dạng: email_id|From: ... - timestamp hoặc email_id|To: ... - timestamp
    id = selected_text.split("|")[0]
    response = send_request(f"GET_EMAIL_DETAIL|{id}")
    if response:
        if response.startswith("success"):
            email_detail = response.split(":", 1)[1]
            print(f"Email detail from server: {email_detail}")  # Debugging line

            # Thay thế <newline> bằng ký tự xuống dòng thực sự
            email_detail = email_detail.replace("<newline>", "\n")

            # Tạo một cửa sổ mới để hiển thị chi tiết email
            detail_window = Toplevel(root)
            detail_window.title("Email Details")
            detail_window.geometry("400x300")

            tk.Label(detail_window, text="Email Details:", font=("Arial", 14, "bold")).pack(pady=10)
            text = tk.Text(detail_window, wrap=WORD)
            text.insert(END, email_detail)
            text.config(state='disabled')
            text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

            tk.Button(detail_window, text="Close", command=detail_window.destroy).pack(pady=10)
        else:
            messagebox.showerror("Error", response.split(":", 1)[1])
    else:
        messagebox.showerror("Error", "No response from server.")





# Giao diện đăng ký
def show_register_frame():
    login_frame.pack_forget()
    register_frame.pack(pady=20)

# Giao diện đăng nhập
def show_login_frame():
    register_frame.pack_forget()
    login_frame.pack(pady=20)

# Giao diện đăng nhập/đăng ký
root = tk.Tk()
root.title("Email Client")
root.geometry("800x600")
root.configure(bg="#f7f7f7")

current_user = None  # Global variable to store logged-in user

# Tạo khung đăng nhập
login_frame = tk.Frame(root, bg="#f7f7f7")
login_frame.pack(pady=20)

tk.Label(login_frame, text="Login", font=("Arial", 16, "bold"), bg="#f7f7f7").pack()
tk.Label(login_frame, text="Username:", bg="#f7f7f7").pack(pady=5)
login_username_entry = tk.Entry(login_frame)
login_username_entry.pack(pady=5)
tk.Label(login_frame, text="Password:", bg="#f7f7f7").pack(pady=5)
login_password_entry = tk.Entry(login_frame, show="*")
login_password_entry.pack(pady=5)

tk.Button(login_frame, text="Login", command=login_user).pack(pady=10)
tk.Button(login_frame, text="Register", command=show_register_frame).pack()

# Tạo khung đăng ký
register_frame = tk.Frame(root, bg="#f7f7f7")
tk.Label(register_frame, text="Register", font=("Arial", 16, "bold"), bg="#f7f7f7").pack()
tk.Label(register_frame, text="Username:", bg="#f7f7f7").pack(pady=5)
reg_username_entry = tk.Entry(register_frame)
reg_username_entry.pack(pady=5)
tk.Label(register_frame, text="Password:", bg="#f7f7f7").pack(pady=5)
reg_password_entry = tk.Entry(register_frame, show="*")
reg_password_entry.pack(pady=5)

tk.Button(register_frame, text="Register", command=register_user).pack(pady=10)
tk.Button(register_frame, text="Back to Login", command=show_login_frame).pack()

# Chạy giao diện Tkinter
root.mainloop()
