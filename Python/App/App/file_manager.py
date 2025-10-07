import os
import zipfile
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
from PIL import Image
from cryptography.fernet import Fernet
import paramiko
import json
import stat
from tkinter.ttk import Progressbar

EXCLUDE_FOLDERS = ['.Trash', 'Applications', 'Library', 'System', 'Volumes']
PROFILE_PATH = os.path.expanduser("~/.ssh_profiles.json")
current_remote_path = '.'
sftp_client = None
selected_remote_path = '.'
status_var = None
progressbar = None
local_tree = None
remote_tree = None
root = None


def upate_status(msg):
    if status_var:
        status_var.set(msg)

def generate_key():
    return Fernet.generate_key()

def save_profile(profile):
    profiles = load_profiles()
    if profile not in profiles:
        profiles.append(profile)
        with open(PROFILE_PATH, 'w') as f:
            json.dump(profiles, f)

def load_profiles():
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, 'r') as f:
            return json.load(f)
    return []

def edit_profiles():
    profiles = load_profiles()
    if not profiles:
        messagebox.showinfo("Info", "No profiles to edit.")
        return
    options = [f"{p['username']}@{p['hostname']}" for p in profiles]
    choice = simpledialog.askstring("Edit Profile", f"Profiles:\n" + "\n".join(f"{i+1}. {o}" for i, o in enumerate(options)) + "\nEnter number to delete or 'e#' to edit:")
    if not choice:
        return
    if choice.startswith('e') and choice[1:].isdigit():
        idx = int(choice[1:]) - 1
        profile = profiles[idx]
        new_hostname = simpledialog.askstring("Edit Hostname", "Enter new hostname", initialvalue=profile['hostname'])
        new_username = simpledialog.askstring("Edit Username", "Enter new username", initialvalue=profile['username'])
        profiles[idx] = {"hostname": new_hostname, "username": new_username}
        with open(PROFILE_PATH, 'w') as f:
            json.dump(profiles, f)
        messagebox.showinfo("Success", "Profile updated.")
    elif choice.isdigit():
        try:
            idx = int(choice) - 1
            profiles.pop(idx)
            with open(PROFILE_PATH, 'w') as f:
                json.dump(profiles, f)
            messagebox.showinfo("Success", "Profile deleted.")
        except:
            messagebox.showerror("Error", "Invalid selection.")
    else:
        messagebox.showerror("Invalid Input", "Please enter a valid profile number or 'e#' to edit.")
        return

def upload_files():
    global sftp_client, current_remote_path
    local_paths = filedialog.askopenfilenames()
    if local_paths and sftp_client:
        for local_path in local_paths:
            filename = os.path.basename(local_path)
            remote_path = os.path.join(current_remote_path, filename)
            try:
                filesize = os.path.getsize(local_path)
                with open(local_path, 'rb') as f:
                    def progress(transferred, total):
                        percent = int((transferred / total) * 100)
                        progressbar['value'] = percent
                        update_status(f"Uploading {filename}: {percent}%")
                        root.update_idletasks()
                    sftp_client.putfo(f, remote_path, callback=progress)
                update_status(f"Uploaded: {local_path} → {remote_path}")
            except Exception as e:
                update_status(f"Upload failed: {e}")

def encrypt_file():
    file_paths = filedialog.askopenfilenames()
    if not file_paths:
        return
    key_path = filedialog.asksaveasfilename(title="Save Encryption Key", defaultextension=".key")
    if not key_path:
        return
    key = generate_key()
    with open(key_path, 'wb') as key_file:
        key_file.write(key)
    fernet = Fernet(key)
    for file_path in file_paths:
        with open(file_path, 'rb') as file:
            original = file.read()
        encrypted = fernet.encrypt(original)
        enc_file_path = file_path + '.enc'
        with open(enc_file_path, 'wb') as enc_file:
            enc_file.write(encrypted)
    messagebox.showinfo("Success", "Files encrypted successfully")

def decrypt_file():
    enc_file_paths = filedialog.askopenfilenames(title="Select Encrypted Files")
    if not enc_file_paths:
        return
    key_path = filedialog.askopenfilename(title="Open Encryption Key", filetypes=[("Key files", "*.key")])
    if not key_path:
        return
    with open(key_path, 'rb') as key_file:
        key = key_file.read()
    fernet = Fernet(key)
    for enc_file_path in enc_file_paths:
        with open(enc_file_path, 'rb') as enc_file:
            encrypted = enc_file.read()
        decrypted = fernet.decrypt(encrypted)
        dec_file_path = enc_file_path.replace('.enc', '')
        with open(dec_file_path, 'wb') as dec_file:
            dec_file.write(decrypted)
    messagebox.showinfo("Success", "Files decrypted successfully")

