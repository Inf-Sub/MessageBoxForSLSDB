import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from configparser import ConfigParser
import sys
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor


VERSION = '0.5.25'  # Версия приложения


class DBYFileViewer:
    def __init__(self):
        self._username = os.getlogin()
        self._logging_path = 'logs'
        self.setup_logging(self._logging_path)

        logging.info(f'Application initialization, version: {VERSION}')

        self._config_ext = 'ini'
        self._section_settings = 'Settings'
        self._section_window = 'WindowSize'
        self._path_exe = 'executable_path'
        self._path_dir = 'folder_path'
        self._width = 80
        self._height = 100
        self._config_file = self.get_executable_base_name()
        logging.info(f'Getting the INI file name: {self._config_file}')

        self.config = self.check_or_create_settings()

        self.root = tk.Tk()  # Создание основного окна
        self.root.title(f'DBY File Viewer v{VERSION}')
        # self.root.withdraw# ()  # Скрытие основного окна до завершения выбора файлов/папок

        self.get_window_size()  # Чтение размеров из конфига
        self.root.geometry(f'{self._width}x{self._height}')
        self._padding = (5, 5, 5, 5)

        self.executable_path = self._get_path(self._section_settings, self._path_exe)
        logging.info(f'Getting the path to the application executable file: {self.executable_path}')

        self.folder_path = self._get_path(self._section_settings, self._path_dir, False)
        logging.info(f'Getting the path to the directory with .DBY files: {self.folder_path}')

        self.dby_files = []



    def setup_logging(self, path):
        if not os.path.exists(path):
            os.mkdir(path)
        log_filename = datetime.now().strftime(f'{path}/%Y.%m.%d_{VERSION}_{self._username}.log')
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
            logging.info(f'INI file created: {self._config_file}')
        else:
            config.read(self._config_file)
        return config

    def get_window_size(self):
        config = self.config
        if config.has_section(self._section_window):
            self._width = config.getint(self._section_window, 'width', fallback=self._width)
            self._width = config.getint(self._section_window, 'height', fallback=self._height)

    def _get_path(self, section, key, get_exe = True):
        if self.config.has_option(section, key):
            value = self.config.get(section, key)
            logging.info(f'Getting data from ini file: SECTION: "{value}", PARAMETER: "{key}", VALUE: "{value}".')
            return value
        else:
            return self.select_executable() if get_exe else self.select_folder()

    def _update_config(self, section, key, value):
        self.config.set(section, key, value)
        logging.info(f'Updating data in the ini file: "{value}", PARAMETER: "{key}", VALUE: "{value}".')
        with open(self._config_file, 'w') as file:
            self.config.write(file)

    def select_executable(self):
        exe_selected = filedialog.askopenfilename(
            title='Выберите исполняемый файл',
            filetypes=(('Executable files', '*.exe'), ('All files', '*.*'))
        )
        if exe_selected:
            logging.info(f'Manual selection of the path to the application executable file: "{exe_selected}".')
            self._update_config(self._section_settings, self._path_exe, exe_selected)
        return exe_selected

    def select_folder(self):
        folder_selected = filedialog.askdirectory(title='Выберите папку')
        if folder_selected:
            logging.info(f'Manually selecting the path to the folder with .DBY files: "{folder_selected}".')
            self._update_config(self._section_settings, self._path_dir, folder_selected)
        return folder_selected

    def find_dby_files(self):
        logging.info('Updating the list of DBY files')
        dby_files = []
        for root, _, files in os.walk(self.folder_path):
            for file in files:
                if file.lower().endswith('.dby'):
                    dby_files.append((os.path.splitext(file)[0], os.path.join(root, file)))
        self.dby_files = dby_files
        logging.info(f'Found {len(dby_files)} DBY files')

    def open_program(self, file_path):
        try:
            logging.info(f'Opening file: {file_path}')
            subprocess.run([self.executable_path, file_path], check=True)
        except Exception as e:
            logging.error(f'Error opening file {file_path}: {str(e)}')
            messagebox.showerror('Error', f'Failed to open file: {str(e)}')

    def on_select(self, event, listbox):
        selected_index = listbox.curselection()
        if selected_index:
            _, file_path = self.dby_files[selected_index[0]]
            with ThreadPoolExecutor() as executor:
                executor.submit(self.open_program, file_path)

    def save_window_size(self):
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        logging.info(f'Saving window size: "{width}x{height}"')
        self._update_config(self._section_window, 'width', str(width))
        self._update_config(self._section_window, 'height', str(height))

    def refresh_list(self, listbox):
        logging.info(f'Pressing the "REFRESH" button.')
        self.find_dby_files()
        listbox.delete(0, tk.END)
        for name, _ in self.dby_files:
            listbox.insert(tk.END, name)

    def create_ui(self):
        def on_double_click(event):
            logging.info(f'Double click on the selected element. Event: "{event}". Listbox: "{listbox}"')
            self.on_select(event, listbox)

        frame = ttk.Frame(self.root, padding=self._padding)
        frame.pack(expand=True, fill=tk.BOTH)

        listbox = tk.Listbox(frame, width=100, height=100, selectmode=tk.SINGLE)
        listbox.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox.config(yscrollcommand=scrollbar.set)

        for name, _ in self.dby_files:
            listbox.insert(tk.END, name)

        listbox.bind('<Double-1>', on_double_click)
        listbox.bind('<Return>', lambda event: self.on_select(event, listbox))

        button_frame = ttk.Frame(self.root)
        button_frame.pack(side=tk.BOTTOM, pady=5)

        refresh_button = ttk.Button(button_frame, text='Обновить', command=lambda: self.refresh_list(listbox))
        refresh_button.pack(side=tk.LEFT, padx=5)

        open_button = ttk.Button(button_frame, text='Открыть', command=lambda: self.on_select(None, listbox))
        open_button.pack(side=tk.LEFT, padx=5)

        close_button = ttk.Button(button_frame, text='Закрыть', command=self.root.quit)
        close_button.pack(side=tk.LEFT, padx=5)

        self.root.protocol('WM_DELETE_WINDOW', lambda: (self.save_window_size(), self.root.quit()))

    def run(self):
        self.create_ui()
        self.root.mainloop()

    # def run(self):
    #     if not self.executable_path:
    #         logging.info(f'The value of the variable "executable_path" is empty, asking the user for manual selection.')
    #         self.executable_path = self.select_executable()
    #
    #     if not self.folder_path:
    #         logging.info(f'The value of the variable "folder_path" is empty, asking the user for manual selection.')
    #         self.folder_path = self.select_folder()
    #
    #     if self.folder_path and self.executable_path:
    #         logging.info(
    #             'The parameters "executable_path" and "folder_path" are filled in, we update the list of DBY files.')
    #         self.find_dby_files()
    #
    #         # root = tk.Tk()
    #         # self.root.title('DBY File Viewer')
    #
    #         frame = ttk.Frame(self.root, padding=self._padding)
    #         frame.pack(expand=True, fill=tk.BOTH)
    #
    #         listbox = tk.Listbox(frame, width=100, height=100)
    #         listbox.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5, pady=5)
    #
    #         scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
    #         scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    #
    #         listbox.config(yscrollcommand=scrollbar.set)
    #
    #         for name, _ in self.dby_files:
    #             listbox.insert(tk.END, name)
    #
    #         listbox.bind('<<ListboxSelect>>', lambda event: self.on_select(event, listbox))
    #
    #         refresh_button = ttk.Button(self.root, text='Обновить', command=lambda: self.refresh_list(listbox))
    #         refresh_button.pack(pady=(0, 5))
    #
    #         open_button = tk.Button(self.root, text='Открыть', command=lambda: self.on_select(None, listbox))
    #         open_button.pack()
    #
    #         close_button = tk.Button(self.root, text='Закрыть', command=self.root.quit)
    #         close_button.pack()
    #
    #         # Сохраняем размер при закрытии окна
    #         # self.root.protocol(
    #         #     'WM_DELETE_WINDOW', lambda: (self.save_window_size(), self.root.quit()))
    #
    #         self.root.mainloop()

if __name__ == '__main__':
    viewer = DBYFileViewer()
    viewer.run()

