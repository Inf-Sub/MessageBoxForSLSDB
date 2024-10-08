import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from configparser import ConfigParser

class DBYFileViewer:
    def __init__(self):
        self._config_file = 'settings.ini'
        self.config = self.check_or_create_settings()
        self.executable_path = self.get_executable_path()
        self.folder_path = self.get_folder_path()
        self.dby_files = []

    def check_or_create_settings(self):
        config = ConfigParser()
        if not os.path.exists(self._config_file):
            config['Settings'] = {'folder_path': '', 'executable_path': ''}

            # Добавляем секцию с размером окна
            config['Window'] = {'width': '600', 'height': '400'}

            with open(self._config_file, 'w') as file:
                config.write(file)
        else:
            config.read(self._config_file)
        return config

    def get_executable_path(self):
        if self.config.has_option('Settings', 'executable_path'):
            return self.config.get('Settings', 'executable_path')
        else:
            return self.select_executable()

    def get_folder_path(self):
        if self.config.has_option('Settings', 'folder_path'):
            return self.config.get('Settings', 'folder_path')
        else:
            return self.select_folder()

    def select_executable(self):
        exe_selected = filedialog.askopenfilename(
            title="Выберите исполняемый файл",
            filetypes=(("Executable files", "*.exe"), ("All files", "*.*"))
        )
        if exe_selected:
            self.config.set('Settings', 'executable_path', exe_selected)
            with open(self._config_file, 'w') as file:
                self.config.write(file)
        return exe_selected

    def select_folder(self):
        folder_selected = filedialog.askdirectory(title="Выберите папку")
        if folder_selected:
            self.config.set('Settings', 'folder_path', folder_selected)
            with open(self._config_file, 'w') as file:
                self.config.write(file)
        return folder_selected

    def find_dby_files(self):
        dby_files = []
        for root, _, files in os.walk(self.folder_path):
            for file in files:
                if file.lower().endswith('.dby'):
                    dby_files.append((os.path.splitext(file)[0], os.path.join(root, file)))
        self.dby_files = dby_files

    def open_program(self, file_path):
        try:
            subprocess.Popen([self.executable_path, file_path])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл: {str(e)}")

    def on_select(self, event, listbox):
        selected_index = listbox.curselection()
        if selected_index:
            _, file_path = self.dby_files[selected_index[0]]
            self.open_program(file_path)

    def save_window_size(self, root):
        width = root.winfo_width()
        height = root.winfo_height()
        self.config.set('Window', 'width', str(width))
        self.config.set('Window', 'height', str(height))
        with open(self._config_file, 'w') as file:
            self.config.write(file)

    def run(self):
        if not self.executable_path:
            self.executable_path = self.select_executable()

        if not self.folder_path:
            self.folder_path = self.select_folder()

        if self.folder_path and self.executable_path:
            self.find_dby_files()

            root = tk.Tk()
            root.title("DBY File Viewer")

            # Восстанавливаем размер окна
            width = self.config.getint('Window', 'width')
            height = self.config.getint('Window', 'height')
            root.geometry(f"{width}x{height}")

            # Создаем фрейм для прокрутки
            frame = ttk.Frame(root)
            frame.pack(expand=True, fill=tk.BOTH)

            # Добавляем scrollbar и listbox
            scrollbar = ttk.Scrollbar(frame)
            listbox = tk.Listbox(frame, width=50, height=20, yscrollcommand=scrollbar.set)
            scrollbar.config(command=listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            listbox.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

            for name, _ in self.dby_files:
                listbox.insert(tk.END, name)

            listbox.bind('<Double-1>', lambda event: self.on_select(event, listbox))

            open_button = tk.Button(root, text="Открыть", command=lambda: self.on_select(None, listbox))
            open_button.pack()

            close_button = tk.Button(root, text="Закрыть", command=root.quit)
            close_button.pack()

            # Сохраняем размер при закрытии окна
            root.protocol("WM_DELETE_WINDOW", lambda: (self.save_window_size(root), root.quit()))

            root.mainloop()

        if __name__ == "__main__":
            viewer = DBYFileViewer()
            viewer.run()