def populate_local_tree(tree, parent, path):
    try:
        entries = sorted(os.listdir(path))
        for entry in entries:
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path) and not entry.startswith('.'):
                node = tree.insert(parent, 'end', text=entry, values=[full_path])
                tree.insert(node, 'end')
    except PermissionError:
        pass

def on_local_open(event):
    item = local_tree.focus()
    path = local_tree.item(item, 'values')[0]
    local_tree.delete(*local_tree.get_children(item))
    populate_local_tree(local_tree, item, path)

def on_remote_open(event):
    item = remote_tree.focus()
    path = remote_tree.item(item, 'values')[0]
    remote_tree.delete(*remote_tree.get_children(item))
    try:
        for entry in sftp_client.listdir_attr(path):
            full_path = os.path.join(path, entry.filename)
            node = remote_tree.insert(item, 'end', text=entry.filename, values=[full_path])
            if stat.S_ISDIR(entry.st_mode):
                remote_tree.insert(node, 'end')
    except Exception as e:
        update_status(f"Failed to open: {e}")

def connect_ssh():
    global sftp_client
    hostname = simpledialog.askstring("SSH", "Hostname")
    username = simpledialog.askstring("SSH", "Username")
    password = simpledialog.askstring("SSH", "Password", show='*')
    try:
        transport = paramiko.Transport((hostname, 22))
        transport.connect(username=username, password=password)
        sftp_client = paramiko.SFTPClient.from_transport(transport)
        refresh_remote_tree(remote_tree, sftp_client, '.')
        update_status(f"Connected to {hostname}")
    except Exception as e:
        messagebox.showerror("SSH Error", str(e))

def refresh_remote_tree(tree, sftp, path):
    global current_remote_path
    current_remote_path = path
    tree.delete(*tree.get_children())
    try:
        for entry in sftp.listdir_attr(path):
            full_path = os.path.join(path, entry.filename)
            node = tree.insert('', 'end', text=entry.filename, values=[full_path])
            if stat.S_ISDIR(entry.st_mode):
                tree.insert(node, 'end')
    except Exception as e:
        print(f"Failed to list remote path {path}: {e}")

def create_gui():
    global sftp_client, status_var, progressbar, root, local_tree, remote_tree
    root = tk.Tk()
    root.title("Full File Manager GUI")
    root.geometry("1200x700")

    status_var = tk.StringVar()
    status_bar = tk.Label(root, textvariable=status_var, anchor='w')
    status_bar.pack(side='bottom', fill='x')
    progressbar = Progressbar(root, orient='horizontal', length=100, mode='determinate')
    progressbar.pack(fill='x')

    main_pane = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    main_pane.pack(fill='both', expand=True)

    local_tree = ttk.Treeview(main_pane)
    remote_tree = ttk.Treeview(main_pane)
    local_tree.pack(fill='both', expand=True)
    remote_tree.pack(fill='both', expand=True)
    main_pane.add(local_tree, weight=1)
    main_pane.add(remote_tree, weight=1)

    populate_local_tree(local_tree, '', os.path.expanduser('~'))
    local_tree.bind("<<TreeviewOpen>>", on_local_open)
    remote_tree.bind("<<TreeviewOpen>>", on_remote_open)

    control_frame = ttk.Frame(root)
    control_frame.pack(pady=5)
    tk.Button(control_frame, text="Encrypt File", command=encrypt_file).grid(row=0, column=0, padx=5)
    tk.Button(control_frame, text="Decrypt File", command=decrypt_file).grid(row=0, column=1, padx=5)
    tk.Button(control_frame, text="Upload Files", command=upload_files).grid(row=0, column=2, padx=5)
    tk.Button(control_frame, text="Edit/Delete Profiles", command=edit_profiles).grid(row=0, column=3, padx=5)
    tk.Button(control_frame, text="Connect SSH", command=connect_ssh).grid(row=0, column=4, padx=5)

    root.mainloop()

create_gui()
