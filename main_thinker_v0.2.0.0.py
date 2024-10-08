import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from configparser import ConfigParser


def check_or_create_settings():
    config = ConfigParser()
    if not os.path.exists("settings.ini"):
        config['Settings'] = {'folder_path': '', 'executable_path': ''}
        with open('settings.ini', 'w') as configfile:
            config.write(configfile)
    else:
        config.read('settings.ini')
    return config


def select_executable(config):
    exe_selected = filedialog.askopenfilename(
        title="Выберите исполняемый файл",
        filetypes=(("Executable files", "*.exe"), ("All files", "*.*"))
    )
    if exe_selected:
        config.set('Settings', 'executable_path', exe_selected)
        with open('settings.ini', 'w') as configfile:
            config.write(configfile)
    return exe_selected


def select_folder(config):
    folder_selected = filedialog.askdirectory(title="Выберите папку")
    if folder_selected:
        config.set('Settings', 'folder_path', folder_selected)
        with open('settings.ini', 'w') as configfile:
            config.write(configfile)
    return folder_selected


def find_dby_files(directory):
    dby_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.dby'):
                dby_files.append((os.path.splitext(file)[0], os.path.join(root, file)))
    return dby_files


def open_program(executable_path, file_path):
    try:
        subprocess.run([executable_path, file_path], check=True)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось открыть файл: {str(e)}")


def on_select(event, listbox, dby_files, executable_path):
    selected_index = listbox.curselection()
    if selected_index:
        _, file_path = dby_files[selected_index[0]]
        listbox.quit()
        open_program(executable_path, file_path)


def main():
    config = check_or_create_settings()

    # Проверяем наличие параметра executable_path в секции Settings
    if config.has_option('Settings', 'executable_path'):
        executable_path = config.get('Settings', 'executable_path')
    else:
        executable_path = select_executable(config)

    if not executable_path:
        executable_path = select_executable(config)

    if config.has_option('Settings', 'folder_path'):
        folder_path = config.get('Settings', 'folder_path')
    else:
        folder_path = select_folder(config)

    if not folder_path:
        folder_path = select_folder(config)

    if folder_path and executable_path:
        dby_files = find_dby_files(folder_path)

        root = tk.Tk()
        root.title("DBY File Viewer")

        listbox = tk.Listbox(root, width=50, height=20)
        listbox.pack(expand=True, fill=tk.BOTH)

        for name, _ in dby_files:
            listbox.insert(tk.END, name)

        listbox.bind('<Double-1>', lambda event: on_select(event, listbox, dby_files, executable_path))

        open_button = tk.Button(root, text="Открыть", command=lambda: on_select(None, listbox, dby_files, executable_path))
        open_button.pack()

        root.mainloop()

if __name__ == "__main__":
    main()
