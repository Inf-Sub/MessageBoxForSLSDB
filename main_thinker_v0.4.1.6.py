import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from configparser import ConfigParser
import sys
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor


VERSION = "0.5.16"  # Версия приложения


class DBYFileViewer:
    def __init__(self):
        self.root = tk.Tk()  # Создание основного окна
        self.root.withdraw()  # Скрытие основного окна до завершения выбора файлов/папок
        self._padding = (5, 5, 5, 5)

        self._username = os.getlogin()
        self.setup_logging()

        self._log_path = 'logs'
        self._config_ext = 'ini'
        self._section_settings = 'Settings'
        self._section_window = 'Window'
        self._path_exe = 'executable_path'
        self._path_dir = 'folder_path'
        self._config_file = self.get_executable_base_name()
        self.config = self.check_or_create_settings()
        self.executable_path = self._get_path(self._section_settings, self._path_exe)
        self.folder_path = self._get_path(self._section_settings, self._path_dir, False)
        self.dby_files = []


    def setup_logging(self):
        if not os.path.exists(self._log_path):
            os.mkdir(self._log_path)
        log_filename = datetime.now().strftime(f'{self._log_path}/%Y.%m.%d_{self._username}.log')
        logging.basicConfig(filename=log_filename, level=logging.INFO,
                            format='%(asctime)s:\t%(levelname)s:\t%(message)s')

    def get_executable_base_name(self):
        return f'{os.path.splitext(os.path.basename(sys.argv[0]))[0]}.{self._config_ext}'

    def check_or_create_settings(self):
        config = ConfigParser()
        if not os.path.exists(self._config_file):
            config[self._section_settings] = {self._path_dir: '', self._path_exe: ''}
            with open(self._config_file, 'w') as file:
                config.write(file)
        else:
            config.read(self._config_file)
        return config

    def _get_path(self, section, path, get_exe = True):
        if self.config.has_option(section, path):
            return self.config.get(section, path)
        else:
            return self.select_executable() if get_exe else self.select_folder()

    def _update_config(self, section, key, value):
        self.config.set(section, key, value)
        with open(self._config_file, 'w') as file:
            self.config.write(file)

    def select_executable(self):
        exe_selected = filedialog.askopenfilename(
            title='Выберите исполняемый файл',
            filetypes=(('Executable files', '*.exe'), ('All files', '*.*'))
        )
        if exe_selected:
            self._update_config(self._section_settings, self._path_exe, exe_selected)
        return exe_selected

    def select_folder(self):
        folder_selected = filedialog.askdirectory(title='Выберите папку')
        if folder_selected:
            self._update_config(self._section_settings, self._path_dir, folder_selected)
        return folder_selected

    def find_dby_files(self):
        logging.info('Обновление списка DBY файлов')
        dby_files = []
        for root, _, files in os.walk(self.folder_path):
            for file in files:
                if file.lower().endswith('.dby'):
                    dby_files.append((os.path.splitext(file)[0], os.path.join(root, file)))
        self.dby_files = dby_files
        logging.info(f'Найдено {len(dby_files)} DBY файлов')

    def open_program(self, file_path):
        try:
            logging.info(f'Открытие файла: {file_path}')
            subprocess.run([self.executable_path, file_path], check=True)
        except Exception as e:
            logging.error(f'Ошибка при открытии файла {file_path}: {str(e)}')
            messagebox.showerror('Ошибка', f'Не удалось открыть файл: {str(e)}')

    def on_select(self, event, listbox):
        selected_index = listbox.curselection()
        if selected_index:
            _, file_path = self.dby_files[selected_index[0]]
            with ThreadPoolExecutor() as executor:
                executor.submit(self.open_program, file_path)

    def save_window_size(self, root, section):
        width = root.winfo_width()
        height = root.winfo_height()
        self._update_config(section, 'width', str(width))
        self._update_config(section, 'height', str(height))

    def refresh_list(self, listbox):
        self.find_dby_files()
        listbox.delete(0, tk.END)
        for name, _ in self.dby_files:
            listbox.insert(tk.END, name)

    def run(self):
        if not self.executable_path:
            self.executable_path = self.select_executable()

        if not self.folder_path:
            self.folder_path = self.select_folder()

        if self.folder_path and self.executable_path:
            self.find_dby_files()

            root = tk.Tk()
            root.title("DBY File Viewer")

            frame = ttk.Frame(root, padding=self._padding)
            frame.pack(expand=True, fill=tk.BOTH)

            listbox = tk.Listbox(frame, width=50, height=20)
            listbox.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            listbox.config(yscrollcommand=scrollbar.set)

            for name, _ in self.dby_files:
                listbox.insert(tk.END, name)

            listbox.bind('<<ListboxSelect>>', lambda event: self.on_select(event, listbox))

            refresh_button = ttk.Button(root, text="Обновить", command=lambda: self.refresh_list(listbox))
            refresh_button.pack(pady=(0, 5))

            open_button = tk.Button(root, text="Открыть", command=lambda: self.on_select(None, listbox))
            open_button.pack()

            # close_button = tk.Button(root, text="Закрыть", command=root.quit)
            # close_button.pack()

            # Сохраняем размер при закрытии окна
            root.protocol(
                "WM_DELETE_WINDOW", lambda: (self.save_window_size(root, self._section_window), root.quit()))

            root.mainloop()

if __name__ == '__main__':
    viewer = DBYFileViewer()
    viewer.run()
